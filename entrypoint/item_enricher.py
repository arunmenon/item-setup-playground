# item_enricher.py

import asyncio
import logging
from models.llm_request_models import LLMRequest
from exceptions.custom_exceptions import StylingGuideNotFoundException
from parsers.parser_factory import ParserFactory

class ItemEnricher:
    def __init__(self, llm_manager, prompt_manager):
        self.llm_manager = llm_manager
        self.prompt_manager = prompt_manager

    async def enrich_item(self, request: LLMRequest):
        # Extract request data
        item = {
            'item_title': request.item_title,
            'short_description': request.short_description,
            'long_description': request.long_description,
            'product_type': request.item_product_type,
            'image_url': request.image_url,
            'attributes_list': request.attributes_list,
            # Add more fields as needed
        }

        logging.debug(f"Received request for product type: '{item['product_type']}'")

        # Define tasks based on available data
        tasks = ["title_enhancement", "short_description_enhancement", "long_description_enhancement"]

        # Add 'attribute_extraction' task if attributes_list is provided
        if item['attributes_list']:
            tasks.append("attribute_extraction")

        # Add 'vision_attribute_extraction' task if image_url is provided
        if item['image_url']:
            tasks.append("vision_attribute_extraction")

        logging.debug(f"Tasks to perform: {tasks}")

        # Generate prompts using the PromptManager
        try:
            prompts_tasks = self.prompt_manager.generate_prompts(item, tasks)
        except StylingGuideNotFoundException as e:
            logging.error(f"Styling guide not found: {str(e)}")
            raise

        # Invoke LLMManager to get responses
        results = await self.invoke_llms(prompts_tasks)

        # Process results (e.g., parse Markdown responses)
        processed_results = self.process_results(results)

        return processed_results

    async def invoke_llms(self, prompts_tasks):
        logging.debug("Invoking LLMManager with generated prompts and tasks")
        tasks_list = []
        for prompt_task in prompts_tasks:
            task_name = prompt_task['task']
            prompt = prompt_task['prompt']
            tasks_list.append(self.invoke_single_llm(task_name, prompt))

        # Run all tasks concurrently
        task_results = await asyncio.gather(*tasks_list)

        results = {}
        for task_name, handler_responses in task_results:
            results[task_name] = handler_responses

        logging.info(f"LLMManager invocation successful. Results: {results}")
        return results

    async def invoke_single_llm(self, task_name, prompt):
        try:
            handler_responses = await self.llm_manager.get_response(prompt, task_name)
            logging.debug(f"Received responses for task '{task_name}': {handler_responses}")
            return task_name, handler_responses
        except Exception as e:
            logging.error(f"Error invoking LLMManager for task '{task_name}': {str(e)}")
            return task_name, {'error': str(e)}

    def process_results(self, results):
        processed_results = {}
        for task, handler_responses in results.items():
            task_results = {}
            for handler_name, response in handler_responses.items():
                result = self.process_single_response(handler_name, task, response)
                task_results[handler_name] = result
            processed_results[task] = task_results
        return processed_results

    def process_single_response(self, handler_name, task, response):
        try:
            if isinstance(response, dict) and 'error' in response:
                return {
                    'handler_name': handler_name,
                    'error': response['error']
                }

            # Use ParserFactory to get the appropriate parser
            parser = ParserFactory.get_parser(handler_name)
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
