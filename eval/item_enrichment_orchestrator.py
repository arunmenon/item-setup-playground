import pandas as pd
import requests
import asyncio
import logging
from tqdm import tqdm
from entrypoint.template_renderer import TemplateRenderer
from entrypoint.styling_guide_manager import StylingGuideManager
from handlers.llm_handler import BaseModelHandler
from models.llm_request_models import LLMRequest, BaseLLMRequest

# Configure logging
logging.basicConfig(level=logging.INFO)

API_URL = "http://localhost:5000/enrich-item"

# Load template renderer and styling guide manager
template_renderer = TemplateRenderer()
styling_guide_manager = StylingGuideManager()

# Assuming you have a configuration for your provider
provider_config = {
    "name": "openai-gpt-4o-mini",
    "provider": "openai",
    "model": "gpt-4o-mini",
    "temperature": 0.2,
}
handler = BaseModelHandler(**provider_config)

async def enrich_and_evaluate(input_file: str, output_file: str):
    # Load the input data
    df = pd.read_csv(input_file)

    results = []
    tasks = []

    # Set up tqdm progress bar for the number of items to process
    with tqdm(total=len(df), desc="Processing Items", unit="item") as progress_bar:
        for index, row in df.iterrows():
            tasks.append(process_item(row, progress_bar))

        # Run tasks concurrently
        all_results = await asyncio.gather(*tasks)

        # Flatten and determine winners
        all_results_flattened = [item for sublist in all_results for item in sublist if item]
        results_with_winners = determine_winner_model(all_results_flattened)

        # Save the results to the output file
        results_df = pd.DataFrame(results_with_winners)
        results_df.to_csv(output_file, index=False)
        logging.info(f"Enrichment and evaluation results saved to '{output_file}'")

async def process_item(row, progress_bar):
    # Create the request payload
    item_data = {
        'item_title': row['item_title'],
        'short_description': row['short_description'],
        'long_description': row['long_description'],
        'item_product_type': row['item_product_type'],
    }
    try:
        # Call the enrichment API
        response = requests.post(API_URL, json=item_data)
        if response.status_code != 200:
            logging.error(f"API call failed for item '{row['item_title']}': {response.text}")
            progress_bar.update(1)
            return None

        enrichment_results = response.json()

        # Proceed to evaluate each task type for this item
        evaluation_results = await evaluate_enrichment(item_data, enrichment_results)
        progress_bar.update(1)
        return evaluation_results

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to connect to enrichment API for item '{row['item_title']}': {e}")
        progress_bar.update(1)
        return None

async def evaluate_enrichment(item_data, enrichment_results):
    product_type = item_data['item_product_type']
    evaluation_tasks = ['title', 'short_description', 'long_description']
    evaluation_results = []

    task_mapping = {
        'title': 'title_enhancement',
        'short_description': 'short_description_enhancement',
        'long_description': 'long_description_enhancement'
    }

    for task in evaluation_tasks:
        # Retrieve the corresponding enhancement response for each model
        task_name = task_mapping[task]
        model_responses = enrichment_results.get(task_name, {})

        for model_name, model_data in model_responses.items():
            enriched_content_key = f"enhanced_{task}"  # e.g., 'enhanced_title'
            enriched_content = model_data.get('response', {}).get(enriched_content_key, None)

            if not enriched_content:
                logging.warning(f"No enriched content for model '{model_name}' and task '{task_name}' in item '{item_data['item_title']}'. Skipping evaluation.")
                continue

            # Retrieve the style guide
            try:
                styling_guide = styling_guide_manager.get_styling_guide(product_type, task_name)
            except ValueError as e:
                logging.error(f"Style guide not found for product type '{product_type}', task '{task_name}': {e}")
                continue

            # Prepare context for the template
            context = {
                'response_content': enriched_content,
                'styling_guide': styling_guide,
                'family': None  # Set if you have family-specific templates
            }

            # Render the evaluation prompt
            try:
                prompt = template_renderer.render_template(f'{task}_eval.jinja2', context)
            except Exception as e:
                logging.error(f"Error rendering template for task '{task}' in item '{item_data['item_title']}': {e}")
                continue

            # Invoke the LLM handler for evaluation
            try:
                response = await handler.invoke(
                    request=BaseLLMRequest(prompt=prompt, max_tokens=150),
                    task=f'{task}_eval'
                )
                response_content_llm = response.get('response', '')
                # Parse the JSON response
                parsed_response = parse_llm_response(response_content_llm)
                evaluation_results.append({
                    'item_title': item_data['item_title'],
                    'product_type': product_type,
                    'task': task,
                    'model_name': model_name,
                    'enriched_content': enriched_content,
                    'quality_score': parsed_response.get('quality_score'),
                    'reasoning': parsed_response.get('reasoning'),
                    'short_description': item_data['short_description'],
                    'long_description': item_data['long_description']
                })
            except Exception as e:
                logging.error(f"Error invoking LLM for evaluation of task '{task}' in item '{item_data['item_title']}': {e}")

    return evaluation_results

def determine_winner_model(all_results):
    # Group results by item and task, and then select the winner based on quality_score
    results_df = pd.DataFrame(all_results)

    winner_results = []
    grouped = results_df.groupby(['item_title', 'task'])

    for (item_title, task), group in grouped:
        # Find the model with the highest quality score
        best_row = group.loc[group['quality_score'].idxmax()]

        # Add winner information
        winner_results.append({
            'item_title': best_row['item_title'],
            'product_type': best_row['product_type'],
            'task': best_row['task'],
            'winner_model': best_row['model_name'],
            'winner_score': best_row['quality_score'],
            'winner_reasoning': best_row['reasoning'],
            'enriched_content': best_row['enriched_content'],
            'short_description': best_row['short_description'],
            'long_description': best_row['long_description']
        })

    return winner_results

def parse_llm_response(response_text: str) -> dict:
    import json
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing LLM response: {e}")
        return {}

if __name__ == '__main__':
    input_file = 'input_items.csv'  # Replace with your input file path
    output_file = 'output_enrichment_evaluation.csv'  # Replace with your desired output file path
    asyncio.run(enrich_and_evaluate(input_file, output_file))
