# ui/admin_database_handler.py

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models.models import (
    Template,
    TaskConfig,
    ProviderConfig,
    StylingGuide,
    # Add other models as needed
)
from models.database import Base

# Create a new database session for the admin interface
engine = create_engine('sqlite:///your_database.db')  # Update with your database path
SessionLocal = sessionmaker(bind=engine)

# ui/admin_database_handler.py

class AdminDatabaseHandler:
    def __init__(self):
        self.db_session = SessionLocal()

    # -----------------------
    # Template CRUD Operations
    # -----------------------

    def get_templates(self):
        return self.db_session.query(Template).all()

    def create_template(self, template_data):
        template = Template(**template_data)
        self.db_session.add(template)
        self.db_session.commit()

    def update_template(self, template_id, updated_data):
        template = self.db_session.query(Template).filter(Template.template_id == template_id).first()
        for key, value in updated_data.items():
            setattr(template, key, value)
        self.db_session.commit()

    def delete_template(self, template_id):
        template = self.db_session.query(Template).filter(Template.template_id == template_id).first()
        self.db_session.delete(template)
        self.db_session.commit()

    # -----------------------
    # TaskConfig CRUD Operations
    # -----------------------

    def get_tasks(self):
        return self.db_session.query(TaskConfig).all()

    def create_task(self, task_data):
        task = TaskConfig(**task_data)
        self.db_session.add(task)
        self.db_session.commit()

    def update_task(self, task_id, updated_data):
        task = self.db_session.query(TaskConfig).filter(TaskConfig.task_id == task_id).first()
        for key, value in updated_data.items():
            setattr(task, key, value)
        self.db_session.commit()

    def delete_task(self, task_id):
        task = self.db_session.query(TaskConfig).filter(TaskConfig.task_id == task_id).first()
        self.db_session.delete(task)
        self.db_session.commit()

    # -----------------------
    # ProviderConfig CRUD Operations
    # -----------------------

    def get_providers(self):
        return self.db_session.query(ProviderConfig).all()

    def create_provider(self, provider_data):
        provider = ProviderConfig(**provider_data)
        self.db_session.add(provider)
        self.db_session.commit()

    def update_provider(self, provider_id, updated_data):
        provider = self.db_session.query(ProviderConfig).filter(ProviderConfig.provider_id == provider_id).first()
        for key, value in updated_data.items():
            setattr(provider, key, value)
        self.db_session.commit()

    def delete_provider(self, provider_id):
        provider = self.db_session.query(ProviderConfig).filter(ProviderConfig.provider_id == provider_id).first()
        self.db_session.delete(provider)
        self.db_session.commit()

    # -----------------------
    # StylingGuide CRUD Operations
    # -----------------------

    def get_styling_guides(self):
        return self.db_session.query(StylingGuide).all()

    def create_styling_guide(self, guide_data):
        guide = StylingGuide(**guide_data)
        self.db_session.add(guide)
        self.db_session.commit()

    def update_styling_guide(self, guide_id, updated_data):
        guide = self.db_session.query(StylingGuide).filter(StylingGuide.styling_guide_id == guide_id).first()
        for key, value in updated_data.items():
            setattr(guide, key, value)
        self.db_session.commit()

    def delete_styling_guide(self, guide_id):
        guide = self.db_session.query(StylingGuide).filter(StylingGuide.styling_guide_id == guide_id).first()
        self.db_session.delete(guide)
        self.db_session.commit()

    # Add methods for task execution configs and other entities as needed

