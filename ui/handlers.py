from random import choices

import gradio as gr
from api_client import APIClient
from database_handler import DatabaseHandler

# Initialize API client and database handler
api_client = APIClient()
db_handler = DatabaseHandler()

def next_index(atr_index, attr_list, attrwise_model_response):
    size = len(attr_list)
    if size == 0:
        return [0, "", gr.update(choices=[]), {}]
    atr_index += 1
    if atr_index >= size:
        atr_index = size-1

    attribute_ae = attr_list[atr_index]
    model_responses_json_ae = attrwise_model_response[attribute_ae]

    # Extract and format responses for display
    formatted_response = [
        f"{model_name}: {details.get('response', {}).get('attribute_enrichment', 'NA')}"
        # key name changes process to process
        for model_name, details in model_responses_json_ae.items()
    ]

    return [atr_index, attribute_ae, gr.update(choices=formatted_response), model_responses_json_ae]


def prev_index(atr_index, attr_list, attrwise_model_response):
    size = len(attr_list)
    if size == 0:
        return [0, "", gr.update(choices=[]), {}]
    atr_index -= 1
    if atr_index < 0:
        atr_index = 0

    attribute_ae = attr_list[atr_index]
    model_responses_json_ae = attrwise_model_response[attribute_ae]

    # Extract and format responses for display
    formatted_response = [
        f"{model_name}: {details.get('response', {}).get('attribute_enrichment', 'NA')}"
        # key name changes process to process
        for model_name, details in model_responses_json_ae.items()
    ]

    return [atr_index, attribute_ae, gr.update(choices=formatted_response), model_responses_json_ae]


def process_single_sku(gtin, title, short_description, long_description, product_type):
    """
    Process a single SKU by sending data to the API and retrieving model responses.
    """
    # Validation: Ensure a product type is selected
    if not product_type:
        return [
            gr.update(choices=[]), {}, "Please select a product type.",
            gr.update(choices=[]), {}, "Please select a product type.",
            gr.update(choices=[]), {}, "Please select a product type.",
            gr.update(choices=[]), {}, "Please select a product type.",
            "", [], {}, 0
        ]

    try:
        # Send data to the API and get responses
        data = api_client.process_single_sku(
            gtin, title, short_description, long_description, product_type
        )
        model_responses_t = data.get("title_enhancement", {})
        model_responses_sd = data.get("short_description_enhancement", {})
        model_responses_ld = data.get("long_description_enhancement", {})
        model_responses_ae = data.get("ae_enrichment", {})


        attrwise_model_response = dict()
        for model, details in model_responses_ae.items():
            atr_vals = details.get('response', {}).get('attribute_enrichment', {})
            for atr in atr_vals:
                if atr not in attrwise_model_response:
                    attrwise_model_response[atr] = {}
                attrwise_model_response[atr][model] = {
                    "response": {
                        "attribute_enrichment": atr_vals[atr]
                    }
                }
        # Setting dummy attrwise_model_response
        attrwise_model_response = {'color': {'gpt-4o': {'response': {'attribute_enrichment': 'Red'}}, 'gemini-1.5-flash': {'response': {'attribute_enrichment': 'Red, Blue'}}}, 'gender': {'gpt-4o': {'response': {'attribute_enrichment': 'Male'}}, 'gemini-1.5-flash': {'response': {'attribute_enrichment': 'Male'}}}, 'age_group': {'gpt-4o': {'response': {'attribute_enrichment': 'Adults'}}, 'gemini-1.5-flash': {'response': {'attribute_enrichment': 'NA'}}}, 'zippered': {'gpt-4o': {'response': {'attribute_enrichment': 'Yes'}}, 'gemini-1.5-flash': {'response': {'attribute_enrichment': 'Yes'}}}, 'shirt_neck_style': {'gpt-4o': {'response': {'attribute_enrichment': 'Polo'}}, 'gemini-1.5-flash': {'response': {'attribute_enrichment': 'NA'}}}}
        #####################################################################################
        attr_list = list(attrwise_model_response.keys())
        curr_ae_model_response = dict()
        if len(attr_list) > 0:
            curr_ae_model_response = attrwise_model_response[attr_list[0]]

        # curr_ae_model_response = {"gpt-4o": {"response": {"attribute_enrichment": "Red"}},"gemini-1.5-flash": {"response": {"attribute_enrichment": "Red, Blue"}}}
        # attr_list = ["color","gender"]
        model_responses = [model_responses_t, model_responses_sd, model_responses_ld, curr_ae_model_response]
        model_response_keys = ["enhanced_title", "enhanced_short_description", "enhanced_long_description", "attribute_enrichment"]
        # Extract and format responses for display
        formatted_responses = []

        for model_name, details in model_responses.items():
            model_version = details.get('model_version', '1.0')
            response_text = details.get('response', {}).get('enhanced_title', 'NA')
            formatted_responses.append(f"{model_name} v{model_version}: {response_text}")
        

        # Return formatted responses and model responses dict
        response = []
        for model_counter in range(len(model_responses)):
            if not model_responses[model_counter]:
                response.extend([gr.update(choices=["No responses available"]), {}, "No responses available."])
            else:
                response.extend([gr.update(choices=formatted_responses[model_counter]), model_responses[model_counter], ""])
        if len(attr_list)>0:
            response.extend([attr_list[0], attr_list, attrwise_model_response, 0]) #passing initial index as 0
        else:
            response.extend(["",[],{},0])
        return response
    except Exception as e:
        return [
                    gr.update(choices=[]), {}, f"Error: {e}",
                    gr.update(choices=[]), {}, f"Error: {e}",
                    gr.update(choices=[]), {}, f"Error: {e}",
                    gr.update(choices=[]), {}, f"Error: {e}",
                    "Error",[],{},0
                ]


def save_preference(selected_response, model_responses_json, gtin, product_type,
                    relevance, clarity, compliance, accuracy, comments, task_type):
    """
    Save the user's preferred model response and detailed feedback to the database.
    """
    if not selected_response:
        return "Please select a response before saving."

    try:
        model_responses = model_responses_json
    except Exception as e:
        return "Error: Failed to process model responses."

    # Extract model name and version from the selected response
    try:
        selected_model_info = selected_response.split(":")[0].strip()
        if " v" in selected_model_info:
            model_name, model_version = selected_model_info.split(" v")
        else:
            model_name = selected_model_info
            model_version = "1.0"
    except Exception as e:
        return "Error: Failed to extract model name and version from the selected response."


    # Save human evaluation
    db_handler.save_evaluation(
        item_id=gtin,
        product_type=product_type,
        task=task_type,
        model_name=model_name,
        model_version=model_version,
        evaluator_type='Human',
        relevance=relevance,
        clarity=clarity,
        compliance=compliance,
        accuracy=accuracy,
        comments=comments,
        is_winner=True  # The selected response is the winner
    )

    # Update leaderboard
    db_handler.increment_model_preference(task_type, product_type, model_name)

    return "Preference and feedback saved successfully!"

def get_leaderboard():
    """
    Retrieve the leaderboard data from the database.
    """
    leaderboard_df = db_handler.get_leaderboard()
    return leaderboard_df
