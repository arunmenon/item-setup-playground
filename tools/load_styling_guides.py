import sys
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import Base, StylingGuide, GenerationPromptTemplate, GenerationTask, ModelFamily
from models.database import SessionLocal
import json
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
            product_type = product_type_dir  # The directory name is the product_type

            # Iterate over each file in the product type directory
            for filename in os.listdir(product_type_path):
                file_path = os.path.join(product_type_path, filename)

                if os.path.isfile(file_path) and filename.endswith('.txt'):
                    # The file name (without extension) is the task_name
                    task_name = os.path.splitext(filename)[0]

                    # Read the content of the file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Check if the record already exists
                    existing_guide = db_session.query(StylingGuide).filter_by(
                        product_type=product_type,
                        task_name=task_name,
                        version=1  # Assuming version 1 for initial load
                    ).first()

                    if existing_guide:
                        logger.info(f"Styling guide already exists for product_type='{product_type}', task_name='{task_name}', version=1. Skipping.")
                        continue

                    # Create a new StylingGuide object
                    new_guide = StylingGuide(
                        product_type=product_type,
                        task_name=task_name,
                        content=content,
                        version=1,
                        is_active=True
                    )

                    # Add to session
                    db_session.add(new_guide)
                    logger.info(f"Added styling guide for product_type='{product_type}', task_name='{task_name}'.")

    # Commit the session
    db_session.commit()
    logger.info("Styling guides have been successfully loaded into the database.")


def load_prompt_templates(base_dir, db_session):
    """
    Loads prompt templates from the file system into the database.

    Args:
        base_dir (str): The base directory containing prompt templates.
        db_session (Session): The SQLAlchemy database session.
    """
    # Query GenerationTasks and ModelFamilies to get the list of tasks and model families
    generation_tasks = db_session.query(GenerationTask).all()
    model_families = db_session.query(ModelFamily).all()

    task_configs = {task.task_name: task.task_id for task in generation_tasks}
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
                    # The file name (without extension) is used to infer task_name and version
                    task_name = os.path.splitext(filename)[0]

                    # Strip off the "_prompt" or "_eval" suffix to get the base task name
                    if "_prompt" in task_name:
                        base_task_name = task_name.replace("_prompt", "")
                    elif "_eval" in task_name:
                        base_task_name = task_name.replace("_eval", "")
                    else:
                        base_task_name = task_name

                    # Check if base_task_name is in task_configs from GenerationTask
                    if base_task_name in task_configs:
                        task_id = task_configs[base_task_name]
                        # Read the content of the file
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        placeholders = ""  # Update with actual placeholders if available

                        new_template = GenerationPromptTemplate(
                            task_id=task_id,
                            model_family_id=model_family_id,
                            template_text=content,
                            version=1,
                            placeholders=placeholders
                        )

                        db_session.add(new_template)
                        logger.info(f"Added generation prompt template: '{filename}' for task_id: {task_id}, model family: {model_family_dir}.")

    # Commit the session
    db_session.commit()
    logger.info("Prompt templates have been successfully loaded into the database.")


if __name__=='__main__':
    # Specify the base directory containing styling guides
    styling_guides_dir = os.path.abspath('styling_guides')  # Update this path if needed
    prompts_dir = os.path.abspath('prompts')  # Update this path if needed

    # Ensure the directory for the SQLite database exists
    database_path = os.path.abspath('/Users/n0s09lj/Workspace/item-setup-playground/results.db')
    if not os.path.isdir(os.path.dirname(database_path)):
        logger.error(f"Directory '{os.path.dirname(database_path)}' does not exist. Please create the directory or provide the correct path.")
        sys.exit(1)

    database_url = f'sqlite:///{database_path}'

    # Create the database and tables
    create_database_and_tables(database_url)

    # Create a new database session
    try:
        db_session = SessionLocal()
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        sys.exit(1)

    try:
        load_styling_guides(styling_guides_dir, db_session)
        load_prompt_templates(prompts_dir, db_session)
    except Exception as e:
        logger.error(f"An error occurred while loading data: {e}")
        db_session.rollback()
    finally:
        db_session.close()