import sys
import os
import logging
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database import Base, SessionLocal
from models.models import StylingGuide, GenerationPromptTemplate, EvaluationPromptTemplate, GenerationTask, \
    EvaluationTask, ModelFamily
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_database_and_tables(database_url):
    """
    Creates the database and tables.

    Args:
        database_url (str): The database URL.
    """
    try:
        # Create the engine
        engine = create_engine(database_url)

        # Create all tables in the database which are defined by Base's subclasses
        Base.metadata.create_all(bind=engine)
        logger.info("Database and tables created successfully.")
    except Exception as e:
        logger.error(f"Error occurred while creating database and tables: {e}")
        sys.exit(1)


def load_styling_guides(base_dir, db_session):
    """
    Loads styling guides from the file system into the database.

    Args:
        base_dir (str): The base directory containing styling guides.
        db_session (Session): The SQLAlchemy database session.
    """
    # Iterate over each product type directory
    for product_type_dir in os.listdir(base_dir):
        product_type_path = os.path.join(base_dir, product_type_dir)

        if os.path.isdir(product_type_path):
            product_type = product_type_dir

            # Iterate over each file in the product type directory
            for filename in os.listdir(product_type_path):
                file_path = os.path.join(product_type_path, filename)

                if os.path.isfile(file_path) and filename.endswith('.txt'):
                    task_name = os.path.splitext(filename)[0]

                    # Read the content of the file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    existing_guide = db_session.query(StylingGuide).filter_by(
                        product_type=product_type,
                        task_name=task_name,
                        version=1
                    ).first()

                    if existing_guide:
                        logger.info(f"Styling guide already exists for product_type='{product_type}', task_name='{task_name}', version=1. Skipping.")
                        continue

                    new_guide = StylingGuide(
                        product_type=product_type,
                        task_name=task_name,
                        content=content,
                        version=1,
                        is_active=True
                    )

                    db_session.add(new_guide)
                    logger.info(f"Added styling guide for product_type='{product_type}', task_name='{task_name}'.")

    db_session.commit()
    logger.info("Styling guides have been successfully loaded into the database.")


def extract_placeholders(template_text):
    # Improved regex to match placeholders, including those with variable spaces
    placeholders = re.findall(r"{\s*([a-zA-Z0-9_]+)\s*}", template_text)
    placeholders = list(set(placeholders))  # Remove duplicates
    placeholders_str = ', '.join(placeholders)
    return placeholders_str


def load_prompt_templates(base_dir, db_session, template_class, task_class, task_suffix):
    """
    Loads prompt templates from the file system into the database.

    Args:
        base_dir (str): The base directory containing prompt templates.
        db_session (Session): The SQLAlchemy database session.
        template_class: The SQLAlchemy model class for the prompt templates.
        task_class: The SQLAlchemy model class for the tasks.
        task_suffix (str): The suffix for the task files (e.g., '_prompt' or '_eval').
    """
    tasks = db_session.query(task_class).all()
    model_families = db_session.query(ModelFamily).all()

    task_configs = {task.task_name: task.task_id for task in tasks}
    model_families_map = {model_family.name: model_family.model_family_id for model_family in model_families}

    for model_family_dir in os.listdir(base_dir):
        model_family_path = os.path.join(base_dir, model_family_dir)

        if os.path.isdir(model_family_path):
            model_family_id = model_families_map.get(model_family_dir)
            if model_family_id is None:
                logger.warning(f"Unknown model family: {model_family_dir}. Skipping.")
                continue

            for filename in os.listdir(model_family_path):
                file_path = os.path.join(model_family_path, filename)

                if os.path.isfile(file_path) and filename.endswith('.jinja2'):
                    task_name = os.path.splitext(filename)[0].replace(task_suffix, "")

                    if task_name in task_configs:
                        task_id = task_configs[task_name]

                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        placeholders = extract_placeholders(content)

                        new_template = template_class(
                            task_id=task_id,
                            model_family_id=model_family_id,
                            template_text=content,
                            version=1,
                            placeholders=placeholders
                        )

                        db_session.add(new_template)
                        logger.info(f"Added {template_class.__name__}: '{filename}' for task_id: {task_id}, model family: {model_family_dir}.")

    db_session.commit()
    logger.info(f"{template_class.__name__} have been successfully loaded into the database.")


if __name__=='__main__':
    styling_guides_dir = os.path.abspath('styling_guides')
    prompts_dir = os.path.abspath('prompts')

    database_path = os.path.abspath('/Users/n0s09lj/Workspace/item-setup-playground/results.db')
    if not os.path.isdir(os.path.dirname(database_path)):
        logger.error(f"Directory '{os.path.dirname(database_path)}' does not exist. Please create the directory or provide the correct path.")
        sys.exit(1)

    database_url = f'sqlite:///{database_path}'

    create_database_and_tables(database_url)

    try:
        db_session = SessionLocal()
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        sys.exit(1)

    try:
        load_styling_guides(styling_guides_dir, db_session)
        load_prompt_templates(prompts_dir, db_session, GenerationPromptTemplate, GenerationTask, '_prompt')
        load_prompt_templates(prompts_dir, db_session, EvaluationPromptTemplate, EvaluationTask, '_eval')
    except Exception as e:
        logger.error(f"An error occurred while loading data: {e}")
        db_session.rollback()
    finally:
        db_session.close()