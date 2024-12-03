import logging
import traceback
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from entrypoint.styling_guide_manager import StylingGuideManager
from entrypoint.template_renderer import TemplateRenderer
from entrypoint.task_manager import TaskManager
from models.models import GenerationTask, EvaluationTask, ModelFamily


class PromptManager:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        # Initialize Helper Classes
        self.styling_guide_manager = StylingGuideManager(db_session)
        self.template_renderer = TemplateRenderer(db_session)
        self.task_manager = TaskManager(db_session)

    def generate_prompts(self, item: Dict[str, Any], family_name: Optional[str], task_type: str) -> List[
        Dict[str, Any]]:
        """
        Generates prompts for each task based on the item details and styling guide.
        Each prompt includes the desired output format.

        Args:
            item (Dict[str, Any]): The input data containing item details.
            family_name (Optional[str]): The model family name used for template selection.
            task_type (str): The type of the task ('generation' or 'evaluation').

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing task details and generated prompts.
        """
        # product_type = item.get('item_product_type', '').lower()
        product_type = item.get('product_type', '').lower()
        logging.info(f"Generating prompts for product type: '{product_type}', task type: '{task_type}'")

        # Generate prompts_tasks list
        prompts_tasks = []

        # Handle default tasks
        default_tasks = self.task_manager.get_default_tasks(task_type)
        logging.debug(f"Default tasks: {default_tasks}")
        self.handle_tasks(family_name, item, product_type, prompts_tasks, default_tasks, task_type, is_conditional=False)

        # Handle conditional tasks
        self.handle_conditional_tasks(item, family_name, product_type, prompts_tasks, task_type)

        return prompts_tasks

    def handle_tasks(
            self,
            family_name: Optional[str],
            item: Dict[str, Any],
            product_type: str,
            prompts_tasks: List[Dict[str, Any]],
            tasks: List[str],
            task_type: str,
            is_conditional: bool
    ):
        for task_name in tasks:
            if not self.task_manager.is_task_defined(task_name, task_type):
                logging.warning(f"Task '{task_name}' is not defined in the tasks configuration. Skipping.")
                continue

            # Get task configuration
            task_config = self.task_manager.get_task_config(task_name, task_type)
            output_format = task_config.get('output_format', 'json')
            max_tokens = task_config.get('max_tokens', 150)

            # Retrieve task-specific styling guide
            try:
                styling_guide = self.styling_guide_manager.get_styling_guide(product_type, task_name)
            except ValueError as e:
                logging.error(str(e))
                continue  # Skip this task

            # Prepare context
            context = self.prepare_prompt_context(item, product_type, styling_guide)

            # Fetch the appropriate template content from the database
            template_content = self.template_renderer.get_template(task_name, task_type, family_name)
            if not template_content:
                logging.error(f"No template found for task '{task_name}', family '{family_name}', and task type '{task_type}'. Skipping.")
                continue

            # Since templates are plain text with placeholders, use Python's string formatting
            try:
                # prompt = template_content.format(**context)
                # Render the template using Jinja2
                prompt = self.template_renderer.render_template(template_content, context)
                if not prompt:
                    logging.error(f"Failed to render template for task '{task_name}'. Skipping.")
                    continue
                logging.debug(f"Generated prompt for task '{task_name}': {prompt[:50]}...")
            except KeyError as e:
                missing_key = e.args[0]
                print (traceback.print_exc())
                logging.error(f"Missing placeholder '{missing_key}' in context for task '{task_name}'. Skipping this task.")
                continue
            except Exception as e:
                logging.error(f"Error formatting template for task '{task_name}': {str(e)}")
                continue  # Skip this task

            # Append task, prompt, output_format, and max_tokens
            prompts_tasks.append({
                'task'         : task_name,
                'prompt'       : prompt,
                'output_format': output_format,
                'max_tokens'   : max_tokens
            })
            task_type_str = "conditional" if is_conditional else "default"
            logging.debug(f"Generated prompt for {task_type_str} task '{task_name}'.")

    def handle_conditional_tasks(
            self,
            item: Dict[str, Any],
            family_name: Optional[str],
            product_type: str,
            prompts_tasks: List[Dict[str, Any]],
            task_type: str
    ):
        conditional_tasks = self.task_manager.get_conditional_tasks(task_type)
        for task_name, condition_key in conditional_tasks.items():
            if condition_key and item.get(condition_key):
                self.handle_tasks(family_name, item, product_type, prompts_tasks, [
                    task_name], task_type, is_conditional=True)

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
            'styling_guide'             : styling_guide,
            'original_title'            : item.get('item_title', ''),
            'original_short_description': item.get('short_description', ''),
            'original_long_description' : item.get('long_description', ''),
            'product_type'              : product_type,
            'image_url'                 : item.get('image_url', ''),
            'attributes_list'           : item.get('attributes_list', []),
            'output_format'             : 'json'
            # Add additional placeholders as needed
        }

        # Remove None or empty values from context
        context = {k: v for k, v in context.items() if v}
        logging.debug(f"Context after filtering: {context}")
        return context