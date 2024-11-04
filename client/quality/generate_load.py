import pandas as pd
import requests
import json
import csv
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import os
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    filename='make_requests.log',
    level=logging.DEBUG,  # Changed to DEBUG to capture detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Mapping of desired output columns to API response tasks
COLUMN_TASK_MAPPING = {
    'enhanced_title': 'title_enhancement',
    'enhanced_short_description': 'short_description_enhancement',
    'enhanced_long_description': 'long_description_enhancement',
    'extracted_attributes': 'attribute_extraction',
    'visual_attributes': 'vision_attribute_extraction'
}

def parse_arguments():
    parser = argparse.ArgumentParser(description='Make API requests to enrich product items.')
    parser.add_argument('--input', type=str, required=True, help='Path to input CSV file containing product items.')
    parser.add_argument('--output', type=str, required=True, help='Base name for output CSV file to save API responses.')
    parser.add_argument('--columns', type=str, required=True,
                        help='Comma-separated list of desired output columns (e.g., enhanced_title).')
    parser.add_argument('--api_url', type=str, default='http://localhost:5000/enrich-item',
                        help='API endpoint URL. Default is http://localhost:5000/enrich-item')
    parser.add_argument('--max_workers', type=int, default=40,
                        help='Maximum number of concurrent threads. Default is 40.')
    return parser.parse_args()

def load_input_csv(input_csv_path):
    try:
        df = pd.read_csv(input_csv_path)
        logging.info(f"Loaded input CSV '{input_csv_path}' with {len(df)} items.")
        return df
    except Exception as e:
        logging.error(f"Failed to read '{input_csv_path}': {e}")
        raise

def generate_unique_output_csv(output_base_path):
    # Extract directory, base name, and extension
    directory, filename = os.path.split(output_base_path)
    base, ext = os.path.splitext(filename)
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create unique filename
    unique_filename = f"{base}_{timestamp}{ext}"
    
    # Full path
    unique_output_path = os.path.join(directory, unique_filename) if directory else unique_filename
    
    return unique_output_path

def initialize_output_csv(output_csv_path, desired_columns, providers):
    # Since the user wants only the LLM responses and 'item_title' for verification
    input_fields = ['item_title']
    # Create column names for each provider
    provider_columns = []
    for col in desired_columns:
        for provider in providers:
            provider_columns.append(f"{col}_{provider}")
    
    output_fieldnames = input_fields + provider_columns
    
    try:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=output_fieldnames)
            writer.writeheader()
        logging.info(f"Initialized output CSV '{output_csv_path}' with headers.")
    except Exception as e:
        logging.error(f"Failed to initialize '{output_csv_path}': {e}")
        raise

def make_request(item, api_url):
    payload = {
        "item_title": item['item_title'],
        "short_description": item['short_description'],
        "long_description": item['long_description'],
        "item_product_type": item['item_product_type']
    }
    try:
        response = requests.post(api_url, json=payload, timeout=60)  # 60 seconds timeout
        response.raise_for_status()
        response_json = response.json()
        logging.info(f"Successfully received response for '{item['item_title']}'.")
        logging.debug(f"Response JSON for '{item['item_title']}': {response_json}")
        return (item, response_json)
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed for '{item['item_title']}': {e}")
        return (item, None)
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error for '{item['item_title']}': {e}")
        return (item, None)

def process_response(item, response_json, desired_columns, providers):
    row = {
        'item_title': item['item_title']
    }
    malformed_entries = []  # To track malformed responses
    
    if not response_json:
        # If there's no response, leave task fields empty or add error messages
        for col in desired_columns:
            for provider in providers:
                column_name = f"{col}_{provider}"
                row[column_name] = 'No response or error'
                malformed_entries.append({
                    'provider': provider,
                    'task': COLUMN_TASK_MAPPING.get(col, col),
                    'error': 'No response or error'
                })
        logging.debug(f"No response for '{item['item_title']}'.")
        return row, malformed_entries
    
    for col in desired_columns:
        task = COLUMN_TASK_MAPPING.get(col)
        if not task:
            for provider in providers:
                column_name = f"{col}_{provider}"
                row[column_name] = 'Unknown task'
                malformed_entries.append({
                    'provider': provider,
                    'task': task,
                    'error': 'Unknown task'
                })
            logging.warning(f"Unknown task '{col}' for '{item['item_title']}'.")
            continue
        # Extract responses from all providers
        task_response = response_json.get(task, {})
        for provider in providers:
            provider_response = task_response.get(provider, '')
            column_name = f"{col}_{provider}"
            if not provider_response:
                row[column_name] = 'No response'
                malformed_entries.append({
                    'provider': provider,
                    'task': task,
                    'error': 'No response'
                })
                logging.debug(f"No response from provider '{provider}' for task '{task}' on item '{item['item_title']}'.")
            else:
                if isinstance(provider_response, str):
                    try:
                        # Attempt to parse the JSON string
                        parsed_response = json.loads(provider_response)
                        logging.debug(f"Parsed response for provider '{provider}' on item '{item['item_title']}': {parsed_response}")
                        # Extract the enhanced field
                        key = col  # Corrected key assignment
                        enhanced_value = parsed_response.get(key, 'No response')
                        row[column_name] = enhanced_value
                        logging.debug(f"Extracted '{key}' for provider '{provider}' on item '{item['item_title']}': {enhanced_value}")
                        if enhanced_value == 'No response':
                            malformed_entries.append({
                                'provider': provider,
                                'task': task,
                                'error': 'Missing enhanced field'
                            })
                    except json.JSONDecodeError:
                        # If not a JSON string, clean the string
                        cleaned_response = provider_response.replace('\n', ' ').strip()
                        row[column_name] = cleaned_response
                        malformed_entries.append({
                            'provider': provider,
                            'task': task,
                            'error': 'JSON parsing failed'
                        })
                        logging.debug(f"JSON parsing failed for provider '{provider}' on item '{item['item_title']}': {provider_response}")
                elif isinstance(provider_response, dict):
                    # Directly extract the enhanced field
                    key = col  # Corrected key assignment
                    enhanced_value = provider_response.get(key, 'No response')
                    row[column_name] = enhanced_value
                    logging.debug(f"Extracted '{key}' for provider '{provider}' on item '{item['item_title']}': {enhanced_value}")
                    if enhanced_value == 'No response':
                        malformed_entries.append({
                            'provider': provider,
                            'task': task,
                            'error': 'Missing enhanced field'
                        })
                else:
                    row[column_name] = 'Invalid response format'
                    malformed_entries.append({
                        'provider': provider,
                        'task': task,
                        'error': 'Invalid response format'
                    })
                    logging.debug(f"Invalid response format from provider '{provider}' on item '{item['item_title']}'.")
    return row, malformed_entries

def write_row(output_csv_path, row_data, output_fieldnames):
    try:
        with open(output_csv_path, 'a', newline='', encoding='utf-8') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=output_fieldnames)
            writer.writerow(row_data)
        logging.debug(f"Wrote row for '{row_data.get('item_title', 'Unknown')}': {row_data}")
    except Exception as e:
        logging.error(f"Failed to write row for '{row_data.get('item_title', 'Unknown')}': {e}")

def write_error_summary(error_summary_path, error_counts):
    try:
        with open(error_summary_path, 'w', newline='', encoding='utf-8') as f_out:
            fieldnames = ['provider', 'task', 'error_count']
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            writer.writeheader()
            for (provider, task), count in error_counts.items():
                writer.writerow({
                    'provider': provider,
                    'task': task,
                    'error_count': count
                })
        logging.info(f"Initialized error summary CSV '{error_summary_path}' with headers.")
    except Exception as e:
        logging.error(f"Failed to write error summary '{error_summary_path}': {e}")
        raise

def main():
    args = parse_arguments()
    
    # Parse desired columns
    desired_columns = [col.strip() for col in args.columns.split(',') if col.strip()]
    
    # Identify all unique providers from the response samples
    # For this example, we'll assume 'runpod_vllm1' and 'runpod_vllm2'
    # You can modify this list based on actual providers in your responses
    providers = ['runpod_vllm1', 'runpod_vllm2']
    
    # Map desired columns to tasks and filter out unknown columns
    filtered_columns = []
    for col in desired_columns:
        task = COLUMN_TASK_MAPPING.get(col)
        if task:
            filtered_columns.append(col)
        else:
            logging.warning(f"Unknown column '{col}'. It will be skipped.")
    
    if not filtered_columns:
        logging.error("No valid output columns specified. Exiting.")
        print("No valid output columns specified. Please check your --columns parameter.")
        exit(1)
    
    # Generate unique output CSV path with timestamp
    unique_output_csv = generate_unique_output_csv(args.output)
    
    # Generate unique error summary CSV path with timestamp
    directory, filename = os.path.split(args.output)
    base, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_summary_filename = f"error_summary_{base}_{timestamp}.csv"
    error_summary_path = os.path.join(directory, error_summary_filename) if directory else error_summary_filename
    
    # Initialize output CSV with only LLM responses and item_title
    initialize_output_csv(unique_output_csv, filtered_columns, providers)
    
    # Initialize error summary data structure
    error_counts = {}  # Key: (provider, task), Value: count
    
    # Load input CSV
    try:
        df = load_input_csv(args.input)
    except Exception:
        print(f"Failed to load input CSV '{args.input}'. Check the log for details.")
        exit(1)
    
    # Initialize tqdm progress bar
    total_items = len(df)
    progress_bar = tqdm(total=total_items, desc="Processing Items", unit="item")
    
    # Use ThreadPoolExecutor for concurrency
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        # Submit all tasks
        future_to_item = {executor.submit(make_request, row, args.api_url): row for index, row in df.iterrows()}
        
        for future in as_completed(future_to_item):
            item, response_json = future.result()
            row_data, malformed_entries = process_response(item, response_json, filtered_columns, providers)
            # Define the fieldnames based on initialization
            fieldnames = ['item_title'] + [f"{col}_{provider}" for col in filtered_columns for provider in providers]
            write_row(unique_output_csv, row_data, fieldnames)
            
            # Update error counts
            for entry in malformed_entries:
                provider = entry['provider']
                task = entry['task']
                key = (provider, task)
                error_counts[key] = error_counts.get(key, 0) + 1
            
            # Update progress bar
            progress_bar.update(1)
    
    progress_bar.close()
    
    # Write error summary CSV
    write_error_summary(error_summary_path, error_counts)
    
    logging.info("All requests processed and responses saved.")
    print(f"\nAll requests processed and responses saved in '{unique_output_csv}'.")
    print(f"Error summary saved in '{error_summary_path}'.")
    print(f"Detailed logs available in 'make_requests.log'.")

if __name__ == "__main__":
    main()
