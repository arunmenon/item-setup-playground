# llm_manager.py

import asyncio
import logging
from typing import Dict, List, Any
from models.llm_request_models import BaseLLMRequest
from handlers.llm_handler import BaseModelHandler

class LLMManager:
    def __init__(self, config):
        self.handlers = {}
        for provider_config in config['providers']:
            provider_config_copy = provider_config.copy()
            name = provider_config_copy.pop('name')
            self.handlers[name] = BaseModelHandler(**provider_config_copy)
        logging.debug(f"Initialized handlers: {list(self.handlers.keys())}")

    async def fan_out_calls(self, prompts_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sends each prompt to all handlers and collects the results.

        Args:
            prompts_tasks (List[Dict[str, Any]]): A list of dictionaries containing 'task' and 'prompt'.

        Returns:
            Dict[str, Any]: A dictionary with tasks as keys and lists of handler responses as values.
        """
        logging.debug("Starting fan-out calls to all handlers for each prompt.")

        results = {}
        tasks = []

        for prompt_task in prompts_tasks:
            prompt = prompt_task['prompt']
            task_name = prompt_task['task']
            for handler_name, handler in self.handlers.items():
                tasks.append(self.invoke_handler(handler_name, handler, prompt, task_name))

        handler_results = await asyncio.gather(*tasks)

        # Organize results by task and handler
        for result in handler_results:
            task = result['task']
            handler_name = result['handler_name']
            if task not in results:
                results[task] = []
            results[task].append({
                'handler_name': handler_name,
                'model': result.get('model'),
                'response': result.get('response'),
                'error': result.get('error'),
                'success': result['success']
            })

        return results

    async def get_response(self, prompt: str) -> Dict[str, Any]:
        """
        Sends the prompt to all handlers concurrently and collects responses.

        Args:
            prompt (str): The prompt to send to the LLMs.

        Returns:
            Dict[str, Any]: A dictionary of responses from all handlers.
        """
        tasks = []
        for handler_name, handler in self.handlers.items():
            tasks.append(self.invoke_handler(handler_name, handler, prompt))

        # Run all handler invocations concurrently
        handler_results = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        for result in handler_results:
            handler_name = result['handler_name']
            if result['success']:
                results[handler_name] = result['response']
            else:
                results[handler_name] = {'error': result['error']}

        return results
    
    async def invoke_handler(self, handler_name: str, handler: BaseModelHandler, prompt: str, task: str) -> Dict[str, Any]:
        """
        Invokes a handler with the given prompt and task.

        Args:
            handler_name (str): The name of the handler.
            handler (BaseModelHandler): The handler instance.
            prompt (str): The prompt to send.
            task (str): The task name.

        Returns:
            Dict[str, Any]: The result of the handler invocation.
        """
        try:
            response = await handler.invoke(request=BaseLLMRequest(prompt=prompt), task=task)
            return {
                'handler_name': handler_name,
                'model': handler.model,
                'task': task,
                'response': response['response'],
                'error': None,
                'success': True
            }
        except Exception as e:
            logging.error(f"Error invoking handler '{handler_name}' for task '{task}': {str(e)}")
            return {
                'handler_name': handler_name,
                'model': handler.model,
                'task': task,
                'response': None,
                'error': str(e),
                'success': False
            }
