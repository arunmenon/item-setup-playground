import asyncio
import csv
import time
import json
from statistics import mean
import sys
from handlers.llm_handler import BaseModelHandler
from models.llm_request_models import BaseLLMRequest
from datetime import datetime
import random

async def send_request(handler_name, handler, prompt, task, results, sem):
    async with sem:
        start_time = time.time()
        try:
            response = await handler.invoke(request=BaseLLMRequest(prompt=prompt), task=task)
            elapsed_time = time.time() - start_time
            results.append({
                "elapsed_time": elapsed_time,
                "success": True
            })
        except Exception as e:
            elapsed_time = time.time() - start_time
            results.append({
                "elapsed_time": elapsed_time,
                "success": False,
                "error": str(e)
            })

async def performance_test():
    # Load configurations
    with open('config.json', 'r') as f:
        provider_configs = json.load(f)
    handlers = {}
    for provider_config in provider_configs['providers']:
        provider_config_copy = provider_config.copy()
        name = provider_config_copy.pop('name')
        handlers[name] = BaseModelHandler(**provider_config_copy)

    # Test parameters
    num_clients = 5  # Number of concurrent users
    num_requests = 10  # Total number of requests per handler
    task = "attribute_extraction"

    # Load prompts from CSV
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'attribute_extraction_prompts.csv'
    prompts = []
    with open(csv_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prompts.append(row['prompt'])

    # Prepare results dictionary
    results = {handler_name: [] for handler_name in handlers.keys()}

    # Create tasks
    tasks = []
    for handler_name, handler in handlers.items():
        sem = asyncio.Semaphore(num_clients)
        for _ in range(num_requests):
            prompt = random.choice(prompts)
            tasks.append(send_request(handler_name, handler, prompt, task, results[handler_name], sem))

    # Run tasks
    start_time = time.time()
    await asyncio.gather(*tasks)
    total_time = time.time() - start_time

    # Analyze results
    for handler_name, handler_results in results.items():
        latencies = [r['elapsed_time'] for r in handler_results if r['success']]
        errors = [r for r in handler_results if not r['success']]
        total_requests = len(handler_results)
        successful_requests = len(latencies)
        error_rate = len(errors) / total_requests * 100

        if latencies:
            p50 = percentile(latencies, 50)
            p90 = percentile(latencies, 90)
            p95 = percentile(latencies, 95)
            p99 = percentile(latencies, 99)
            avg_latency = mean(latencies)
        else:
            p50 = p90 = p95 = p99 = avg_latency = None

        throughput = successful_requests / total_time

        print(f"Handler: {handler_name}")
        print(f"Total Requests: {total_requests}")
        print(f"Successful Requests: {successful_requests}")
        print(f"Error Rate: {error_rate:.2f}%")
        if avg_latency is not None:
            print(f"Average Latency: {avg_latency:.2f} seconds")
            print(f"P50 Latency: {p50:.2f} seconds")
            print(f"P90 Latency: {p90:.2f} seconds")
            print(f"P95 Latency: {p95:.2f} seconds")
            print(f"P99 Latency: {p99:.2f} seconds")
        else:
            print("No successful requests to calculate latency statistics.")
        print(f"Throughput: {throughput:.2f} requests/second")
        print("")

def percentile(data, percentile):
    size = len(data)
    return sorted(data)[int(size * percentile / 100)]

if __name__ == "__main__":
    asyncio.run(performance_test())
