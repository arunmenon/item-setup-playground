import gradio as gr
import json
from api_client import APIClient
from database_handler import DatabaseHandler
from ui_helpers import display_single_sku_input
from styles import get_css

# Initialize API client and database handler
api_client = APIClient()
db_handler = DatabaseHandler()

def process_single_sku(gtin, title, short_description, long_description, product_type):
    """
    Process a single SKU by sending data to the API and retrieving model responses.
    """
    try:
        # Send data to the API and get responses
        data = api_client.process_single_sku(gtin, title, short_description, long_description, product_type)
        model_responses = data.get("title_enhancement", {})
        
        if not model_responses:
            return gr.update(choices=["No responses available"]), "{}"
        
        # Extract and format responses for display
        formatted_responses = [
            f"{model_name}: {details.get('response', {}).get('enhanced_title', 'NA')}"
            for model_name, details in model_responses.items()
        ]
        
        # Return formatted responses and serialized model responses
        return gr.update(choices=formatted_responses), json.dumps(model_responses)
    except Exception as e:
        return gr.update(choices=[f"Error: {e}"]), "{}"

def save_preference(selected_response, model_responses_json, gtin, product_type):
    """
    Save the user's preferred model response to the database and update the leaderboard.
    """
    print(f"Received selected_response: {selected_response}")
    print(f"Received model_responses_json: {model_responses_json}")
    print(f"Received gtin: {gtin}, product_type: {product_type}")

    if not selected_response:
        print("No response selected by the user.")
        return "Please select a response before saving."

    try:
        # Deserialize model responses
        model_responses = json.loads(model_responses_json)
        print(f"Deserialized model_responses: {model_responses}")
    except json.JSONDecodeError as e:
        print(f"JSON decoding failed: {e}")
        return "Error: Failed to process model responses."

    # Save preference in the database
    db_handler.save_preference(gtin, product_type, "title_enhancement", model_responses, selected_response)
    print(f"Saved preference for GTIN: {gtin}, Product Type: {product_type}")

    # Extract model name from the selected response
    try:
        model_name = selected_response.split(":")[0].strip()
        print(f"Extracted model_name: {model_name}")
    except Exception as e:
        print(f"Failed to extract model name: {e}")
        return "Error: Failed to extract model name from the selected response."

    # Update leaderboard
    db_handler.increment_model_preference("title_enhancement", product_type, model_name)
    print(f"Incremented preference count for model: {model_name} in leaderboard.")

    return "Preference saved successfully!"

def get_leaderboard():
    """
    Retrieve the leaderboard data from the database.
    """
    leaderboard_df = db_handler.get_leaderboard()
    return leaderboard_df

# Retrieve the initial leaderboard data
initial_leaderboard_data = get_leaderboard()

# Gradio Interface
with gr.Blocks(css=get_css()) as app:
    gr.Markdown("# Item Setup Playground Interface")

    # Input Components
    gtin, title, short_desc, long_desc, product_type = display_single_sku_input()
    
    # Generate Enrichment Button
    generate_btn = gr.Button("Generate Enrichment")
    
    # Model Responses Display and Preference Selection
    model_responses_output = gr.Radio(label="Select your preferred response:")
    save_btn = gr.Button("Save Preference")
    feedback_output = gr.Textbox(label="Feedback", interactive=False)
    
    # Leaderboard Display
    leaderboard_output = gr.Dataframe(
        headers=["Task Type", "Product Type", "Model", "Preference Count"],
        value=initial_leaderboard_data
    )

    # State Components to hold intermediate data
    state_model_responses = gr.State(value="{}")  # Initialize with an empty JSON object

    # Define actions for buttons
    generate_btn.click(
        fn=process_single_sku, 
        inputs=[gtin, title, short_desc, long_desc, product_type],
        outputs=[model_responses_output, state_model_responses]
    )

    save_btn.click(
        fn=save_preference,
        inputs=[model_responses_output, state_model_responses, gtin, product_type],
        outputs=feedback_output
    )

# Launch the Gradio app
if __name__ == "__main__":
    app.launch()
