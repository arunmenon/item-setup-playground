import csv
import requests
import itertools
from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm
from datetime import datetime

# Constants
API_ENDPOINT = "http://localhost:5000/enrich-item"
MODEL = SentenceTransformer('all-MiniLM-L6-v2')
INPUT_FILE = "enhanced_input_skus.csv"

# Generate a filename with a timestamp suffix
def generate_filename(base_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.csv"

# Save data to a CSV file with a timestamped filename
def save_to_csv(base_name, data, fieldnames):
    filename = generate_filename(base_name)
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print(f"Data saved to {filename}")

# Step 1: Load SKU Data
def load_sku_data(filename):
    sku_data = []
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            sku_data.append(row)
    return sku_data

# Step 2: Send Requests and Collect Model Responses
def fetch_model_responses(sku_data):
    results = []
    with tqdm(total=len(sku_data), desc="Processing SKUs", unit="SKU") as pbar:
        for item in sku_data:
            payload = {
                "item_title": item["Title"],
                "short_description": item["Short_Description"],
                "long_description": item["Long_Description"],
                "item_product_type": item["Product_Type"]
            }
            
            response = requests.post(API_ENDPOINT, json=payload)
            if response.status_code == 200:
                data = response.json()
                for task, handlers in data.items():
                    task_results = {"SKU": item["SKU"], "GTIN": item["GTIN"], "Task": task}
                    for handler_name, handler_response in handlers.items():
                        # Use .get() to safely access 'response' and 'error'
                        response_text = handler_response.get("response")
                        error_message = handler_response.get("error")

                        # Check if the model response is successful and extract enhanced_title if available
                        if response_text and error_message is None:
                            # Extract enhanced_title text
                            enhanced_title = response_text.get("enhanced_title") if isinstance(response_text, dict) else "NA"
                            task_results[handler_name] = enhanced_title
                        else:
                            # Mark as NA if there's an error or missing response
                            print(f"Error from {handler_name} for SKU {item['SKU']}: {error_message}")
                            task_results[handler_name] = "NA"
                    results.append(task_results)
            else:
                print(f"Failed to get response for SKU {item['SKU']} with status code {response.status_code}")
            pbar.update(1)  # Update progress bar
    return results

# Step 3: Calculate Pairwise Semantic Similarity Scores
def calculate_pairwise_similarity(task_responses):
    scores = []
    valid_responses = [resp for resp in task_responses if resp["Response"] != "NA"]

    if len(valid_responses) > 1:
        embeddings = MODEL.encode([resp["Response"] for resp in valid_responses])

        for (i, response1), (j, response2) in itertools.combinations(enumerate(valid_responses), 2):
            score = util.pytorch_cos_sim(embeddings[i], embeddings[j]).item()
            scores.append({
                "SKU": response1["SKU"],
                "GTIN": response1["GTIN"],
                "Task": response1["Task"],
                "Model_1": response1["Model"],
                "Response_1": response1["Response"],
                "Model_2": response2["Model"],
                "Response_2": response2["Response"],
                "Similarity_Score": score
            })
    return scores

# Main Execution
def main():
    # Load SKU data
    sku_data = load_sku_data(INPUT_FILE)
    
    # Fetch model responses with progress bar
    responses = fetch_model_responses(sku_data)
    save_to_csv("model_responses", responses, fieldnames=["SKU", "GTIN", "Task", "openai", "gemini"])

    # Calculate pairwise similarity for each SKU and task
    all_similarity_scores = []
    for response in responses:
        task_responses = [
            {"SKU": response["SKU"], "GTIN": response["GTIN"], "Task": response["Task"], "Model": model, "Response": resp}
            for model, resp in response.items()
            if model in ["openai", "gemini"] and resp != "NA"
        ]
        
        # Compute similarity scores for each task with valid responses
        similarity_scores = calculate_pairwise_similarity(task_responses)
        all_similarity_scores.extend(similarity_scores)
    
    # Save similarity scores to CSV with timestamp
    save_to_csv("similarity_scores", all_similarity_scores, fieldnames=[
        "SKU", "GTIN", "Task", "Model_1", "Response_1", "Model_2", "Response_2", "Similarity_Score"
    ])

if __name__ == "__main__":
    main()
