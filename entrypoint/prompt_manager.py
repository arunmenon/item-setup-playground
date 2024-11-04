# entrypoint/prompt_manager.py

import os
import logging
from typing import List, Dict, Any, Optional
from common.utils import load_config, validate_config
from .styling_guide_manager import StylingGuideManager
from .template_renderer import TemplateRenderer
from .task_manager import TaskManager

class PromptManager:
    _instance = None

    def __new__(cls, 
                config_path: Optional[str] = None, 
                styling_guides_dir: str = 'styling_guides', 
                prompts_dir: str = 'prompts',
                config: Optional[Dict[str, Any]] = None):
        if cls._instance is None:
            cls._instance = super(PromptManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, 
                 config_path: Optional[str] = None, 
                 styling_guides_dir: str = 'styling_guides',
                 prompts_dir: str = 'prompts',
                 config:Optional[Dict]= None):
        if not hasattr(self, 'initialized'):
            # Load and validate the configuration
             # Load and validate the configuration
            if config is not None:
                self.config = config
                logging.info("Configuration loaded from provided 'config' parameter.")
            elif config_path is not None:
                self.config = load_config(config_path)
                logging.info(f"Configuration loaded from '{config_path}'.")
            
            self.tasks_config: Dict[str, Dict[str, Any]] = self.config.get('tasks', {})
            self.task_execution: Dict[str, Any] = self.config.get('task_execution', {})
            self.prompts_dir = prompts_dir

            # Initialize Helper Classes
            self.styling_guide_manager = StylingGuideManager(styling_guides_dir)
            self.template_renderer = TemplateRenderer(prompts_dir=prompts_dir)
            self.task_manager = TaskManager(self.tasks_config, self.task_execution)

            self.initialized = True  # Prevent re-initialization

    def generate_prompts(self, item: Dict[str, Any], model: str = None) -> List[Dict[str, Any]]:
        """
        Generates prompts for each task based on the item details and styling guide.
        Each prompt includes the desired output format.

        Args:
            item (Dict[str, Any]): The input data containing item details.
            model (str, optional): The model to use for template selection. Defaults to None.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing task details and generated prompts.
        """
        product_type = item.get('product_type', '').lower()
        logging.info(f"Generating prompts for product type: '{product_type}'")

        # Generate prompts_tasks list
        prompts_tasks = []

        # Handle default tasks
        default_tasks = self.task_manager.get_default_tasks()
        logging.debug(f"Default tasks: {default_tasks}")
        self.handle_tasks(model, item, product_type, prompts_tasks, default_tasks, is_conditional=False)

        # Handle conditional tasks
        self.handle_conditional_tasks(item, model, product_type, prompts_tasks)

        return prompts_tasks

    def handle_tasks(
        self, 
        model: Optional[str], 
        item: Dict[str, Any],
        product_type: str,
        prompts_tasks: List[Dict[str, Any]], 
        tasks: List[str], 
        is_conditional: bool
    ):
        """
        Processes and generates prompts for a list of tasks.
        """
        for task in tasks:
            if not self.task_manager.is_task_defined(task):
                logging.warning(f"Task '{task}' is not defined in the tasks configuration. Skipping.")
                continue

            template_name = f"{task}_prompt.jinja2"

            # Get task configuration
            output_format = self.task_manager.get_task_output_format(task)

            # Retrieve task-specific styling guide
            try:
                styling_guide = self.styling_guide_manager.get_styling_guide(product_type, task)
            except ValueError as e:
                logging.error(str(e))
                continue  # Skip this task

            # Prepare context
            context = self.prepare_prompt_context(item, product_type, styling_guide)

            context_with_format = context.copy()
            context_with_format['output_format'] = output_format

            # Include 'model' in context if provided
            if model:
                context_with_format['model'] = model

            # Render the prompt using TemplateRenderer
            try:
                # Pass only 'template_name' and 'context_with_format'
                prompt = self.template_renderer.render_template(template_name, context_with_format)
                logging.debug(f"Rendered prompt for task '{task}': {prompt[:50]}...")
            except Exception as e:
                logging.error(f"Error rendering template for task '{task}': {str(e)}")
                continue  # Skip this task

            # Append task, prompt, and output_format
            prompts_tasks.append({
                'task': task,
                'prompt': prompt,
                'output_format': output_format
            })
            task_type = "conditional" if is_conditional else "default"
            logging.info(f"Generated prompt for {task_type} task '{task}'.")

    def handle_conditional_tasks(
        self, 
        item: Dict[str, Any], 
        model: Optional[str], 
        product_type: str,
        prompts_tasks: List[Dict[str, Any]]
    ):
        """
        Processes and generates prompts for conditional tasks based on input data.
        """
        conditional_tasks = self.task_manager.get_conditional_tasks()
        for cond_task, condition_key in conditional_tasks.items():
            if condition_key and item.get(condition_key):
                # Process the conditional task
                self.handle_tasks(model, item, product_type, prompts_tasks, [cond_task], is_conditional=True)

    def prepare_prompt_context(self, item: Dict[str, Any], product_type: str, styling_guide: str) -> Dict[str, Any]:
        """
        Prepares the context dictionary for prompt rendering.

        Args:
            item (Dict[str, Any]): The input data containing item details.
            product_type (str): The product type.
            styling_guide (str): The styling guide content.

        Returns:
            Dict[str, Any]: The context dictionary with necessary placeholders.
        """
        context = {
            'styling_guide': styling_guide,
            'original_title': item.get('item_title', ''),
            'original_short_description': item.get('short_description', ''),
            'original_long_description': item.get('long_description', ''),
            'product_type': product_type,
            'image_url': item.get('image_url', ''),
            'attributes_list': item.get('attributes_list', []),
            'output_format': 'json'
            # Add additional placeholders as needed
        }

        # Remove None or empty values from context
        context = {k: v for k, v in context.items() if v}
        logging.debug(f"Context after filtering: {context}")
        return context
