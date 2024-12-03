import logging
from typing import Optional
from sqlalchemy.orm import Session
from models.models import (
    GenerationPromptTemplate,
    EvaluationPromptTemplate,
    GenerationTask,
    EvaluationTask,
    ModelFamily
)

class TemplateRenderer:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_template(
        self,
        task_name: str,
        task_type: str,
        model_family_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Fetches the latest template content for a given task, type, and model family.

        Args:
            task_name (str): The name of the task.
            task_type (str): The type of the task ('generation' or 'evaluation').
            model_family_name (Optional[str]): The model family name.

        Returns:
            Optional[str]: The template content if found, None otherwise.
        """
        try:
            if model_family_name:
                model_family = self.db_session.query(ModelFamily).filter_by(name=model_family_name).first()
                if not model_family:
                    logging.error(f"Model family '{model_family_name}' not found.")
                    return None
                model_family_id = model_family.model_family_id
            else:
                model_family_id = None

            if task_type == 'generation':
                template_class = GenerationPromptTemplate
                task_class = GenerationTask
                task_id_field = GenerationPromptTemplate.task_id
            elif task_type == 'evaluation':
                template_class = EvaluationPromptTemplate
                task_class = EvaluationTask
                task_id_field = EvaluationPromptTemplate.task_id
            else:
                logging.error(f"Invalid task type '{task_type}'. Must be 'generation' or 'evaluation'.")
                return None

            # Fetch the task
            task = self.db_session.query(task_class).filter_by(task_name=task_name).first()
            if not task:
                logging.error(f"Task '{task_name}' not found.")
                return None

            # Fetch the template
            query = self.db_session.query(template_class).filter(
                task_id_field == task.task_id,
                template_class.model_family_id == model_family_id
            ).order_by(template_class.version.desc())
            template = query.first()

            if template:
                return template.template_text
            else:
                return None

        except Exception as e:
            logging.error(f"Error fetching template content: {e}")
            return None