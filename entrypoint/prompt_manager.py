# entrypoint/prompt_manager.py

import os
import logging
import glob
from typing import List, Dict, Any

class PromptManager:
    def __init__(self, styling_guides_dir: str = 'styling_guides'):
        self.styling_guide_cache: Dict[str, str] = {}
        self.load_all_styling_guides(styling_guides_dir)

    def load_all_styling_guides(self, styling_guides_dir: str) -> None:
        """
        Loads all styling guides from the specified directory into the cache.

        Args:
            styling_guides_dir (str): Path to the styling guides directory.
        """
        pattern = os.path.join(styling_guides_dir, '**', '*.txt')
        for filepath in glob.iglob(pattern, recursive=True):
            product_type = os.path.basename(os.path.dirname(filepath))
            with open(filepath, 'r') as file:
                self.styling_guide_cache[product_type] = file.read()
            logging.debug(f"Loaded styling guide for product type: {product_type}")
        logging.info(f"Loaded styling guides for product types: {list(self.styling_guide_cache.keys())}")

    def generate_prompts(self, item_title: str, short_description: str, long_description: str,
                        product_type: str, tasks: List[str]) -> List[Dict[str, Any]]:
        """
        Generates prompts for each task based on the item details and styling guide.

        Args:
            item_title (str): Original item title.
            short_description (str): Original short description.
            long_description (str): Original long description.
            product_type (str): Product type to fetch the relevant styling guide.
            tasks (List[str]): List of tasks to generate prompts for.

        Returns:
            List[Dict[str, Any]]: A list of prompts with associated task names.
        """
        styling_guide = self.styling_guide_cache.get(product_type)
        if not styling_guide:
            logging.error(f"No styling guide found for product type: {product_type}")
            raise ValueError(f"No styling guide found for product type: {product_type}")

        prompts_tasks = []
        for task in tasks:
            if task == "title_enhancement":
                prompt = f"{styling_guide}\n\nEnhance the following title:\nOriginal Title: {item_title}"
            elif task == "short_description_enhancement":
                prompt = f"{styling_guide}\n\nEnhance the following short description:\nOriginal Short Description: {short_description}"
            elif task == "long_description_enhancement":
                prompt = f"{styling_guide}\n\nEnhance the following long description:\nOriginal Long Description: {long_description}"
            else:
                logging.warning(f"Unknown task: {task}")
                continue  # Skip unknown tasks
            prompts_tasks.append({"task": task, "prompt": prompt})
            logging.debug(f"Generated prompt for task '{task}'")
        return prompts_tasks
