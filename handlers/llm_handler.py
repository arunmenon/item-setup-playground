# llm_handler.py
from typing import Dict, List, Any
import asyncio
from asyncio import Semaphore
import logging
from handlers.openai_handler import OpenAIHandler
from handlers.ow_model_handler import OpenWeightsModelHandler

logging.basicConfig(level=logging.DEBUG)

class LLMHandler:
    def __init__(self, config: Dict[str, Any], api_key: str, max_concurrent_tasks: int = 5, batch_size: int = 10):
        logging.debug("Initializing LLMHandler with config: %s, max_concurrent_tasks: %d, batch_size: %d", config, max_concurrent_tasks, batch_size)
        self.llms = config.get("llms", {})
        if not self.llms:
            logging.error("No LLMs configured. Please provide at least one LLM in the configuration.")
            raise ValueError("No LLMs configured. Please provide at least one LLM in the configuration.")
        self.semaphore = Semaphore(max_concurrent_tasks)  # Limit the number of concurrent tasks to avoid overwhelming the system
        self.batch_size = batch_size  # Limit the number of tasks processed concurrently in each batch
        self.openai_handler = OpenAIHandler(api_key)
        self.open_weights_handlers = {
            llm_name: OpenWeightsModelHandler(llm_config.get("endpoint"))
            for llm_name, llm_config in self.llms.items() if llm_config.get("type") == "open_weights"
        }
        logging.info("LLMHandler initialized with configuration: %s", self.llms)

    async def fan_out_calls(self, metadata: Dict[str, Any], tasks: List[str]) -> Dict[str, Dict[str, Any]]:
        logging.debug("Starting fan_out_calls with metadata: %s and tasks: %s", metadata, tasks)
        responses = {}
        tasks_list = [self.invoke_llm(metadata, task, llm_name) for llm_name in self.llms.keys() for task in tasks]
        
        # Process tasks in batches to avoid overwhelming system resources
        for i in range(0, len(tasks_list), self.batch_size):
            logging.debug("Processing batch %d to %d", i, i + self.batch_size)
            batch = tasks_list[i:i + self.batch_size]
            done, pending = await asyncio.wait(batch, return_when=asyncio.FIRST_EXCEPTION)
            for future in done:
                try:
                    result = await future
                    llm_name = result["llm_name"]
                    task = result["task"]
                    response = result["response"]

                    logging.debug("Received response for LLM: %s, Task: %s, Response: %s", llm_name, task, response)

                    if llm_name not in responses:
                        responses[llm_name] = {}
                    responses[llm_name][task] = response
                except Exception as e:
                    logging.error("Error occurred while processing a task: %s. Metadata: %s, Task: %s", e, metadata, task)

            # Cancel any pending tasks if an exception was raised
            for future in pending:
                future.cancel()

        logging.info("Completed fan_out_calls with responses: %s", responses)
        return responses

    async def invoke_llm(self, metadata: Dict[str, Any], task: str, llm_name: str) -> Dict[str, Any]:
        logging.debug("Invoking LLM: %s for task: %s with metadata: %s", llm_name, task, metadata)
        async with self.semaphore:
            logging.debug("Acquired semaphore for LLM: %s, Task: %s", llm_name, task)
            prompt = metadata.get("product_title", "")
            logging.debug("Using prompt: %s", prompt)
            llm_config = self.llms.get(llm_name, {})
            llm_type = llm_config.get("type")

            if llm_type == "openai":
                logging.debug("Invoking OpenAI handler for LLM: %s, Task: %s", llm_name, task)
                return await self.openai_handler.invoke(prompt, llm_name, task, model=llm_config.get("model", "gpt-4"))
            elif llm_type == "open_weights":
                logging.debug("Invoking OpenWeightsModelHandler for LLM: %s, Task: %s", llm_name, task)
                open_weights_handler = self.open_weights_handlers.get(llm_name)
                return await open_weights_handler.invoke(prompt, llm_name, task)
            else:
                logging.error("LLM %s not supported", llm_name)
                raise ValueError(f"LLM {llm_name} not supported")
