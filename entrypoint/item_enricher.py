# item_enricher.py

import asyncio
import logging
from models.llm_request_models import LLMRequest
from exceptions.custom_exceptions import StylingGuideNotFoundException

class ItemEnricher:
    def __init__(self, llm_manager, prompt_manager):
        self.llm_manager = llm_manager
        self.prompt_manager = prompt_manager

    async def enrich_item(self, request: LLMRequest):
        # Extract request data
        item_title = request.item_title
        short_description = request.short_description
        long_description = request.long_description
        item_product_type = request.item_product_type
        image_url = request.image_url
        attributes_list = request.attributes_list
        # You can extract more fields as needed

        logging.debug(f"Received request for product type: {repr(item_product_type)}")

        # Define tasks based on available data
        tasks = ["title_enhancement", "short_description_enhancement", "long_description_enhancement"]

        # Add 'attribute_extraction' task if attributes_list is provided
        if attributes_list:
            tasks.append("attribute_extraction")

        # Add 'vision_attribute_extraction' task if image_url is provided
        if image_url:
            tasks.append("vision_attribute_extraction")

        logging.debug(f"Tasks to perform: {tasks}")

        # Generate prompts using the updated PromptManager
        try:
            prompts_tasks = self.generate_prompts(
                item_title, short_description, long_description, item_product_type, tasks, image_url, attributes_list
            )
        except StylingGuideNotFoundException as e:
            logging.error(f"Styling guide not found: {str(e)}")
            raise

        # Invoke LLMManager to get responses
        results = await self.invoke_llms(prompts_tasks)

        # Process results (e.g., parse JSON responses)
        processed_results = self.process_results(results)

        return processed_results

    def generate_prompts(self, item_title, short_description, long_description,
                         item_product_type, tasks, image_url=None, attributes_list=None):
        logging.debug("Generating prompts for the tasks")
        prompts_tasks = self.prompt_manager.generate_prompts(
            item_title=item_title,
            short_description=short_description,
            long_description=long_description,
            product_type=item_product_type,
            tasks=tasks,
            image_url=image_url,
            attributes_list=attributes_list
        )
        logging.debug(f"Generated prompts and tasks: {prompts_tasks}")
        return prompts_tasks

    async def invoke_llms(self, prompts_tasks):
        logging.debug("Invoking LLMManager with generated prompts and tasks")
        tasks_list = []
        for prompt_task in prompts_tasks:
            task_name = prompt_task['task']
            prompt = prompt_task['prompt']
            tasks_list.append(self.invoke_single_llm(task_name, prompt))

        # Run all tasks concurrently
        task_results = await asyncio.gather(*tasks_list, return_exceptions=True)


        results = {}
        for task_name, response in task_results:
            results[task_name] = response

        logging.info(f"LLMManager invocation successful. Results: {results}")
        return results

    async def invoke_single_llm(self, task_name, prompt):
        try:
            response = await self.llm_manager.get_response(prompt)
            logging.debug(f"Received response for task '{task_name}': {response}")
            return task_name, response
        except Exception as e:
            logging.error(f"Error invoking LLMManager for task '{task_name}': {str(e)}")
            return task_name, {'error': str(e)}
        
    def process_results(self, results):
        # Process the results, e.g., parse JSON responses
        processed_results = {}
        for task, response in results.items():
            if 'error' in response:
                processed_results[task] = response
            else:
                try:
                    # Parse the JSON response
                    import json
                    processed_response = json.loads(response)
                    processed_results[task] = processed_response
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON response for task '{task}': {str(e)}")
                    processed_results[task] = {'error': 'Invalid JSON response'}
        return processed_results
