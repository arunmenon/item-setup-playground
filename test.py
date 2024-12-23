import asyncio
from handlers.llm_handler import BaseModelHandler
from models.llm_request_models import BaseLLMRequest
import csv
import time
import json
from datetime import datetime
import sys

async def process_prompt_task_pair(prompt, task, handlers):
    request = BaseLLMRequest(prompt=prompt)
    results = []

    # For recording elapsed time
    tasks = []
    for handler_name, handler in handlers.items():
        tasks.append(invoke_handler(handler_name, handler, request, task))

    # Wait for all handlers to finish for this prompt-task pair
    handler_results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in handler_results:
        results.append(result)

    return results

async def invoke_handler(handler_name, handler, request, task):
    start_time = time.time()
    try:
        response = await handler.invoke(request=request, task=task)
        elapsed_time = time.time() - start_time
        result = {
            "handler_name": handler_name,
            "provider": handler.provider_name,
            "model": handler.model,
            "prompt": request.prompt,
            "task": task,
            "response": response['response'],
            "elapsed_time": elapsed_time
        }
        print(f"{handler_name} ({handler.provider_name}, model: {handler.model}) response for prompt '{request.prompt}':\n{response['response']}\nElapsed time: {elapsed_time:.2f} seconds\n")
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"Error during {handler_name} invocation for prompt '{request.prompt}': {str(e)}\nElapsed time: {elapsed_time:.2f} seconds\n")
        result = {
            "handler_name": handler_name,
            "provider": handler.provider_name,
            "model": handler.model,
            "prompt": request.prompt,
            "task": task,
            "error": str(e),
            "elapsed_time": elapsed_time
        }
    return result

async def test_providers_with_csv():
    # Get CSV file name from command-line argument or use default
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'attribute_extraction_prompts.csv'
    prompts_tasks = []
    with open(csv_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prompts_tasks.append((row['prompt'], row['task']))

    # Load provider configurations
    with open('config.json', 'r') as f:
        provider_configs = json.load(f)
    handlers = {}
    for provider_config in provider_configs['providers']:
        provider_config_copy = provider_config.copy()
        name = provider_config_copy.pop('name')
        handlers[name] = BaseModelHandler(**provider_config_copy)    

    all_results = []

    # Loop over prompt-task pairs
    for prompt, task in prompts_tasks:
        print(f"Processing prompt: '{prompt}' with task: '{task}'\n")
        # Process the prompt-task pair
        results = await process_prompt_task_pair(prompt, task, handlers)
        all_results.extend(results)

    # Generate a timestamped filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f'responses_{timestamp}.json'

    # Persist the results to the JSON file with the timestamped filename
    with open(output_filename, 'w') as f:
        json.dump(all_results, f, indent=4)

    print(f"Responses have been saved to '{output_filename}'")

# Run the test if executed as a script
if __name__ == "__main__":
    asyncio.run(test_providers_with_csv())
