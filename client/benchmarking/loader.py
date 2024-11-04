import openai
import time
from openai import OpenAI
from tqdm import tqdm
import psutil  # For system memory usage
import json
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import numpy as np

# Function to read configuration from a text file
def read_config(file_path):
    config = {}
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):  # Ignore empty lines and comments
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
    return config

# Function to load prompts based on model family
def load_prompts(model_family):
    prompt_file = f"{model_family}_prompts.txt"
    prompts = []
    try:
        with open(prompt_file, 'r') as file:
            for line in file:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    _, prompt = line.split('=', 1)
                    prompts.append(prompt.strip())
    except FileNotFoundError:
        print(f"Prompt file {prompt_file} not found.")
    return prompts

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Run benchmark script with specified config file.")
parser.add_argument('--config', type=str, required=True, help="Path to the config file (e.g., config_mistral.txt)")
parser.add_argument('--total_users', type=int, required=True, help="Total number of user sessions to simulate.")
parser.add_argument('--active_users', type=int, required=True, help="Number of active concurrent users making requests.")
parser.add_argument('--delay', type=float, default=0.5, help="Delay in seconds between each user request (default: 0.5 seconds)")
args = parser.parse_args()

# Load configuration
config = read_config(args.config)

# Retrieve settings
model_family = config.get('model_family')
model_name = config.get('model_name')
max_tokens = int(config.get('max_tokens', 50))  # Default to 50 if not specified

# Load prompts based on model family
prompts = load_prompts(model_family)

# Configure OpenAI to use the local server
base_url = "http://localhost:8000/v1"
openai.api_key = "sk-llama"  # Placeholder API key

def get_completion(prompt, model, max_tokens, client):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        content = response.choices[0].message.content
        tokens_generated = len(content.split())  # Estimate tokens by word count
        return content, tokens_generated
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, 0

def simulate_user_session(session_id, prompts, model_name, max_tokens, delay):
    client = OpenAI(base_url=base_url)
    session_results = []

    # Progress bar for each session
    with tqdm(total=len(prompts), desc=f"Session {session_id}", position=session_id + 1) as pbar:
        for prompt in prompts:
            time.sleep(delay)  # Simulate delay between requests for each user
            start_time = time.time()

            # Capture memory usage before request
            memory_before = psutil.virtual_memory().used / (1024 ** 2)  # in MB

            # Generate response
            completion, tokens_generated = get_completion(prompt, model=model_name, max_tokens=max_tokens, client=client)

            # Capture memory usage after request
            memory_after = psutil.virtual_memory().used / (1024 ** 2)  # in MB
            memory_used = memory_after - memory_before

            # Capture elapsed time
            end_time = time.time()
            elapsed_time = end_time - start_time

            # Calculate throughput (tokens per second)
            throughput = tokens_generated / elapsed_time if elapsed_time > 0 else 0

            # Store results for each prompt in this user session
            session_results.append({
                "session_id": session_id,
                "prompt": prompt,
                "completion": completion,
                "response_time_seconds": elapsed_time,
                "tokens_generated": tokens_generated,
                "throughput_tokens_per_second": throughput,
                "memory_used_mb": memory_used
            })
            
            # Update session progress
            pbar.update(1)

    return session_results

# Main function to execute benchmark with multiple users
def run_benchmark():
    benchmark_results = []

    with ThreadPoolExecutor(max_workers=args.active_users) as executor:
        futures = [
            executor.submit(simulate_user_session, i, prompts, model_name, max_tokens, args.delay)
            for i in range(args.total_users)
        ]

        for future in tqdm(as_completed(futures), total=args.total_users, desc="Processing User Sessions"):
            benchmark_results.extend(future.result())

    # Calculate and display latency percentiles
    latencies = [result['response_time_seconds'] for result in benchmark_results]
    latency_50th = np.percentile(latencies, 50)
    latency_90th = np.percentile(latencies, 90)
    latency_95th = np.percentile(latencies, 95)
    latency_99th = np.percentile(latencies, 99)
    
    print(f"50th percentile latency: {latency_50th} seconds")
    print(f"90th percentile latency: {latency_90th} seconds")
    print(f"95th percentile latency: {latency_95th} seconds")
    print(f"99th percentile latency: {latency_99th} seconds")

    # Generate timestamped output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"benchmark_results_{model_name}_{timestamp}.json"

    # Save results to JSON file for further analysis
    with open(output_filename, "w") as outfile:
        json.dump(benchmark_results, outfile, indent=4)

    print(f"Results saved to {output_filename}")

if __name__ == "__main__":
    run_benchmark()
