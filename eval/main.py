import sys
import os
import traceback

from ui.db.database_handler import DatabaseHandler

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.join(base_dir, "../"))

from eval.eval_task_handlers.input_handler import InputHandler
from eval.eval_task_handlers.api_handler import APIHandler
from eval.eval_task_handlers.evaluator import Evaluator
from eval.eval_task_handlers.batch_processor import BatchProcessor
from eval.utils.helper_functions import prepare_item
from eval.config.constants import API_URL, TASK_MAPPING
from entrypoint.template_renderer import TemplateRenderer
from entrypoint.styling_guide_manager import StylingGuideManager
from handlers.llm_handler import BaseModelHandler
import argparse
import logging
import asyncio
from models.database import SessionLocal


# from dotenv import load_dotenv
#
# load_dotenv()

async def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run enrichment and evaluation script.")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file path.")
    parser.add_argument("--batch_size", type=int, default=100, help="Batch size for processing.")
    args = parser.parse_args()

    # Initialize the database session
    db_session = SessionLocal()
    db_handler = DatabaseHandler(db_path='/Users/n0s09lj/Workspace/item-setup-playground/results.db')
    # Initialize actors
    template_renderer = TemplateRenderer(db_session=db_session)
    styling_guide_manager = StylingGuideManager(db_session=db_session)

    # Initialize LLM handler
    provider_config_1 = {
        "name"           : "gpt-4o",
        "provider"       : "openai",
        "model"          : "gpt-4o",
        "family"         : "default",
        "temperature"    : 0.2,
        "version"        : "2024-02-01",
        "api_base"       : "https://wmtllmgateway.stage.walmart.com/wmtllmgateway/v1/openai",
        "required_fields": []
    }

    handler_1 = BaseModelHandler(**provider_config_1)

    provider_config_2 = {
        "name"           : "meta-llama/Llama-3.1-405B-Instruct-FP8",
        "provider"       : "elements_openai",
        "model"          : "meta-llama/Llama-3.1-405B-Instruct-FP8",
        "family"         : "llama",
        "temperature"    : 0.1,
        "version"        : "",
        "api_base"       : "https://llama-3-dot-1-405b-fp8-stage.element.glb.us.walmart.net/llama-3-dot-1-405b-fp8/v1/completions",
        "required_fields": []
    }
    # handler_2 = BaseModelHandler(**provider_config_2)

    provider_config_3 = {
        "name"           : "claude-3-haiku",
        "provider"       : "claude",
        "model"          : "claude-3-haiku",
        "version"        : "20240307",
        "api_base"       : "https://wmtllmgateway.stage.walmart.com/wmtllmgateway/v1/google-genai",
        "family"         : "default",
        "temperature"    : 0.2,
        "required_fields": []
    }
    handler_3 = BaseModelHandler(**provider_config_3)

    input_handler = InputHandler(args.input)
    api_handler = APIHandler(API_URL)
    evaluator_1 = Evaluator(db_session=db_session, template_renderer=template_renderer, styling_guide_manager=styling_guide_manager, handler=handler_1, evaluator_id="gpt4o")
    # evaluator_2 = Evaluator(db_session=db_session, template_renderer=template_renderer, styling_guide_manager=styling_guide_manager, handler=handler_2, evaluator_id="llama_405b")
    evaluator_3 = Evaluator(db_session=db_session, template_renderer=template_renderer, styling_guide_manager=styling_guide_manager, handler=handler_3, evaluator_id="claude-3.5-sonnet")

    # List of evaluators
    # evaluators = [evaluator_1, evaluator_2, evaluator_3]
    evaluators = [evaluator_1, evaluator_3]
    # evaluators = [evaluator_1]
    # evaluators = [evaluator_2]

    # Load input data
    df = input_handler.load_data()

    # Initialize the BatchProcessor
    batch_processor = BatchProcessor(batch_size=args.batch_size, db_handler=db_handler)

    # Process batches
    await batch_processor.process_batches(
        df, api_handler, evaluators, prepare_item, include_evaluation=True
    )

    logging.info("Batch processing completed.")


if __name__=="__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    asyncio.run(main())