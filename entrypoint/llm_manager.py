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

    async def fan_out_calls(self, prompts_tasks: List[Dict[str, Any]]):
        # For each task, fan out to all handlers
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
                'model': result['model'],
                'response': result['response'],
                'success': result['success']
            })
        return results

    async def invoke_handler(self, handler_name, handler, prompt, task):
        try:
            response = await handler.invoke(request=BaseLLMRequest(prompt=prompt), task=task)
            return {
                'handler_name': handler_name,
                'model': handler.model,
                'task': task,
                'response': response['response'],
                'success': True
            }
        except Exception as e:
            logging.error(f"Error invoking handler {handler_name} for task {task}: {str(e)}")
            return {
                'handler_name': handler_name,
                'model': handler.model,
                'task': task,
                'error': str(e),
                'response': None,
                'success': False
            }
