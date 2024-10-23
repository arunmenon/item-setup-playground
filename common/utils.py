# utils.py
import os
import logging
import json

def setup_logging(level=logging.DEBUG):
    logging.basicConfig(level=level)
    logging.info("Logging is configured.")

def load_config(config_path: str) -> dict:
    try:
        with open(config_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error("Configuration file not found at %s", config_path)
        raise ValueError("Configuration file not found. Please ensure the correct path is provided.")
    except Exception as e:
        logging.error("Error loading configuration: %s", str(e))
        raise ValueError(f"Error loading configuration: {str(e)}")

def get_env_variable(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        logging.error(f"Environment variable {var_name} not found. Please set it.")
        raise ValueError(f"Environment variable {var_name} not found. Please set it.")
    return value
