# entrypoint/styling_guide_manager.py

import os
import logging
import glob
import difflib
from typing import Dict, Any

class StylingGuideManager:
    _instance = None

    def __new__(cls, styling_guides_dir: str = 'styling_guides'):
        if cls._instance is None:
            cls._instance = super(StylingGuideManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, styling_guides_dir: str = 'styling_guides'):
        if not hasattr(self, 'initialized'):
            self.styling_guides_dir = styling_guides_dir
            # Nested dictionary: {product_type: {task: guide_content}}
            self.styling_guide_cache: Dict[str, Dict[str, str]] = {}
            self.load_all_styling_guides()
            self.initialized = True  # Prevent re-initialization

    def load_all_styling_guides(self) -> None:
        """
        Loads all styling guides from the specified directory into the cache.
        """
        pattern = os.path.join(self.styling_guides_dir, '**', '*.txt')
        for filepath in glob.iglob(pattern, recursive=True):
            # Assume the styling guide is stored in a folder named after the product type
            product_type = os.path.basename(os.path.dirname(filepath)).strip(' "\'').lower()
            task_name = os.path.splitext(os.path.basename(filepath))[0].strip().lower()
            logging.info(f"Loading styling guide for product type: '{product_type}', task: '{task_name}' from '{filepath}'")

            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                if content:
                    if product_type not in self.styling_guide_cache:
                        self.styling_guide_cache[product_type] = {}
                    self.styling_guide_cache[product_type][task_name] = content
                    logging.debug(f"Loaded styling guide for '{product_type}' - '{task_name}'.")
                else:
                    logging.warning(f"Styling guide for '{product_type}' - '{task_name}' is empty. Skipping.")

        if not self.styling_guide_cache:
            logging.error(f"No styling guides loaded from '{self.styling_guides_dir}'.")
            raise ValueError(f"No styling guides loaded from '{self.styling_guides_dir}'.")

        logging.info(f"Loaded styling guides for product types: {list(self.styling_guide_cache.keys())}")

    def get_styling_guide(self, product_type: str, task: str) -> str:
        """
        Retrieves the styling guide for the given product type and task. Uses fuzzy matching if exact match is not found.

        Args:
            product_type (str): The product type.
            task (str): The task name (e.g., 'title_enhancement').

        Returns:
            str: The styling guide content.

        Raises:
            ValueError: If no styling guide is found for the product type or task.
        """
        product_type = product_type.lower()
        task = task.lower()
        product_guides = self.styling_guide_cache.get(product_type)

        if not product_guides:
            # Perform fuzzy matching on product_type
            closest_matches = difflib.get_close_matches(
                product_type, self.styling_guide_cache.keys(), n=1, cutoff=0.6
            )
            if closest_matches:
                matched_product_type = closest_matches[0]
                product_guides = self.styling_guide_cache[matched_product_type]
                logging.info(f"Fuzzy matched product type '{product_type}' to '{matched_product_type}'")
            else:
                error_msg = f"No styling guide found for product type: '{product_type}'"
                logging.error(error_msg)
                raise ValueError(error_msg)

        styling_guide = product_guides.get(task)
        if styling_guide:
            logging.debug(f"Found exact styling guide for product type '{product_type}', task '{task}'")
            return styling_guide

        # Perform fuzzy matching on task
        closest_task = difflib.get_close_matches(
            task, product_guides.keys(), n=1, cutoff=0.6
        )
        if closest_task:
            task = closest_task[0]
            styling_guide = product_guides[task]
            logging.info(f"Fuzzy matched task '{task}' to '{closest_task[0]}'")
            return styling_guide

        error_msg = f"No styling guide found for task: '{task}' under product type: '{product_type}'"
        logging.error(error_msg)
        raise ValueError(error_msg)
