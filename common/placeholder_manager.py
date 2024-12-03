# common/placeholder_manager.py

import logging
from jinja2 import Environment, meta
from sqlalchemy.orm import Session
from models.models import Placeholder, Template

class PlaceholderManager:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.env = Environment()

    def extract_placeholders(self, template_content: str) -> set:
        ast = self.env.parse(template_content)
        placeholders = meta.find_undeclared_variables(ast)
        return placeholders

    def update_template_placeholders(self, template: Template):
        placeholders_in_content = self.extract_placeholders(template.content)
        existing_placeholders = {ph.name for ph in template.placeholders}
        placeholders_to_add = placeholders_in_content - existing_placeholders

        # Add new placeholders
        for ph_name in placeholders_to_add:
            placeholder = self.db_session.query(Placeholder).filter_by(name=ph_name).first()
            if not placeholder:
                # Ideally, prompt the user to define the placeholder
                placeholder = Placeholder(
                    name=ph_name,
                    data_type='string',  # Default; consider prompting for actual data type
                    description='',
                    default_value=''
                )
                self.db_session.add(placeholder)
                self.db_session.commit()
            template.placeholders.append(placeholder)

        # Remove placeholders no longer in content
        placeholders_to_remove = existing_placeholders - placeholders_in_content
        for ph_name in placeholders_to_remove:
            placeholder = self.db_session.query(Placeholder).filter_by(name=ph_name).first()
            if placeholder:
                template.placeholders.remove(placeholder)

        self.db_session.commit()
