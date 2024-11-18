# main.py

import asyncio
import logging
from config import parse_args
from logger_config import setup_logging
from data_loader import load_sku_data
from api_client import fetch_model_responses_async
from response_processor import process_responses
from similarity_calculator import calculate_pairwise_similarity
from utils import save_to_csv

def main():
    # Setup logging
    setup_logging()
    logging.info("Starting the SKU processing script.")

    # Parse command-line arguments
    args = parse_args()

    # Load SKU data
    sku_data = load_sku_data(args.input_file)
    if not sku_data:
        logging.error("No SKU data loaded. Exiting.")
        return

    # Fetch model responses asynchronously
    responses = asyncio.run(fetch_model_responses_async(sku_data, 
                                                        args.api_endpoint,
                                                        max_concurrent_requests=args.max_concurrent_requests))
    if not responses:
        logging.error("No responses received from the API. Exiting.")
        return

    # Process responses
    processed_results, model_names = process_responses(responses)

    # Save model responses to CSV
    fieldnames = ['SKU', 'GTIN', 'Task'] + sorted(model_names)
    save_to_csv("model_responses", processed_results, fieldnames=fieldnames)

    # Calculate pairwise similarity
    all_similarity_scores = calculate_pairwise_similarity(processed_results)

    # Save similarity scores to CSV
    similarity_fieldnames = [
        "SKU", "GTIN", "Task", "Model_1", "Response_1", "Model_2", "Response_2", "Similarity_Score"
    ]
    save_to_csv("similarity_scores", all_similarity_scores, fieldnames=similarity_fieldnames)

    logging.info("SKU processing script completed successfully.")

if __name__ == "__main__":
    main()
