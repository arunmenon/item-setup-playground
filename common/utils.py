# utils.py
import os
import logging
import json
import yaml

def setup_logging(level=logging.DEBUG):
    logging.basicConfig(level=level)
    logging.info("Logging is configured.")

def load_config(config_path: str) -> dict:
    """
    Loads the configuration from a JSON or YAML file.
    """
    try:
        with open(config_path, 'r') as file:
            if config_path.endswith(('.yaml', '.yml')):
                config = yaml.safe_load(file)
            elif config_path.endswith('.json'):
                config = json.load(file)
            else:
                raise ValueError("Unsupported configuration file format.")
        logging.info(f"Configuration loaded from {config_path}")
        return config
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        raise

def validate_config(config: dict):
    """
    Validates the configuration to ensure all required fields are present.
    Dynamically validates tasks without hardcoding task names.
    """
    # Validate providers
    for provider in config.get('providers', []):
        required_provider_fields = ['name', 'provider', 'model', 'temperature', 'endpoint_id']
        missing_fields = [field for field in required_provider_fields if field not in provider]
        if missing_fields:
            logging.error(f"Provider configuration incomplete: {provider}. Missing fields: {missing_fields}")
            raise ValueError(f"Provider configuration incomplete: {provider}. Missing fields: {missing_fields}")
    
    # Ensure 'tasks' section exists
    tasks = config.get('tasks')
    if not tasks or not isinstance(tasks, dict):
        logging.error("Missing or invalid 'tasks' section in configuration.")
        raise ValueError("Missing or invalid 'tasks' section in configuration.")
    
    # Validate each task
    for task_name, task_details in tasks.items():
        if not isinstance(task_details, dict):
            logging.error(f"Task '{task_name}' should be a dictionary of its configurations.")
            raise ValueError(f"Task '{task_name}' should be a dictionary of its configurations.")
        
        # Define required fields for each task
        required_task_fields = ['max_tokens', 'output_format']
        missing_task_fields = [field for field in required_task_fields if field not in task_details]
        if missing_task_fields:
            logging.error(f"Task '{task_name}' is missing fields: {missing_task_fields}")
            raise ValueError(f"Task '{task_name}' is missing fields: {missing_task_fields}")
    
    # Validate task_execution block
    task_execution = config.get('task_execution')
    if not task_execution or not isinstance(task_execution, dict):
        logging.error("Missing or invalid 'task_execution' section in configuration.")
        raise ValueError("Missing or invalid 'task_execution' section in configuration.")
    
    # Validate 'default_tasks'
    default_tasks = task_execution.get('default_tasks')
    if default_tasks is None or not isinstance(default_tasks, list):
        logging.error("Missing or invalid 'default_tasks' in 'task_execution' section.")
        raise ValueError("Missing or invalid 'default_tasks' in 'task_execution' section.")
    
    # Ensure all default tasks are defined in 'tasks'
    undefined_default_tasks = [task for task in default_tasks if task not in tasks]
    if undefined_default_tasks:
        logging.error(f"Default tasks {undefined_default_tasks} are not defined in 'tasks' section.")
        raise ValueError(f"Default tasks {undefined_default_tasks} are not defined in 'tasks' section.")
    
    # Validate 'conditional_tasks'
    conditional_tasks = task_execution.get('conditional_tasks')
    if  not isinstance(conditional_tasks, dict):
        logging.error("Invalid 'conditional_tasks' in 'task_execution' section.")
        raise ValueError("Invalid 'conditional_tasks' in 'task_execution' section.")
    
    # Ensure all conditional tasks are defined in 'tasks' and conditions are valid
    for cond_task, condition_key in conditional_tasks.items():
        if cond_task not in tasks:
            logging.error(f"Conditional task '{cond_task}' is not defined in 'tasks' section.")
            raise ValueError(f"Conditional task '{cond_task}' is not defined in 'tasks' section.")
        if not isinstance(condition_key, str):
            logging.error(f"Condition for task '{cond_task}' must be a string representing a field name.")
            raise ValueError(f"Condition for task '{cond_task}' must be a string representing a field name.")
    
    logging.info("Configuration validation passed.")

def get_env_variable(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        logging.error(f"Environment variable {var_name} not found. Please set it.")
        raise ValueError(f"Environment variable {var_name} not found. Please set it.")
    return value
