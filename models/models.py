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

class TaskConfig(Base):
    __tablename__ = 'tasks'

    task_id = Column(Integer, primary_key=True)
    task_name = Column(String, unique=True, nullable=False)
    max_tokens = Column(Integer, nullable=False)
    output_format = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class TaskExecutionConfig(Base):
    __tablename__ = 'task_execution_config'

    config_id = Column(Integer, primary_key=True)
    default_tasks = Column(JSONEncodedDict, nullable=False)
    conditional_tasks = Column(JSONEncodedDict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
        

class Template(Base):
    __tablename__ = 'templates'

    template_id = Column(Integer, primary_key=True)
    template_name = Column(String, nullable=False)
    template_type = Column(String, nullable=False)  # 'base' or 'model'
    parent_template_id = Column(Integer, ForeignKey('templates.template_id'), nullable=True)
    model_family = Column(String, nullable=True)
    task_name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    parent_template = relationship("Template", remote_side=[template_id], backref="child_templates")

    placeholders = relationship("Placeholder", secondary='template_placeholders', back_populates="templates")

    __table_args__ = (
        UniqueConstraint('template_name', 'version', name='_template_name_version_uc'),
        CheckConstraint("template_type IN ('base', 'model')", name='check_template_type')
    )

class Placeholder(Base):
    __tablename__ = 'placeholders'

    placeholder_id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    data_type = Column(String, nullable=False)
    default_value = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    templates = relationship("Template", secondary='template_placeholders', back_populates="placeholders")

template_placeholders = Table('template_placeholders', Base.metadata,
    Column('template_id', Integer, ForeignKey('templates.template_id'), primary_key=True),
    Column('placeholder_id', Integer, ForeignKey('placeholders.placeholder_id'), primary_key=True)
)
