# utils.py
import os
import logging
import json
import yaml

def setup_logging(level=logging.DEBUG):
    logging.basicConfig(level=level)
    logging.info("Logging is configured.")

def load_config(config_path: str) -> dict[str, any]:
    """
    Loads the configuration from a JSON or YAML file.
    """
    try:
        with open(config_path, 'r') as file:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
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

def validate_config(config: dict[str, any]):
    """
    Validates the configuration to ensure all required fields are present.
    """
    required_tasks = ["title_enhancement", "short_description_enhancement", "long_description_enhancement", "attribute_extraction", "vision_attribute_extraction"]
    for provider in config.get('providers', []):
        if 'name' not in provider or 'provider' not in provider or 'model' not in provider:
            logging.error(f"Provider configuration incomplete: {provider}")
            raise ValueError(f"Provider configuration incomplete: {provider}")
    
    for task in required_tasks:
        if task not in config.get('tasks', {}):
            logging.error(f"Task '{task}' is missing in the 'tasks' section.")
            raise ValueError(f"Task '{task}' is missing in the 'tasks' section.")
        if 'max_tokens' not in config['tasks'][task]:
            logging.error(f"'max_tokens' missing for task '{task}'.")
            raise ValueError(f"'max_tokens' missing for task '{task}'.")
    
    logging.info("Configuration validation passed.")

def get_env_variable(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        logging.error(f"Environment variable {var_name} not found. Please set it.")
        raise ValueError(f"Environment variable {var_name} not found. Please set it.")
    return value
