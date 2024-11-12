import asyncio
import time
import json
from statistics import mean
import sys
from handlers.llm_handler import BaseModelHandler
from models.llm_request_models import BaseLLMRequest
import random
import csv
import argparse

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

def percentile(data, percentile_rank):
    size = len(data)
    if size == 0:
        return None
    return sorted(data)[int(size * percentile_rank / 100)]

async def run_handler_test(handler_name, handler, prompts, num_requests, num_clients, task, results):
    results[handler_name] = []
    sem = asyncio.Semaphore(num_clients)
    tasks = []
    for _ in range(num_requests):
        prompt = random.choice(prompts)
        tasks.append(send_request(handler_name, handler, prompt, task, results[handler_name], sem))

    # Run tasks and measure total time per handler
    print(f"Running performance test for handler: {handler_name} (Model: {handler.model})")
    start_time = time.time()
    await asyncio.gather(*tasks)
    total_time = time.time() - start_time

    # Analyze results for this handler
    handler_results = results[handler_name]
    latencies = [r['elapsed_time'] for r in handler_results if r['success']]
    errors = [r for r in handler_results if not r['success']]
    total_requests = len(handler_results)
    successful_requests = len(latencies)
    error_rate = len(errors) / total_requests * 100 if total_requests > 0 else 0

    if latencies:
        p50 = percentile(latencies, 50)
        p90 = percentile(latencies, 90)
        p95 = percentile(latencies, 95)
        p99 = percentile(latencies, 99)
        avg_latency = mean(latencies)
    else:
        p50 = p90 = p95 = p99 = avg_latency = None

    throughput = successful_requests / total_time if total_time > 0 else 0

    print(f"\nHandler: {handler_name} (Model: {handler.model})")
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

async def performance_test():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Performance Test for LLM Handlers')
    parser.add_argument('--clients', type=int, default=50, help='Number of concurrent clients per handler')
    parser.add_argument('--requests', type=int, default=100, help='Total number of requests per handler')
    parser.add_argument('--csv', type=str, default='attribute_extraction_prompts.csv', help='CSV file containing prompts')
    parser.add_argument('--task', type=str, default='attribute_extraction', help='Task type for the handlers')
    args = parser.parse_args()

    num_clients = args.clients
    num_requests = args.requests
    csv_file = args.csv
    task = args.task

    # Load configurations
    with open('config.json', 'r') as f:
        provider_configs = json.load(f)
    handlers = {}
    for provider_config in provider_configs['providers']:
        provider_config_copy = provider_config.copy()
        name = provider_config_copy.pop('name')
        handlers[name] = BaseModelHandler(**provider_config_copy)

    # Load prompts from CSV
    prompts = []
    with open(csv_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prompts.append(row['prompt'])

    # Check if prompts were loaded successfully
    if not prompts:
        print(f"No prompts found in '{csv_file}'. Please provide a valid CSV file with prompts.")
        return

    # Prepare results dictionary
    results = {}

    # Create handler test tasks
    handler_test_tasks = []
    for handler_name, handler in handlers.items():
        handler_test_tasks.append(
            run_handler_test(handler_name, handler, prompts, num_requests, num_clients, task, results)
        )

    # Run all handler tests concurrently
    await asyncio.gather(*handler_test_tasks)

if __name__ == "__main__":
    asyncio.run(performance_test())
