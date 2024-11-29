# ui/admin_database_handler.py

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models.models import (
    EvaluationPromptTemplate,
    GenerationPromptTemplate,
    GenerationTask,
    EvaluationTask,
    ModelFamily,
    ProviderConfig,
    StylingGuide,
    # Add other models as needed
)
from models.database import Base

# Create a new database session for the admin interface
engine = create_engine('sqlite:///your_database.db')  # Update with your database path
SessionLocal = sessionmaker(bind=engine)

class AdminDatabaseHandler:
    def __init__(self):
        self.db_session = SessionLocal()

    # -----------------------
    # Model Family CRUD Operations
    # -----------------------
    def get_model_families(self):
        return self.db_session.query(ModelFamily).all()
    
    def create_model_family(self, name):
        model_family = ModelFamily(name=name)
        self.db_session.add(model_family)
        self.db_session.commit()

    def update_model_family(self, model_family_id, updated_data):
        model_family = self.db_session.query(ModelFamily).get(model_family_id)
        for key, value in updated_data.items():
            setattr(model_family, key, value)
        self.db_session.commit()

    def delete_model_family(self, model_family_id):
        model_family = self.db_session.query(ModelFamily).get(model_family_id)
        self.db_session.delete(model_family)
        self.db_session.commit()

    # -----------------------
    # Generation Task CRUD Operations
    # -----------------------
    def get_generation_tasks(self):
        return self.db_session.query(GenerationTask).all()

    def create_generation_task(self, task_data):
        task = GenerationTask(**task_data)
        self.db_session.add(task)
        self.db_session.commit()
        return task  # Return the task in case we need its ID

    def update_generation_task(self, task_id, updated_data):
        task = self.db_session.query(GenerationTask).get(task_id)
        for key, value in updated_data.items():
            setattr(task, key, value)
        self.db_session.commit()

    def delete_generation_task(self, task_id):
        task = self.db_session.query(GenerationTask).get(task_id)
        self.db_session.delete(task)
        self.db_session.commit()

    # -----------------------
    # Evaluation Task CRUD Operations
    # -----------------------
    def get_evaluation_tasks(self):
        return self.db_session.query(EvaluationTask).all()

    def create_evaluation_task(self, task_data):
        task = EvaluationTask(**task_data)
        self.db_session.add(task)
        self.db_session.commit()
        return task

    def update_evaluation_task(self, task_id, updated_data):
        task = self.db_session.query(EvaluationTask).get(task_id)
        for key, value in updated_data.items():
            setattr(task, key, value)
        self.db_session.commit()

    def delete_evaluation_task(self, task_id):
        task = self.db_session.query(EvaluationTask).get(task_id)
        self.db_session.delete(task)
        self.db_session.commit()

    # -----------------------
    # Generation Prompt Template CRUD Operations
    # -----------------------
    def get_generation_prompt_templates(self, task_id=None):
        query = self.db_session.query(GenerationPromptTemplate)
        if task_id:
            query = query.filter(GenerationPromptTemplate.task_id == task_id)
        return query.all()

    def create_generation_prompt_template(self, template_data):
        model_family_name = template_data.pop('model_family')
        model_family = self.db_session.query(ModelFamily).filter_by(name=model_family_name).first()

        if model_family:
            template_data['model_family_id'] = model_family.model_family_id
            template = GenerationPromptTemplate(**template_data)
            self.db_session.add(template)
            self.db_session.commit()
        else:
            raise ValueError(f"Model family '{model_family_name}' does not exist.")

    def update_generation_prompt_template(self, template_id, updated_data):
        template = self.db_session.query(GenerationPromptTemplate).get(template_id)

        if 'model_family' in updated_data:
            model_family_name = updated_data.pop('model_family')
            model_family = self.db_session.query(ModelFamily).filter_by(name=model_family_name).first()

            if model_family:
                updated_data['model_family_id'] = model_family.model_family_id
            else:
                raise ValueError(f"Model family '{model_family_name}' does not exist.")

        for key, value in updated_data.items():
            setattr(template, key, value)

        self.db_session.commit()

    def delete_generation_prompt_template(self, template_id):
        template = self.db_session.query(GenerationPromptTemplate).get(template_id)
        self.db_session.delete(template)
        self.db_session.commit()

    # -----------------------
    # Evaluation Prompt Template CRUD Operations
    # -----------------------
    def get_evaluation_prompt_templates(self, task_id=None):
        query = self.db_session.query(EvaluationPromptTemplate)
        if task_id:
            query = query.filter(EvaluationPromptTemplate.task_id == task_id)
        return query.all()

    def create_evaluation_prompt_template(self, template_data):
        model_family_name = template_data.pop('model_family')
        model_family = self.db_session.query(ModelFamily).filter_by(name=model_family_name).first()

        if model_family:
            template_data['model_family_id'] = model_family.model_family_id
            template = EvaluationPromptTemplate(**template_data)
            self.db_session.add(template)
            self.db_session.commit()
        else:
            raise ValueError(f"Model family '{model_family_name}' does not exist.")

    def update_evaluation_prompt_template(self, template_id, updated_data):
        template = self.db_session.query(EvaluationPromptTemplate).get(template_id)

        if 'model_family' in updated_data:
            model_family_name = updated_data.pop('model_family')
            model_family = self.db_session.query(ModelFamily).filter_by(name=model_family_name).first()

            if model_family:
                updated_data['model_family_id'] = model_family.model_family_id
            else:
                raise ValueError(f"Model family '{model_family_name}' does not exist.")

        for key, value in updated_data.items():
            setattr(template, key, value)

        self.db_session.commit()

    def delete_evaluation_prompt_template(self, template_id):
        template = self.db_session.query(EvaluationPromptTemplate).get(template_id)
        self.db_session.delete(template)
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
