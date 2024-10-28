# item_enricher.py
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

        logging.debug(f"Received request for product type: {repr(item_product_type)}")
        # Normalize product type to ensure consistency


        
        # Generate prompts
        tasks = ["title_enhancement", "short_description_enhancement", "long_description_enhancement"]
        prompts_tasks = self.generate_prompts(
            item_title, short_description, long_description,item_product_type, tasks
        )

        # Invoke LLMManager
        results = await self.invoke_llms(prompts_tasks)

        return results

    
    def generate_prompts(self, item_title, short_description, long_description, item_product_type, tasks):
        logging.debug("Generating prompts for the tasks")
        prompts_tasks = self.prompt_manager.generate_prompts(
            item_title, short_description, long_description, item_product_type, tasks
        )
        logging.debug(f"Generated prompts and tasks: {prompts_tasks}")
        return prompts_tasks

    async def invoke_llms(self, prompts_tasks):
        logging.debug(f"Invoking LLMManager with generated prompts and tasks")
        results = await self.llm_manager.fan_out_calls(prompts_tasks)
        logging.info(f"LLMManager invocation successful. Results: {results}")
        return results
