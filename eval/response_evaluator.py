import pandas as pd
import asyncio
import logging
from entrypoint.template_renderer import TemplateRenderer
from entrypoint.styling_guide_manager import StylingGuideManager
from handlers.llm_handler import BaseModelHandler
from models.llm_request_models import BaseLLMRequest

# Configure logging
logging.basicConfig(level=logging.INFO)

async def evaluate_responses(input_file: str, output_file: str):
    # Load the input data
    df = pd.read_csv(input_file)
    
    # Initialize necessary components
    template_renderer = TemplateRenderer()
    styling_guide_manager = StylingGuideManager()
    
    # Configure your provider as needed
    provider_config = {
        "name": "openai-gpt-4o-mini",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "temperature": 0.2,
    }
    handler = BaseModelHandler(**provider_config)
    
    tasks = []
    for index, row in df.iterrows():
        tasks.append(process_row(row, template_renderer, styling_guide_manager, handler))
    
    # Run tasks concurrently
    results = await asyncio.gather(*tasks)
    
    # Flatten results and save to output file
    all_results = [item for sublist in results for item in sublist if item is not None]
    results_df = pd.DataFrame(all_results)
    results_df.to_csv(output_file, index=False)
    logging.info(f"Evaluation results saved to '{output_file}'")

async def process_row(row, template_renderer, styling_guide_manager, handler):
    model_name = row['model_name']
    item = row['item']
    product_type = row['product_type']
    
    tasks = ['title', 'short_description', 'long_description']
    response_keys = {
        'title': 'title_response',
        'short_description': 'short_description_response',
        'long_description': 'long_description_response'
    }
    evaluation_results = []
    
    # Mapping evaluation tasks to enhancement tasks
    task_mapping = {
        'title_eval': 'title_enhancement',
        'short_description_eval': 'short_description_enhancement',
        'long_description_eval': 'long_description_enhancement'
    }
    
    for task in tasks:
        response_content = row.get(response_keys[task])
        if not response_content:
            logging.warning(f"No response content for task '{task}' in item '{item}'. Skipping.")
            continue
        
        # Evaluation task name (e.g., 'title_eval')
        eval_task_name = f"{task}_eval"
        
        # Map evaluation task to the corresponding enhancement task
        enhancement_task = task_mapping.get(eval_task_name, eval_task_name)
    
        # Retrieve the style guide using the enhancement task name
        try:
            styling_guide = styling_guide_manager.get_styling_guide(product_type, enhancement_task)
        except ValueError as e:
            logging.error(f"Style guide not found for product type '{product_type}', task '{enhancement_task}': {e}")
            continue  # Skip this task
        
        # Prepare context for the template
        context = {
            'response_content': response_content,
            'styling_guide': styling_guide,
            'family': None  # Set if you have family-specific templates
        }
        
        # Render the prompt
        try:
            prompt = template_renderer.render_template(f'{eval_task_name}.jinja2', context)
        except Exception as e:
            logging.error(f"Error rendering template for item '{item}', task '{eval_task_name}': {e}")
            continue  # Skip this task
        
        # Invoke the LLM handler
        try:
            response = await handler.invoke(
                request=BaseLLMRequest(prompt=prompt, max_tokens=150),
                task=eval_task_name
            )
            response_content_llm = response.get('response', '')
            # Parse the JSON response
            parsed_response = parse_llm_response(response_content_llm)
            evaluation_results.append({
                'model_name': model_name,
                'item': item,
                'product_type': product_type,
                'task': task,
                'response_content': response_content,
                'quality_score': parsed_response.get('quality_score'),
                'reasoning': parsed_response.get('reasoning')
            })
        except Exception as e:
            logging.error(f"Error invoking LLM for item '{item}', task '{eval_task_name}': {e}")
            continue  # Skip this task
    
    return evaluation_results

def parse_llm_response(response_text: str) -> dict:
    import json
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing LLM response: {e}")
        return {}

if __name__ == '__main__':
    input_file = 'input.csv'  # Replace with your input file path
    output_file = 'evaluation_output.csv'  # Replace with your desired output file path
    asyncio.run(evaluate_responses(input_file, output_file))
