# load_config.py

import os
import sys
import json
import logging
from datetime import datetime
from sqlalchemy import create_engine, Text, TypeDecorator
from sqlalchemy.orm import sessionmaker

# Import models from models module
from models.models import Base, ModelFamily, ProviderConfig, TaskExecutionConfig, GenerationTask, EvaluationTask

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JSONEncodedDict(TypeDecorator):
    """
    Helper class for SQLAlchemy to handle JSON encoded dictionaries.
    """
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is None:
            return '{}'
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if not value:
            return {}
        return json.loads(value)


def ensure_tables_exist(engine):
    """
    Ensures that the necessary tables are created.
    Args:
        engine: SQLAlchemy engine object.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Ensured that all tables exist.")
    except Exception as e:
        logger.error(f"Error occurred while ensuring tables exist: {e}")
        sys.exit(1)


def save_or_update_evaluation_task(db_session, task_name, description):
    """
    Saves or updates evaluation tasks into the database.
    Args:
        db_session (session): The SQLAlchemy database session.
        task_name (str): The name of the task.
        description (str): The description of the task.
    """
    try:
        existing_task = db_session.query(EvaluationTask).filter_by(task_name=task_name).first()
        if existing_task:
            logger.info(f"Evaluation task '{task_name}' already exists in the database.")
        else:
            new_task = EvaluationTask(task_name=task_name, description=description)
            db_session.add(new_task)
            db_session.commit()
            logger.info(f"Evaluation task '{task_name}' saved to the database.")
    except Exception as e:
        logger.error(f"Error occurred while saving/updating evaluation task: {e}")
        db_session.rollback()


def save_or_update_generation_task(db_session, task_name, max_tokens, output_format):
    """
    Saves or updates generation tasks into the database.
    Args:
        db_session (session): The SQLAlchemy database session.
        task_name (str): The name of the task.
        max_tokens (int): The max tokens for the task.
        output_format (str): The output format for the task.
    """
    try:
        existing_task = db_session.query(GenerationTask).filter_by(task_name=task_name).first()
        if existing_task:
            # Update the existing task
            existing_task.max_tokens = max_tokens
            existing_task.output_format = output_format
            existing_task.updated_at = datetime.utcnow()
            db_session.commit()
            logger.info(f"Generation task '{task_name}' updated in the database.")
        else:
            # Create a new task
            new_task = GenerationTask(
                task_name=task_name,
                description=f"Task description for {task_name}",
                max_tokens=max_tokens,
                output_format=output_format
            )
            db_session.add(new_task)
            db_session.commit()
            logger.info(f"Generation task '{task_name}' saved to the database.")
    except Exception as e:
        logger.error(f"Error occurred while saving/updating generation task: {e}")
        db_session.rollback()


def save_or_update_provider(db_session, provider_data):
    """
    Saves or updates providers into the database.
    Args:
        db_session (session): The SQLAlchemy database session.
        provider_data (dict): A dictionary containing provider information.
    """
    try:
        # Map JSON fields to ProviderConfig fields
        mapped_provider_data = {
            'name'         : provider_data['name'],
            'provider_name': provider_data['provider'],
            'family'       : provider_data['family'],
            'model'        : provider_data['model'],
            'version' : provider_data.get('version', ''),
            'api_base': provider_data.get('api_base', ''),
            'temperature'  : provider_data['temperature'],
            'created_at'   : datetime.utcnow(),
            'updated_at'   : datetime.utcnow(),
            'is_active'    : True  # assuming we want the provider to be active by default
        }

        existing_provider = db_session.query(ProviderConfig).filter_by(name=mapped_provider_data['name']).first()
        if existing_provider:
            # Update the existing provider
            for key, value in mapped_provider_data.items():
                setattr(existing_provider, key, value)
            db_session.commit()
            logger.info(f"Provider '{mapped_provider_data['name']}' updated in the database.")
        else:
            # Create a new provider
            new_provider = ProviderConfig(**mapped_provider_data)
            db_session.add(new_provider)
            db_session.commit()
            logger.info(f"Provider '{mapped_provider_data['name']}' saved to the database.")
    except Exception as e:
        logger.error(f"Error occurred while saving/updating provider: {e}")
        db_session.rollback()


def save_or_update_model_family(db_session, family_name):
    """
    Saves or updates model families into the database.
    Args:
        db_session (session): The SQLAlchemy database session.
        family_name (str): The name of the model family.
    """
    try:
        existing_family = db_session.query(ModelFamily).filter_by(name=family_name).first()
        if existing_family:
            # Already exists, no need to update
            logger.info(f"Model family '{family_name}' already exists in the database.")
        else:
            # Create a new model family
            new_family = ModelFamily(name=family_name)
            db_session.add(new_family)
            db_session.commit()
            logger.info(f"Model family '{family_name}' saved to the database.")
    except Exception as e:
        logger.error(f"Error occurred while saving/updating model family: {e}")
        db_session.rollback()


def save_or_update_task_execution_config(db_session, default_tasks, conditional_tasks):
    """
    Saves or updates the task execution configuration into the database.
    Args:
        db_session (session): The SQLAlchemy database session.
        default_tasks (list): A list of default tasks.
        conditional_tasks (dict): A dictionary of conditional tasks.
    """
    try:
        existing_config = db_session.query(TaskExecutionConfig).order_by(TaskExecutionConfig.config_id.desc()).first()
        if existing_config:
            # Update the existing configuration
            existing_config.default_tasks = default_tasks
            existing_config.conditional_tasks = conditional_tasks
            db_session.commit()
            logger.info("Task execution configuration updated in the database.")
        else:
            # Create a new configuration
            new_config = TaskExecutionConfig(
                default_tasks=default_tasks,
                conditional_tasks=conditional_tasks
            )
            db_session.add(new_config)
            db_session.commit()
            logger.info("Task execution configuration saved to the database.")
    except Exception as e:
        logger.error(f"Error occurred while saving/updating task execution configuration: {e}")
        db_session.rollback()


def load_task_execution_config(db_session):
    """
    Loads the most recent task execution configuration from the database.
    Args:
        db_session (session): The SQLAlchemy database session.
    Returns:
        dict: A dictionary with the task execution configuration or raises an error if not found.
    """
    try:
        config = db_session.query(TaskExecutionConfig).order_by(TaskExecutionConfig.config_id.desc()).first()
        if config:
            task_execution = {
                'default_tasks'    : config.default_tasks,
                'conditional_tasks': config.conditional_tasks
            }
            logger.info("Loaded task execution configuration.")
            return task_execution
        else:
            logger.error("No task execution configuration found in the database.")
            raise ValueError("No task execution configuration found in the database.")
    except Exception as e:
        logger.error(f"Error occurred while loading task execution configuration: {e}")
        raise


def main():
    # Paths
    working_dir = os.getcwd()
    database_path = os.path.join(working_dir, 'results.db')
    config_path = os.path.join(working_dir, 'providers', 'config.json')

    # Ensure the directory for the SQLite database exists
    if not os.path.isdir(os.path.dirname(database_path)):
        logger.error(f"Directory '{os.path.dirname(database_path)}' does not exist. Please create the directory or provide the correct path.")
        sys.exit(1)

    database_url = f'sqlite:///{database_path}'

    # Create the database and tables
    engine = create_engine(database_url)
    ensure_tables_exist(engine)

    # Create a new database session
    try:
        Session = sessionmaker(bind=engine)
        db_session = Session()
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        sys.exit(1)

    try:
        # Load the configuration from the JSON file
        with open(config_path, 'r') as file:
            config = json.load(file)

        # Save or update task execution configuration into the database
        task_execution_config = config.get('task_execution', {})
        save_or_update_task_execution_config(db_session,
            task_execution_config.get('default_tasks', []),
            task_execution_config.get('conditional_tasks', {}))

        # Save or update model families into the database
        providers = config.get('providers', [])
        for provider in providers:
            if "family" in provider:
                save_or_update_model_family(db_session, provider['family'])
            save_or_update_provider(db_session, provider)

        # Save or update generation tasks from default tasks in task execution config
        default_tasks = task_execution_config.get('default_tasks', [])
        tasks_config = config.get('tasks', {})
        for task_name in default_tasks:
            task_details = tasks_config.get(task_name, {})
            max_tokens = task_details.get('max_tokens', 0)
            output_format = task_details.get('output_format', 'text')
            save_or_update_generation_task(db_session, task_name, max_tokens, output_format)

        # Now load the tasks from the database
        loaded_task_execution = load_task_execution_config(db_session)
        print(f"Task Execution Config: {loaded_task_execution}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        db_session.rollback()
    finally:
        db_session.close()


if __name__=='__main__':
    main()