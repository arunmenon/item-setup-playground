# entrypoint/task_manager.py

from typing import Dict, Any, List

class TaskManager:
    def __init__(self, tasks_config: Dict[str, Dict[str, Any]], task_execution: Dict[str, Any]):
        self.tasks_config = tasks_config
        self.task_execution = task_execution

    def get_default_tasks(self) -> List[str]:
        return self.task_execution.get('default_tasks', [])

    def get_conditional_tasks(self) -> Dict[str, str]:
        return self.task_execution.get('conditional_tasks', {})

    def is_task_defined(self, task_name: str) -> bool:
        return task_name in self.tasks_config

    def get_task_output_format(self, task_name: str) -> str:
        return self.tasks_config.get(task_name, {}).get('output_format', 'json')
