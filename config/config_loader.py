# config_loader.py
import json
from pathlib import Path
from typing import Dict, Any
import os

class ConfigLoader:
    @staticmethod
    def load_config(config_path: str) -> Dict[str, Any]:
        """
        Loads the configuration from a JSON file.

        Args:
            config_path (str): The path to the configuration file.

        Returns:
            Dict[str, Any]: The configuration data as a dictionary.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            ValueError: If the configuration file contains invalid JSON.
        """
        config_file_path = Path(os.path.normpath(config_path))
        if not config_file_path.is_file():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_file_path, 'r') as config_file:
                return json.load(config_file)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON from the configuration file: {e}")
