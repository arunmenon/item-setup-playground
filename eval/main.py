import sys
import os
import traceback

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
    # provider_config = {
    #     "name"           : "gpt-4o",
    #     "provider"       : "openai",
    #     "model"          : "gpt-4o",
    #     "family"         : "default",
    #     "temperature"    : 0.2,
    #     "version"        : "2024-02-01",
    #     "api_base"       : "https://wmtllmgateway.prod.walmart.com/wmtllmgateway/v1/openai",
    #     "required_fields": []
    # }

    provider_config = {
        "name"           : "meta-llama/Llama-3.1-405B-Instruct-FP8",
        "provider"       : "elements_openai",
        "model"          : "meta-llama/Llama-3.1-405B-Instruct-FP8",
        "family"         : "llama",
        "temperature"    : 0.1,
        "api_base"       : "https://llama-3-dot-1-405b-fp8-stage.element.glb.us.walmart.net/llama-3-dot-1-405b-fp8/v1/completions",
        "required_fields": []
    }
    try:
        handler = BaseModelHandler(**provider_config)

        input_handler = InputHandler(args.input)
        api_handler = APIHandler(API_URL)
        evaluator = Evaluator(TASK_MAPPING, template_renderer, styling_guide_manager, handler)

        # Initialize the BatchProcessor
        batch_processor = BatchProcessor(args.batch_size)

        # Load input data
        df = input_handler.load_data()

        # Process batches
        # batch_processor.process_batches(
        #     df, api_handler, evaluator, prepare_item
        # )
        asyncio.run(batch_processor.process_batches(df, api_handler, evaluator, prepare_item))
        # asyncio.run(batch_processor.process_batches(df, api_handler, evaluator, prepare_item))
    except Exception as e:
        print (f"Error : {e}")
        print (f"Traceback : {traceback.print_exc()}")

    logging.info("Batch processing completed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    main()
