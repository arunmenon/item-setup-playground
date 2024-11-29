# models/models.py

from sqlalchemy import (
    Column, Integer,Float, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Table
)
from sqlalchemy.orm import relationship
import json
from sqlalchemy.types import TypeDecorator

from datetime import datetime
from .database import Base

# JSON TypeDecorator for storing JSON data in TEXT fields
class JSONEncodedDict(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is None:
            return '{}'
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return {}
        return json.loads(value)
    
class ModelFamily(Base):
    __tablename__ = 'model_families'
    model_family_id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    generation_prompt_templates = relationship('GenerationPromptTemplate', back_populates='model_family')
    evaluation_prompt_templates = relationship('EvaluationPromptTemplate', back_populates='model_family')

class GenerationTask(Base):
    __tablename__ = 'generation_tasks'
    task_id = Column(Integer, primary_key=True)
    task_name = Column(String, nullable=False)
    description = Column(Text)
    prompt_templates = relationship('GenerationPromptTemplate', back_populates='generation_task', cascade='all, delete-orphan')
    
class EvaluationTask(Base):
    __tablename__ = 'evaluation_tasks'
    task_id = Column(Integer, primary_key=True)
    task_name = Column(String, nullable=False)
    description = Column(Text)
    prompt_templates = relationship('EvaluationPromptTemplate', back_populates='evaluation_task', cascade='all, delete-orphan')

class GenerationPromptTemplate(Base):
    __tablename__ = 'generation_prompt_templates'
    template_id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('generation_tasks.task_id'), nullable=False)
    model_family_id = Column(Integer, ForeignKey('model_families.model_family_id'), nullable=False)
    template_text = Column(Text, nullable=False)
    version = Column(Integer, nullable=False)
    generation_task = relationship('GenerationTask', back_populates='prompt_templates')
    model_family = relationship('ModelFamily', back_populates='generation_prompt_templates')

class EvaluationPromptTemplate(Base):
    __tablename__ = 'evaluation_prompt_templates'
    template_id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('evaluation_tasks.task_id'), nullable=False)
    model_family_id = Column(Integer, ForeignKey('model_families.model_family_id'), nullable=False)
    template_text = Column(Text, nullable=False)
    version = Column(Integer, nullable=False)
    evaluation_task = relationship('EvaluationTask', back_populates='prompt_templates')
    model_family = relationship('ModelFamily', back_populates='evaluation_prompt_templates')

    
class ProviderConfig(Base):
    __tablename__ = 'providers'

    provider_id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    provider_name = Column(String, nullable=False)  # e.g., 'openai'
    family = Column(String, nullable=False)         # e.g., 'gpt', 'llama'
    model = Column(String, nullable=False)
    max_tokens = Column(Integer, nullable=True)
    temperature = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class StylingGuide(Base):
    __tablename__ = 'styling_guides'

    styling_guide_id = Column(Integer, primary_key=True)
    product_type = Column(String, nullable=False)
    task_name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('product_type', 'task_name', 'version', name='_product_task_version_uc'),
    )


class TaskExecutionConfig(Base):
    __tablename__ = 'task_execution_config'

    config_id = Column(Integer, primary_key=True)
    default_tasks = Column(JSONEncodedDict, nullable=False)
    conditional_tasks = Column(JSONEncodedDict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

