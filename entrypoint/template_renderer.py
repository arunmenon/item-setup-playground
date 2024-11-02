# entrypoint/template_renderer.py

import os
import logging
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, ChoiceLoader, select_autoescape

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

    def _initialize_environment(self) -> Environment:
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
        default_templates_path = os.path.join(self.prompts_dir, 'default')
        if os.path.exists(default_templates_path):
            loaders.append(FileSystemLoader(default_templates_path))
        else:
            logging.warning(f"Default templates directory '{default_templates_path}' does not exist.")

        # Load general templates (e.g., 'general_instructions.jinja2')
        loaders.append(FileSystemLoader(self.prompts_dir))
        env = Environment(
            loader=ChoiceLoader(loaders),
            autoescape=select_autoescape(['jinja2'])
        )
        return env

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Renders a template with the given context.

        Args:
            template_name (str): Name of the template file.
            context (Dict[str, Any]): Context variables for the template.
            model (str, optional): Model-specific template directory.

        Returns:
            str: Rendered template as a string.

        Raises:
            jinja2.TemplateNotFound: If the template is not found.
            jinja2.TemplateError: If rendering fails.
        """
        model = context.get('model')  # Retrieve 'model' from context
        try:
            if model:
                # Try to load model-specific template
                template_path = os.path.join(model, template_name)
                template = self.env.get_template(template_path)
            else:
                # Load default template
                template = self.env.get_template(template_name)
            logging.debug(f"Loaded template '{template_name}' for model '{model}'.")
        except Exception as e:
            logging.error(f"Template '{template_name}' not found for model '{model}': {e}")
            raise

        try:
            prompt = template.render(**context)
            logging.debug(f"Rendered prompt for template '{template_name}': {prompt[:50]}...")
            return prompt
        except Exception as e:
            logging.error(f"Error rendering template '{template_name}': {e}")
            raise
