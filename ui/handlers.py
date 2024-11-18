import gradio as gr
from api_client import APIClient
from database_handler import DatabaseHandler

# Initialize API client and database handler
api_client = APIClient()
db_handler = DatabaseHandler()

def process_single_sku(gtin, title, short_description, long_description, product_type):
    """
    Process a single SKU by sending data to the API and retrieving model responses.
    """
    # Validation: Ensure a product type is selected
    if not product_type:
        return gr.update(choices=[]), {}, "Please select a product type."

    try:
        # Send data to the API and get responses
        data = api_client.process_single_sku(
            gtin, title, short_description, long_description, product_type
        )
        model_responses = data.get("title_enhancement", {})

        if not model_responses:
            return gr.update(choices=["No responses available"]), {}, "No responses available."

        # Extract and format responses for display
        formatted_responses = [
            f"{model_name}: {details.get('response', {}).get('enhanced_title', 'NA')}"
            for model_name, details in model_responses.items()
        ]

        # Return formatted responses and model responses dict
        return gr.update(choices=formatted_responses), model_responses, ""
    except Exception as e:
        return gr.update(choices=[]), {}, f"Error: {e}"

def save_preference(selected_response, model_responses_json, gtin, product_type,
                    relevance, clarity, compliance, accuracy, comments):
    """
    Save the user's preferred model response and detailed feedback to the database.
    """
    if not selected_response:
        return "Please select a response before saving."

    try:
        model_responses = model_responses_json
    except Exception as e:
        return "Error: Failed to process model responses."

    # Extract model name from the selected response
    try:
        model_name = selected_response.split(":")[0].strip()
    except Exception as e:
        return "Error: Failed to extract model name from the selected response."

    # Save preference and feedback in the database
    db_handler.save_preference(
        gtin,
        product_type,
        "title_enhancement",
        model_responses,
        selected_response,
        model_name,
        relevance,
        clarity,
        compliance,
        accuracy,
        comments
    )

    # Update leaderboard
    db_handler.increment_model_preference("title_enhancement", product_type, model_name)

    return "Preference and feedback saved successfully!"

def get_leaderboard():
    """
    Retrieve the leaderboard data from the database.
    """
    leaderboard_df = db_handler.get_leaderboard()
    return leaderboard_df
