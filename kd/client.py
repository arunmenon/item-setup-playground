# example_usage.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from kd.scenario_params import ScenarioParams
from kd.instruction_dataset_creator import InstructionDatasetCreator

# Set up SQLAlchemy session for DB (assuming db contains evaluation_tasks etc.)
engine = create_engine('sqlite:///external_database.db')
SessionLocal = sessionmaker(bind=engine)
db_session = SessionLocal()

# Scenario: 
# project_id: "my_project"
# dataset_id: "my_dataset"
# generation_model: "gpt-4o"
# generation_tasks: ["title_enhancement"]
# evaluation_tasks: ["title_style_guide_compliance_check"]
# scenario_type: "all_eval_models" means we want all eval models to have scored this item well.
# min_score: 80.0 for quality_score
params = ScenarioParams(
    project_id="my_project",
    dataset_id="my_dataset",
    generation_model="gpt-4o",
    generation_tasks=["title_enhancement"],
    evaluation_tasks=["title_style_guide_compliance_check"],
    eval_task_metric=None,  # Will auto-derive from evaluation_task
    scenario_type="all_eval_models",
    eval_model=None,
    min_score=80.0,
    top_n=100
)

instruction_format = {
    "instruction_field": "instruction",
    "input_field": "input",
    "output_field": "output"
}

creator = InstructionDatasetCreator(
    db_session=db_session,
    scenario_params=params,
    instruction_format=instruction_format,
    gcs_bucket="my_finetune_bucket",
    gcs_output_path="finetune_data/dataset.jsonl",
    family_name=None
)

creator.run()
