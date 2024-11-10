# entrypoint/template_renderer.py

import os
import logging
from jinja2 import Environment, FileSystemLoader, select_autoescape, ChoiceLoader
from typing import Dict, Any

class TemplateRenderer:
    _instance = None

    def __new__(cls, prompts_dir: str = 'prompts'):
        if cls._instance is None:
            cls._instance = super(TemplateRenderer, cls).__new__(cls)
        return cls._instance

    def __init__(self, prompts_dir: str = 'prompts'):
        if not hasattr(self, 'initialized'):
            self.prompts_dir = prompts_dir
            self.env = self._initialize_environment()
            self.initialized = True  # Prevent re-initialization

    # entrypoint/template_renderer.py

    def _initialize_environment(self) -> Environment:
        """
        Initializes the Jinja2 environment with appropriate template loaders.

        Returns:
            Environment: Configured Jinja2 environment.
        """
        loaders = []

        # Load family-specific templates (e.g., 'llama')
        family_dirs = [
            d for d in os.listdir(self.prompts_dir)
            if os.path.isdir(os.path.join(self.prompts_dir, d)) and d not in ['default', 'base_templates', 'includes']
        ]
        for family_dir in family_dirs:
            family_templates_path = os.path.join(self.prompts_dir, family_dir)
            loaders.append(FileSystemLoader(family_templates_path))
            logging.debug(f"Added loader for family '{family_dir}'.")

        # Load default templates
        default_templates_path = os.path.join(self.prompts_dir, 'default')
        if os.path.exists(default_templates_path):
            loaders.append(FileSystemLoader(default_templates_path))
            logging.debug(f"Added loader for 'default' templates.")
        else:
            logging.warning(f"Default templates directory '{default_templates_path}' does not exist.")

        # Load base_templates
        base_templates_path = os.path.join(self.prompts_dir, 'base_templates')
        if os.path.exists(base_templates_path):
            loaders.append(FileSystemLoader(base_templates_path))
            logging.debug(f"Added loader for 'base_templates'.")
        else:
            logging.warning(f"Base templates directory '{base_templates_path}' does not exist.")

        # Load includes
        includes_path = os.path.join(self.prompts_dir, 'includes')
        if os.path.exists(includes_path):
            loaders.append(FileSystemLoader(includes_path))
            logging.debug(f"Added loader for 'includes'.")
        else:
            logging.warning(f"Includes directory '{includes_path}' does not exist.")

        # Load general templates from the root prompts directory
        loaders.append(FileSystemLoader(self.prompts_dir))
        logging.debug(f"Added loader for general templates in '{self.prompts_dir}'.")

        env = Environment(
            loader=ChoiceLoader(loaders),
            autoescape=select_autoescape(['jinja2'])
        )
        logging.debug("Initialized Jinja2 environment with all loaders.")
        return env

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Renders a template with the given context.

        Args:
            template_name (str): Name of the template file.
            context (Dict[str, Any]): Context variables for the template.

        Returns:
            str: Rendered template as a string.

        Raises:
            jinja2.TemplateNotFound: If the template is not found.
            jinja2.TemplateError: If rendering fails.
        """
        family_name = context.get('family')  # Retrieve 'model' from context

        try:
            if family_name:
                # Try to load model-specific template
                template_path = os.path.join(family_name, template_name)
                template = self.env.get_template(template_path)
                logging.debug(f"Loaded family-specific template '{template_path}'.")

            else:
                # Load default template
                template = self.env.get_template(template_name)
                logging.debug(f"Loaded default template '{template_name}'.")
        except Exception as e:
            logging.error(f"Template '{template_name}' not found for family '{family_name}': {e}")
            raise

        try:
            prompt = template.render(**context)
            logging.debug(f"Rendered prompt for template '{template_name}': {prompt[:50]}...")
            return prompt
        except Exception as e:
            logging.error(f"Error rendering template '{template_name}': {e}")
            raise
