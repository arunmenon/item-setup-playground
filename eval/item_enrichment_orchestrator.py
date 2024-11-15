import pandas as pd
import requests
import asyncio
import logging
from tqdm import tqdm
from entrypoint.template_renderer import TemplateRenderer
from entrypoint.styling_guide_manager import StylingGuideManager
from handlers.llm_handler import BaseModelHandler
from models.llm_request_models import LLMRequest, BaseLLMRequest
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)

API_URL = "http://localhost:5000/enrich-item"

# Load template renderer and styling guide manager
template_renderer = TemplateRenderer()
styling_guide_manager = StylingGuideManager()

# Provider configuration
provider_config = {
    "name": "openai-gpt-4o-mini",
    "provider": "openai",
    "model": "gpt-4o-mini",
    "temperature": 0.2,
}
handler = BaseModelHandler(**provider_config)

TASK_MAPPING = {
    'title': 'title_enhancement',
    'short_description': 'short_description_enhancement',
    'long_description': 'long_description_enhancement'
}


async def enrich_and_evaluate(input_file: str, output_file: str):
    # Load input data
    df = pd.read_csv(input_file)
    tasks = [process_item(row) for _, row in df.iterrows()]

    # Run tasks concurrently
    with tqdm(total=len(df), desc="Processing Items", unit="item") as progress_bar:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        progress_bar.update(len(results))

    # Determine winners and save results
    all_results = [item for sublist in results if sublist for item in sublist]
    winners = determine_winner_model(all_results)
    results_df = pd.DataFrame(winners)
    results_df.to_csv(output_file, index=False)
    logging.info(f"Results saved to '{output_file}'")


async def process_item(row: pd.Series) -> List[Dict[str, Any]]:
    item_data = prepare_item(row)
    try:
        enrichment_results = call_api(item_data)
        if not enrichment_results:
            return None
        return await evaluate_item(item_data, enrichment_results)
    except Exception as e:
        logging.error(f"Error processing item '{row['item_id']}': {e}")
        return None


def call_api(item_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        response = requests.post(API_URL, json=item_data)
        if response.status_code == 200:
            return response.json()
        logging.error(f"API failed for item '{item_data['item_id']}': {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"API connection failed for item '{item_data['item_id']}': {e}")
    return {}


def prepare_item(row: pd.Series) -> Dict[str, Any]:
    return {
        'item_id': row['item_id'],
        'item_title': row['item_title'],
        'short_description': row['short_description'],
        'long_description': row['long_description'],
        'item_product_type': row['item_product_type'],
    }


async def evaluate_item(item_data: Dict[str, Any], enrichment_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    evaluation_results = []
    product_type = item_data['item_product_type']

    for task, task_name in TASK_MAPPING.items():
        model_responses = enrichment_results.get(task_name, {})
        for model_name, model_data in model_responses.items():
            enriched_content = model_data.get('response', {}).get(f"enhanced_{task}")
            if not enriched_content:
                logging.warning(f"No enriched content for task '{task_name}' in item '{item_data['item_id']}'.")
                continue
            evaluation_results.append(
                await evaluate_task(item_data, product_type, task, model_name, enriched_content)
            )
    return [result for result in evaluation_results if result]


async def evaluate_task(item_data, product_type, task, model_name, enriched_content):
    try:
        styling_guide = styling_guide_manager.get_styling_guide(product_type, TASK_MAPPING[task])
        context = {'response_content': enriched_content, 'styling_guide': styling_guide}
        prompt = template_renderer.render_template(f'{task}_eval.jinja2', context)

        response = await handler.invoke(
            request=BaseLLMRequest(prompt=prompt, max_tokens=150), task=f'{task}_eval'
        )
        parsed_response = parse_llm_response(response.get('response', ''))
        return generate_eval_response(item_data, product_type, task, model_name, enriched_content, parsed_response)
    except Exception as e:
        logging.error(f"Error evaluating task '{task}' for item '{item_data['item_id']}': {e}")
        return None


def generate_eval_response(item_data, product_type, task, model_name, enriched_content, parsed_response):
    # Map task to its corresponding original field in item_data
    original_field_mapping = {
        'title': 'item_title',
        'short_description': 'short_description',
        'long_description': 'long_description',
    }

    # Base response structure
    response = {
        'item_id': item_data['item_id'],
        'item_title': item_data['item_title'],
        'product_type': product_type,
        'task': task,
        'model_name': model_name,
        'enriched_content': enriched_content,
        'quality_score': parsed_response.get('quality_score'),
        'reasoning': parsed_response.get('reasoning'),
    }

    # Add original field dynamically if it exists for the task
    original_field = original_field_mapping.get(task)
    if original_field:
        response[f'original_{task}'] = item_data.get(original_field)

    return response


def determine_winner_model(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results_df = pd.DataFrame(results)
    winner_results = []

    for (item_id, task), group in results_df.groupby(['item_id', 'task']):
        group = group.dropna(subset=['quality_score'])
        if group.empty:
            logging.warning(f"No valid scores for item '{item_id}' and task '{task}'.")
            continue
        best_row = group.loc[group['quality_score'].idxmax()]
        winner_results.append({
            **best_row.to_dict(),
            'winner_model': best_row['model_name'],
            'winner_score': best_row['quality_score']
        })
    return winner_results


def parse_llm_response(response_text: str) -> dict:
    try:
        import json
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse LLM response: {e}")
        return {}


if __name__ == '__main__':
    input_file = 'input_items.csv'
    output_file = 'output_enrichment_evaluation.csv'
    asyncio.run(enrich_and_evaluate(input_file, output_file))
