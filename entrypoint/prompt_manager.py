# entrypoint/prompt_manager.py

import os
import logging
import glob
import difflib  # For fuzzy matching

from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader, ChoiceLoader, select_autoescape

class PromptManager:
    _instance = None

    def __new__(cls, styling_guides_dir: str = 'styling_guides', prompts_dir: str = 'prompts'):
        if cls._instance is None:
            cls._instance = super(PromptManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, styling_guides_dir: str = 'styling_guides', prompts_dir: str = 'prompts'):
        if not hasattr(self, 'initialized'):
            self.styling_guide_cache: Dict[str, str] = {}
            self.load_all_styling_guides(styling_guides_dir)
            self.prompts_dir = prompts_dir
            self.env = self._initialize_environment()
            self.initialized = True  # To prevent re-initialization

    def _initialize_environment(self):
        loaders = []
        # Load model-specific templates
        model_dirs = [
            d for d in os.listdir(self.prompts_dir)
            if os.path.isdir(os.path.join(self.prompts_dir, d)) and d != 'default'
        ]
        for model_dir in model_dirs:
            model_templates_path = os.path.join(self.prompts_dir, model_dir)
            loaders.append(FileSystemLoader(model_templates_path))
        # Load default templates
        loaders.append(FileSystemLoader(os.path.join(self.prompts_dir, 'default')))
        # Load general templates (e.g., 'general_instructions.jinja2')
        loaders.append(FileSystemLoader(self.prompts_dir))
        env = Environment(
            loader=ChoiceLoader(loaders),
            autoescape=select_autoescape(['jinja2'])
        )
        return env

    def load_all_styling_guides(self, styling_guides_dir: str) -> None:
        """
        Loads all styling guides from the specified directory into the cache.
        """
        pattern = os.path.join(styling_guides_dir, '**', '*.txt')
        for filepath in glob.iglob(pattern, recursive=True):
            product_type = os.path.basename(os.path.dirname(filepath)).strip(' "\'').lower()
            logging.info(f"Loading styling guide for product type: {product_type}")

            with open(filepath, 'r', encoding='utf-8') as file:
                self.styling_guide_cache[product_type] = file.read()

        logging.info(f"Loaded styling guides for product types: {list(self.styling_guide_cache.keys())}")

    def get_styling_guide(self, product_type: str) -> str:
        """
        Retrieves the styling guide for the given product type.
        """
        product_type = product_type.lower()
        styling_guide = self.styling_guide_cache.get(product_type)

        if not styling_guide:
            # Perform fuzzy matching
            closest_matches = difflib.get_close_matches(
                product_type, self.styling_guide_cache.keys(), n=1, cutoff=0.6
            )
            if closest_matches:
                matched_product_type = closest_matches[0]
                logging.info(f"Fuzzy matched '{product_type}' to '{matched_product_type}'")
                styling_guide = self.styling_guide_cache[matched_product_type]
            else:
                error_msg = f"No styling guide found for product type: '{product_type}'"
                logging.error(error_msg)
                raise ValueError(error_msg)

        return styling_guide

    def generate_prompts(
        self, item: Dict[str, Any], tasks: List[str], model: str = None
    ) -> List[Dict[str, Any]]:
        """
        Generates prompts for each task based on the item details and styling guide.
        """
        product_type = item.get('product_type', '').lower()
        logging.info(f"Generating prompts for product type: '{product_type}' with tasks: {tasks}")

        # Retrieve the styling guide
        try:
            styling_guide = self.get_styling_guide(product_type)
        except ValueError as e:
            logging.error(str(e))
            raise

        # Prepare context
        context = {
            'styling_guide': styling_guide,
            'original_title': item.get('item_title', ''),
            'original_short_description': item.get('short_description', ''),
            'original_long_description': item.get('long_description', ''),
            'product_type': product_type,
            'image_url': item.get('image_url', ''),
            'attributes_list': item.get('attributes_list', []),
            # Add additional placeholders as needed
        }

        # Remove None or empty values from context
        context = {k: v for k, v in context.items() if v}

        prompts_tasks = []
        for task in tasks:
            template_name = f"{task}_prompt.jinja2"

            # Load the template
            try:
                if model:
                    # Try to load model-specific template
                    template_path = os.path.join(model, template_name)
                    template = self.env.get_template(template_path)
                else:
                    # Load default template
                    template = self.env.get_template(template_name)
            except Exception as e:
                logging.error(f"Template for task '{task}' not found: {str(e)}")
                continue  # Skip this task

            # Render the prompt
            try:
                prompt = template.render(**context)
            except Exception as e:
                logging.error(f"Error rendering template for task '{task}': {str(e)}")
                continue  # Skip this task

            prompts_tasks.append({'task': task, 'prompt': prompt})
            logging.debug(f"Generated prompt for task '{task}': {prompt[:50]}...")

        return prompts_tasks
