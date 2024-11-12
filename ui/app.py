import gradio as gr
import json
from api_client import APIClient
from database_handler import DatabaseHandler
from ui_helpers import display_single_sku_input
from styles import get_css
import plotly.express as px
import pandas as pd  # Ensure pandas is imported

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
            return gr.update(choices=["No responses available"]), {}
        
        # Extract and format responses for display
        formatted_responses = [
            f"{model_name}: {details.get('response', {}).get('enhanced_title', 'NA')}"
            for model_name, details in model_responses.items()
        ]
        
        # Return formatted responses and model responses dict
        return gr.update(choices=formatted_responses), model_responses
    except Exception as e:
        return gr.update(choices=[f"Error: {e}"]), {}

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
        # Use model_responses directly since it's a dict
        model_responses = model_responses_json
    except Exception as e:
        print(f"Failed to process model responses: {e}")
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

def generate_leaderboard_plot():
    leaderboard_df = db_handler.get_leaderboard()
    if leaderboard_df.empty:
        return None
    fig = px.bar(
        leaderboard_df,
        x="model_name",
        y="preference_count",
        color="product_type",
        barmode="group",
        title="Model Preferences by Product Type"
    )
    return fig

def get_leaderboard():
    """
    Retrieve the leaderboard data from the database.
    """
    leaderboard_df = db_handler.get_leaderboard()
    return leaderboard_df

# Retrieve the initial leaderboard data
initial_leaderboard_data = get_leaderboard()
if initial_leaderboard_data.empty:
    initial_leaderboard_data = pd.DataFrame(columns=["Task Type", "Product Type", "Model", "Preference Count"])

initial_plot = generate_leaderboard_plot()
if initial_plot is None:
    initial_plot = px.Figure()

# Gradio Interface
with gr.Blocks(css=get_css()) as app:
    gr.Markdown("# Item Setup Playground Interface")

    with gr.Tabs():
        with gr.TabItem("Item Enrichment"):
            with gr.Row():
                with gr.Column():
                    gtin, title, short_desc, long_desc, product_type = display_single_sku_input()
                    generate_btn = gr.Button("Generate Enrichment")
                with gr.Column():
                    model_responses_output = gr.Radio(label="Select your preferred response:")
                    save_btn = gr.Button("Save Preference")
                    feedback_output = gr.Textbox(label="Feedback", interactive=False)
                    model_responses_json = gr.JSON(visible=False)  # Hidden component

            # Define actions for buttons
            generate_btn.click(
                fn=process_single_sku, 
                inputs=[gtin, title, short_desc, long_desc, product_type],
                outputs=[model_responses_output, model_responses_json]
            )

            save_btn.click(
                fn=save_preference,
                inputs=[model_responses_output, model_responses_json, gtin, product_type],
                outputs=feedback_output
            )

        with gr.TabItem("Leaderboard & Analytics"):
            gr.Markdown("## Leaderboard")
            refresh_button = gr.Button("Refresh Data")
            leaderboard_output = gr.Dataframe(
                headers=["Task Type", "Product Type", "Model", "Preference Count"],
                value=initial_leaderboard_data
            )
            gr.Markdown("## Analytics")
            analytics_plot = gr.Plot(value=initial_plot)

            # Define the refresh function
            def refresh_leaderboard_and_analytics():
                updated_leaderboard_data = get_leaderboard()
                if updated_leaderboard_data.empty:
                    updated_leaderboard_data = pd.DataFrame(columns=["Task Type", "Product Type", "Model", "Preference Count"])
                updated_plot = generate_leaderboard_plot()
                return updated_leaderboard_data, updated_plot

            # Action for refresh button
            refresh_button.click(
                fn=refresh_leaderboard_and_analytics,
                inputs=[],
                outputs=[leaderboard_output, analytics_plot]
            )

# Launch the Gradio app
if __name__ == "__main__":
    app.launch()
