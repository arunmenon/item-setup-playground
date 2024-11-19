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


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run enrichment and evaluation script.")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file path.")
    parser.add_argument("--batch_size", type=int, default=100, help="Batch size for processing.")
    args = parser.parse_args()

    # Initialize actors
    template_renderer = TemplateRenderer()
    styling_guide_manager = StylingGuideManager()

    # Initialize LLM handler
    provider_config_1 = {
        "name": "openai-gpt-4o-mini",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "temperature": 0.2,
    }
    handler_1 = BaseModelHandler(**provider_config_1)
    provider_config_2 = {
        "name": "openai-gpt-4o-mini",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "temperature": 0.2,
    }
    handler_2 = BaseModelHandler(**provider_config_2)


    input_handler = InputHandler(args.input)
    api_handler = APIHandler(API_URL)
    evaluator_1 = Evaluator(TASK_MAPPING, template_renderer, styling_guide_manager, handler_1,evaluator_id="gpt4_1")
    evaluator_2 = Evaluator(TASK_MAPPING, template_renderer, styling_guide_manager, handler_2,evaluator_id="gpt4_2")


    # Initialize the BatchProcessor
    batch_processor = BatchProcessor(args.batch_size)

    # List of evaluators
    evaluators = [evaluator_1, evaluator_2]

    # Load input data
    df = input_handler.load_data()

    # Process batches
    batch_processor.process_batches(
        df, api_handler, evaluators, prepare_item
    )

    logging.info("Batch processing completed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    main()
