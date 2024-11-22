# item_enricher.py

import asyncio
import json
import logging
from typing import Dict, Any, List
from handlers.llm_handler import BaseModelHandler
from models.llm_request_models import BaseLLMRequest, LLMRequest
from exceptions.custom_exceptions import StylingGuideNotFoundException
from parsers.parser_factory import ParserFactory


class ItemEnricher:
    def __init__(self, llm_manager, prompt_manager):
        """
        Initializes the ItemEnricher with LLMManager and PromptManager instances.

        Args:
            llm_manager: An instance of LLMManager to handle LLM interactions.
            prompt_manager: An instance of PromptManager to handle prompt generation.
        """
        self.llm_manager = llm_manager
        self.prompt_manager = prompt_manager

    async def enrich_item(self, request: LLMRequest):
        """
        Enriches an item based on the provided request and model.

        Args:
            request (LLMRequest): The incoming request containing item details.
            model (str): The model to use for enrichment.

        Returns:
            Dict[str, Any]: A dictionary containing enriched data for each task.
        """
        # Extract request data into a dictionary
        item = self.prepare_item(request)
        logging.info(f"Received request for product type: '{item['product_type']}'")
        # Collect unique family names
        family_names = set(self.llm_manager.family_names.values())
        logging.info(f"family names '{family_names}'")

        # Generate prompts per family
        prompts_per_family = {}
        for family_name in family_names:
            prompts = self.prompt_manager.generate_prompts(item, family_name=family_name)
            prompts_per_family[family_name] = prompts
            logging.debug(f"Generated prompts for family '{family_name}': {prompts}")

        # Associate prompts with handlers
        prompts_tasks = []
        for handler_name, handler in self.llm_manager.handlers.items():
            # Get the family_name associated with the handler
            family_name = self.llm_manager.get_family_name(handler_name)
            prompts = prompts_per_family[family_name]
            for prompt_task in prompts:
                prompt_task_copy = prompt_task.copy()
                prompt_task_copy['provider_name'] = handler_name
                prompts_tasks.append(prompt_task_copy)
        
        
        logging.debug(f"prompt_tasks {prompts_tasks}")    
        # Create a mapping from task_name to output_format for parser selection
        task_to_format = {pt['task']: pt['output_format'] for pt in prompts_tasks}

        # Invoke LLMManager to get responses for all prompts
        results = await self.invoke_llms(prompts_tasks)

        # Process and parse the results based on output_format
        processed_results = self.process_results(results, task_to_format)

        return processed_results

    def prepare_item(self, request):
        item = {
            'item_title': request.item_title,
            'short_description': request.short_description,
            'long_description': request.long_description,
            'product_type': request.item_product_type,
            #'image_url': request.image_url,
            #'attributes_list': request.attributes_list,
            # Add more fields as needed
        }
        
        return item

    async def invoke_llms(self, prompts_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Invokes each handler with its associated prompts.

        Args:
            prompts_tasks (List[Dict[str, Any]]): A list of dictionaries containing 'task', 'prompt', and 'provider_name'.

        Returns:
            Dict[str, Any]: A dictionary with tasks as keys and handler responses as values.
        """
        logging.debug("Invoking LLMManager with generated prompts and tasks")
        tasks_list = []

        for prompt_task in prompts_tasks:
            task_name = prompt_task['task']
            prompt = prompt_task['prompt']
            provider_name = prompt_task['provider_name']
            handler = self.llm_manager.handlers.get(provider_name)
            if not handler:
             logging.error(f"Handler '{provider_name}' not found. Skipping prompt for task '{task_name}'.")
             continue
            
            
            tasks_list.append(self.invoke_single_llm(task_name, prompt,provider_name,handler))

        # Run all LLM invocations concurrently
        task_results = await asyncio.gather(*tasks_list)

        results = {}
        for task_name, handler_name, handler_response in task_results:
            if task_name not in results:
                results[task_name] = {}
            results[task_name][handler_name] = handler_response
            logging.debug(f"Stored result for task '{task_name}' from handler '{handler_name}': {handler_response}")


        logging.info(f"LLMManager invocation successful. Results: {results}")
        return results

    # entrypoint/item_enricher.py

    async def invoke_single_llm(self, task_name: str, prompt: str, handler_name: str, handler: BaseModelHandler) -> (str, str, Dict[str, Any]):
        """
        Invokes the LLMManager for a single task and prompt.

        Args:
            task_name (str): The name of the task.
            prompt (str): The prompt to send to the LLM.
            handler_name (str): The name of the handler.
            handler (BaseModelHandler): The handler instance.

        Returns:
            Tuple[str, str, Dict[str, Any]]: The task name, handler name, and its corresponding response.
        """
        try:
            # Get max_tokens from task config
            task_config = self.llm_manager.tasks.get(task_name, {})
            max_tokens = task_config.get('max_tokens', 150)

            # Invoke the handler with the prompt
            # response = await handler.invoke(request=BaseLLMRequest(prompt=prompt, max_tokens=max_tokens), task=task_name)
            response = await handler.invoke(request=BaseLLMRequest(prompt=prompt, parameters={'max_tokens': max_tokens}), task=task_name)
            logging.debug(f"Received response for task '{task_name}' from handler '{handler_name}': {response}")

            return task_name, handler_name, {'response': response['response'], 'error': None}
        except Exception as e:
            logging.error(f"Error invoking handler '{handler_name}' for task '{task_name}': {str(e)}")
            return task_name, handler_name, {'response': None, 'error': str(e)}


    def process_results(self, results: Dict[str, Any], task_to_format: Dict[str, str]) -> Dict[str, Any]:
        """
        Processes and parses the LLM responses based on their output formats.

        Args:
            results (Dict[str, Any]): The raw responses from the LLMManager.
            task_to_format (Dict[str, str]): A mapping from task names to their output formats.

        Returns:
            Dict[str, Any]: The parsed and structured results.
        """
        processed_results = {}
        for task, handler_responses in results.items():
            output_format = task_to_format.get(task, 'json')  # Default to 'json' if not specified
            task_results = {}
            for handler_name, response in handler_responses.items():
                result = self.process_single_response(handler_name, task, response, output_format)
                task_results[handler_name] = result
            processed_results[task] = task_results
        return processed_results

    def process_single_response(self, handler_name: str, task: str, response: Any, output_format: str) -> Dict[str, Any]:
        """
        Parses a single handler's response based on the specified output format.

        Args:
            handler_name (str): The name of the handler.
            task (str): The task name.
            response (Any): The raw response from the handler.
            output_format (str): The desired output format ('json' or 'markdown').

        Returns:
            Dict[str, Any]: The parsed response or an error message.
        """
        logging.debug(f"response to be parsed is {response} ")
        response_content = ''
        fixed_response = ''
        try:
            if isinstance(response, dict) and response.get('error') is not None:
                # If the handler returned an error, propagate it
                return {
                    'handler_name': handler_name,
                    'error': response['error']
                }
            response_content = response.get('response', '')


            # Use ParserFactory to get the appropriate parser based on output_format
            parser = ParserFactory.get_parser(output_format)
            parsed_response = parser.parse(response_content)

            return {
                'handler_name': handler_name,
                'response': parsed_response
            }

        except Exception as e:
            if '{' in response_content:
                json_start = response_content.index('{')
                fixed_response = response_content[json_start:]
            else:
                fixed_res_dict = {task : response_content}
                fixed_response = json.dumps(fixed_res_dict)
            try:
                parser = ParserFactory.get_parser(output_format)
                parsed_response = parser.parse(fixed_response)
                return {
                    'handler_name': handler_name,
                    'response': parsed_response
                }
            except Exception as ex:
                fixed_response = fixed_response.replace("```json", "").replace("```", "").replace("\n","")
                try:
                    parser = ParserFactory.get_parser(output_format)
                    parsed_response = parser.parse(fixed_response)
                    return {
                        'handler_name': handler_name,
                        'response': parsed_response
                    }
                except Exception as ex:
                    logging.error(
                        f"Error processing response from handler '{handler_name}' for task '{task}': {str(e)}\nResponse Text: {response}"
                    )
                    return {
                        'handler_name': handler_name,
                        'error': 'Parsing failed'
                    }