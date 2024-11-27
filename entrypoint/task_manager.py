# entrypoint/task_manager.py

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from models.models import TaskConfig, TaskExecutionConfig
import logging

class TaskManager:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.tasks_config: Dict[str, Dict[str, Any]] = {}
        self.task_execution: Dict[str, Any] = {}
        self.load_tasks()
        self.load_task_execution_config()

    def load_tasks(self):
        tasks = self.db_session.query(TaskConfig).all()
        for task in tasks:
            self.tasks_config[task.task_name] = {
                'max_tokens': task.max_tokens,
                'output_format': task.output_format
            }
        logging.info(f"Loaded tasks: {list(self.tasks_config.keys())}")

    def load_task_execution_config(self):
        config = self.db_session.query(TaskExecutionConfig).order_by(TaskExecutionConfig.config_id.desc()).first()
        if config:
            self.task_execution = {
                'default_tasks': config.default_tasks,
                'conditional_tasks': config.conditional_tasks
            }
            logging.info("Loaded task execution configuration.")
        else:
            logging.error("No task execution configuration found in the database.")
            raise ValueError("No task execution configuration found in the database.")

    def get_default_tasks(self) -> List[str]:
        return self.task_execution.get('default_tasks', [])

    def get_conditional_tasks(self) -> Dict[str, str]:
        return self.task_execution.get('conditional_tasks', {})

    def is_task_defined(self, task_name: str) -> bool:
        return task_name in self.tasks_config

    def get_task_output_format(self, task_name: str) -> str:
        return self.tasks_config.get(task_name, {}).get('output_format', 'json')
