# main.py

import argparse
import logging
import asyncio
from relational_metadata_handler import RelationalMetadataHandler
from bigquery_input_handler import BigQueryInputHandler
from bigquery_store import BigQueryEvaluationStore
from handlers.llm_handler import BaseModelHandler
from entrypoint.template_renderer import TemplateRenderer
from entrypoint.styling_guide_manager import StylingGuideManager
from eval.eval_task_handlers.api_handler import APIHandler
from eval.eval_task_handlers.evaluator import Evaluator
from eval.eval_task_handlers.batch_processor import BatchProcessor
from eval.utils.helper_functions import prepare_item
from eval.config.constants import API_URL
from models.database import SessionLocal

async def main():
    parser = argparse.ArgumentParser(description="Run enrichment and evaluation from BigQuery with relational metadata.")
    parser.add_argument("--tenant_name", type=str, required=True, help="Tenant name.")
    parser.add_argument("--dataset_name", type=str, required=True, help="Dataset name.")
    parser.add_argument("--batch_size", type=int, default=100, help="Batch size.")
    parser.add_argument("--relational_db_url", type=str, required=True, help="DB URL for MySQL/Postgres/SQLite.")
    parser.add_argument("--project", type=str, default="my_project", help="GCP project.")
    parser.add_argument("--dataset", type=str, default="my_dataset", help="BigQuery dataset.")
    parser.add_argument("--task_input_table", type=str, default="task_input", help="task_input table name.")
    args = parser.parse_args()

    # Get dataset_id from relational DB
    metadata_handler = RelationalMetadataHandler(db_url=args.relational_db_url)
    dataset_id = metadata_handler.get_dataset_id(args.tenant_name, args.dataset_name)

    db_session = SessionLocal()
    template_renderer = TemplateRenderer(db_session=db_session)
    styling_guide_manager = StylingGuideManager(db_session=db_session)
    api_handler = APIHandler(API_URL)

    provider_config_1 = {
        "name": "gpt-4o",
        "provider": "openai",
        "model": "gpt-4o",
        "family": "default",
        "temperature": 0.2,
        "version": "2024-02-01",
        "api_base": "https://wmtllmgateway.stage.walmart.com/wmtllmgateway/v1/openai",
        "required_fields": []
    }

    handler_1 = BaseModelHandler(**provider_config_1)

    provider_config_3 = {
        "name": "claude-3-haiku",
        "provider": "claude",
        "model": "claude-3-haiku",
        "version": "20240307",
        "api_base": "https://wmtllmgateway.stage.walmart.com/wmtllmgateway/v1/google-genai",
        "family": "default",
        "temperature": 0.2,
        "required_fields": []
    }
    handler_3 = BaseModelHandler(**provider_config_3)

    evaluator_1 = Evaluator(db_session, template_renderer, styling_guide_manager, handler_1, evaluator_id="gpt4o")
    evaluator_3 = Evaluator(db_session, template_renderer, styling_guide_manager, handler_3, evaluator_id="claude-3.5-sonnet")
    evaluators = [evaluator_1, evaluator_3]

    input_handler = BigQueryInputHandler(
        project=args.project,
        dataset=args.dataset,
        table=args.task_input_table,
        dataset_id=dataset_id,
        batch_size=args.batch_size
    )

    store = BigQueryEvaluationStore(
        evaluation_table=f"{args.project}.{args.dataset}.evaluation_results",
        aggregated_table=f"{args.project}.{args.dataset}.aggregated_evaluations"
    )

    batch_processor = BatchProcessor(batch_size=args.batch_size, store=store)

    while True:
        df = input_handler.load_next_batch()
        if df is None:
            break
        await batch_processor.process_batches(df, api_handler, evaluators, prepare_item, include_evaluation=True)

    logging.info("Batch processing completed.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    asyncio.run(main())
