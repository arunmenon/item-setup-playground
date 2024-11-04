# item_enricher.py

import asyncio
import logging
from typing import Dict, Any, List
from models.llm_request_models import LLMRequest
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

    async def enrich_item(self, request: LLMRequest, model: str):
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

        
        # Generate prompts for each task using PromptManager
        try:
            prompts_tasks = self.prompt_manager.generate_prompts(item, model=model)
        except StylingGuideNotFoundException as e:
            logging.error(f"Styling guide not found: {str(e)}")
            raise

        logging.info(f"prompt_tasks {prompts_tasks}")    
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
            'image_url': request.image_url,
            'attributes_list': request.attributes_list,
            # Add more fields as needed
        }
        
        return item

    async def invoke_llms(self, prompts_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Invokes the LLMManager to get responses for each prompt.

        Args:
            prompts_tasks (List[Dict[str, Any]]): A list of dictionaries containing 'task', 'prompt', and 'output_format'.

        Returns:
            Dict[str, Any]: A dictionary with tasks as keys and handler responses as values.
        """
        logging.debug("Invoking LLMManager with generated prompts and tasks")
        tasks_list = []

        for prompt_task in prompts_tasks:
            task_name = prompt_task['task']
            prompt = prompt_task['prompt']
            tasks_list.append(self.invoke_single_llm(task_name, prompt))

        # Run all LLM invocations concurrently
        task_results = await asyncio.gather(*tasks_list)

        results = {}
        for task_name, handler_responses in task_results:
            results[task_name] = handler_responses

        logging.info(f"LLMManager invocation successful. Results: {results}")
        return results

    async def invoke_single_llm(self, task_name: str, prompt: str) -> (str, Dict[str, Any]):
        """
        Invokes the LLMManager for a single task and prompt.

        Args:
            task_name (str): The name of the task.
            prompt (str): The prompt to send to the LLM.

        Returns:
            Tuple[str, Dict[str, Any]]: The task name and its corresponding handler responses.
        """
        try:
            handler_responses = await self.llm_manager.get_response(prompt, task_name)
            logging.debug(f"Received responses for task '{task_name}': {handler_responses}")
            return task_name, handler_responses
        except Exception as e:
            logging.error(f"Error invoking LLMManager for task '{task_name}': {str(e)}")
            return task_name, {'error': str(e)}

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
        try:
            if isinstance(response, dict) and 'error' in response:
                # If the handler returned an error, propagate it
                return {
                    'handler_name': handler_name,
                    'error': response['error']
                }

            # Use ParserFactory to get the appropriate parser based on output_format
            parser = ParserFactory.get_parser(output_format)
            parsed_response = parser.parse(response)

            return {
                'handler_name': handler_name,
                'response': parsed_response
            }

        except Exception as e:
            logging.error(
                f"Error processing response from handler '{handler_name}' for task '{task}': {str(e)}\nResponse Text: {response}"
            )
            return {
                'handler_name': handler_name,
                'error': 'Parsing failed'
            }
