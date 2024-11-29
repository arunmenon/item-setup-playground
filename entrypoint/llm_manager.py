# llm_manager.py

import asyncio
import logging
from typing import Dict, List, Any
from models.llm_request_models import BaseLLMRequest
from handlers.llm_handler import BaseModelHandler
from models.models import ProviderConfig, GenerationTask, EvaluationTask
from sqlalchemy.orm import Session

class LLMManager:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.handlers = {}
        self.family_names = {}
        self.tasks = {}
        self.load_providers()
        self.load_tasks()
        logging.debug(f"Initialized handlers: {list(self.handlers.keys())}")
        logging.debug(f"Initialized tasks: {list(self.tasks.keys())}")

    def load_providers(self):
        providers = self.db_session.query(ProviderConfig).filter_by(is_active=True).all()
        for provider in providers:
            name = provider.name
            family_name = provider.family
            provider_kwargs = {
                'provider': provider.provider_name,
                'model': provider.model,
                'max_tokens': provider.max_tokens,
                'temperature': provider.temperature,
                # Add other provider-specific parameters if needed
            }
            self.handlers[name] = BaseModelHandler(**provider_kwargs)
            self.family_names[name] = family_name
            logging.debug(f"Initialized handler '{name}' for family '{family_name}'.")

    def load_tasks(self):
        # Load GenerationTasks
        generation_tasks = self.db_session.query(GenerationTask).all()
        for task in generation_tasks:
            self.tasks[(task.task_name, 'generation')] = {
                'task_type': 'generation',
                'max_tokens': task.max_tokens,
                'output_format': task.output_format
            }
        # Load EvaluationTasks
        evaluation_tasks = self.db_session.query(EvaluationTask).all()
        for task in evaluation_tasks:
            self.tasks[(task.task_name, 'evaluation')] = {
                'task_type': 'evaluation',
                'max_tokens': task.max_tokens,
                'output_format': task.output_format
            }
            
    def get_task_config(self, task_name: str, task_type: str) -> Dict[str, Any]:
        return self.tasks.get((task_name, task_type), {})
    
    def get_family_name(self, handler_name):
        return self.family_names.get(handler_name, 'default')

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
            # Get max_tokens from task config
            task_config = self.tasks.get(task, {})
            max_tokens = task_config.get('max_tokens', handler.max_tokens)

            response = await handler.invoke(request=BaseLLMRequest(prompt=prompt, max_tokens=max_tokens), task=task)
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
