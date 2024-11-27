# entrypoint/template_renderer.py

import logging
from jinja2 import Environment, BaseLoader, TemplateNotFound
from sqlalchemy.orm import Session
from models.models import Template

class DatabaseTemplateLoader(BaseLoader):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_source(self, environment, template_name):
        try:
            template = (
                self.db_session.query(Template)
                .filter_by(template_name=template_name, is_active=True)
                .order_by(Template.version.desc())
                .first()
            )
            if template:
                source = template.content
                return source, None, lambda: False
            else:
                raise TemplateNotFound(template_name)
        except Exception as e:
            logging.error(f"Error loading template '{template_name}': {e}")
            raise TemplateNotFound(template_name)

class TemplateRenderer:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.env = Environment(loader=DatabaseTemplateLoader(db_session))

    def render_template(self, template_name: str, context: dict) -> str:
        try:
            template = self.env.get_template(template_name)
            rendered_content = template.render(**context)
            return rendered_content
        except TemplateNotFound:
            logging.error(f"Template '{template_name}' not found.")
            raise
        except Exception as e:
            logging.error(f"Error rendering template '{template_name}': {e}")
            raise
