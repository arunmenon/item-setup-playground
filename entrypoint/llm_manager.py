# llm_manager.py

import asyncio
import logging
from typing import Dict, List, Any
from models.llm_request_models import BaseLLMRequest
from handlers.llm_handler import BaseModelHandler
from providers.provider_factory import ProviderFactory

class LLMManager:
    def __init__(self, config):
        self.handlers = {}
        self.family_names = {}
        for provider_config in config['providers']:
            provider_config_copy = provider_config.copy()
            name = provider_config_copy["name"]
            print(f"name from provider {name}")
            #provider_name = provider_config_copy.pop('provider')
            family_name = provider_config_copy['family']
            family_name = provider_config_copy['family']
            self.handlers[name] = BaseModelHandler(**provider_config_copy)
            self.family_names[name]=family_name
        self.tasks = config.get('tasks', {})    
        logging.debug(f"Initialized handlers: {list(self.handlers.keys())}")
        logging.debug(f"Initialized tasks: {list(self.tasks.keys())}")

    def get_family_name(self, handler_name):
        return self.family_names.get(handler_name, 'default')
    
    async def invoke_handler(self, handler_name: str, handler: BaseModelHandler, prompt: str, task: str,max_tokens: int) -> Dict[str, Any]:
        """
        Invokes a handler with the given prompt and task.

        Args:
            handler_name (str): The name of the handler.
            handler (BaseModelHandler): The handler instance.
            prompt (str): The prompt to send.
            task (str): The task name.
            max_tokens (int): The maximum number of tokens for the response.

        Returns:
            Dict[str, Any]: The result of the handler invocation.
        """
        try:
            response = await handler.invoke(request=BaseLLMRequest(prompt=prompt,max_tokens=max_tokens), task=task)
            logging.debug(f"Received response for task '{task}' from handler '{handler_name}': {response}")

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
