import openai
import time
from openai import OpenAI
from tqdm import tqdm
import psutil  # For system memory usage
import json
import argparse
from datetime import datetime
import concurrent.futures
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

# Function to get the completion and calculate latency excluding delay
def get_completion(prompt, model, max_tokens, client):
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        content = response.choices[0].message.content
        tokens_generated = len(content.split())  # Estimate tokens by word count
    except Exception as e:
        print(f"An error occurred: {e}")
        content = None
        tokens_generated = 0
    elapsed_time = time.time() - start_time
    return content, tokens_generated, elapsed_time

# Function to simulate sessions
def simulate_session(session_id, prompts, model_name, max_tokens, delay, results, client):
    session_latencies = []
    for prompt in tqdm(prompts, desc=f"Session {session_id}"):
        completion, tokens_generated, elapsed_time = get_completion(prompt, model_name, max_tokens, client)
        session_latencies.append(elapsed_time)  # Log latency without delay
        results.append({
            "session_id": session_id,
            "prompt": prompt,
            "completion": completion,
            "response_time_seconds": elapsed_time,
            "tokens_generated": tokens_generated,
        })
        time.sleep(delay)  # Introduce delay after logging response time

    return session_latencies

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Run benchmark script with specified config file.")
parser.add_argument('--config', type=str, required=True, help="Path to the config file (e.g., config_mistral.txt)")
parser.add_argument('--total_users', type=int, required=True, help="Total number of users to simulate")
parser.add_argument('--active_users', type=int, required=True, help="Number of concurrent active users")
parser.add_argument('--delay', type=int, default=0, help="Delay between requests in seconds")
args = parser.parse_args()

# Load configuration
config = read_config(args.config)
model_family = config.get('model_family')
model_name = config.get('model_name')
max_tokens = int(config.get('max_tokens', 50))  # Default to 50 if not specified
prompts = load_prompts(model_family)

# Configure OpenAI to use the local server
base_url = "http://localhost:8000/v1"
openai.api_key = "sk-llama"  # Placeholder API key
client = OpenAI(base_url=base_url)

# Results to store per session
benchmark_results = []
latency_data = []

# Run sessions concurrently
with concurrent.futures.ThreadPoolExecutor(max_workers=args.active_users) as executor:
    futures = []
    for session_id in range(args.total_users):
        futures.append(
            executor.submit(
                simulate_session, session_id, prompts, model_name, max_tokens, args.delay, benchmark_results, client
            )
        )
    # Collect latencies from each session
    for future in concurrent.futures.as_completed(futures):
        latency_data.extend(future.result())

# Calculate percentiles for latency
latency_50th = np.percentile(latency_data, 50)
latency_90th = np.percentile(latency_data, 90)
latency_95th = np.percentile(latency_data, 95)
latency_99th = np.percentile(latency_data, 99)

# Display percentiles
print(f"50th percentile latency: {latency_50th:.2f} seconds")
print(f"90th percentile latency: {latency_90th:.2f} seconds")
print(f"95th percentile latency: {latency_95th:.2f} seconds")
print(f"99th percentile latency: {latency_99th:.2f} seconds")

# Generate timestamped output filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_filename = f"benchmark_results_{model_name}_{timestamp}.json"

# Save results to JSON file
with open(output_filename, "w") as outfile:
    json.dump(benchmark_results, outfile, indent=4)

print(f"Results saved to {output_filename}")
