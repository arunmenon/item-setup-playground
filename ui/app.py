import requests
import streamlit as st
import pandas as pd
from database_handler import DatabaseHandler
from api_client import APIClient
from ui_components import display_single_sku_input, display_model_responses, display_leaderboard
from styles import get_css  # Import the CSS function

# Initialize instances
db_handler = DatabaseHandler()
api_client = APIClient()

# Ensure tables are created in the database if they don't already exist
db_handler.create_tables_if_not_exists()

# Streamlit App configuration
st.set_page_config(page_title="Item Setup Playground", layout="wide")

# Apply custom CSS styling
st.markdown(get_css(), unsafe_allow_html=True)

# Main Title and description
st.markdown('<div class="title">Item Setup Playground Interface</div>', unsafe_allow_html=True)

# User Choice: Single SKU or Bulk Upload
st.markdown('<div class="subheader">Choose Input Method</div>', unsafe_allow_html=True)
choice = st.radio("Would you like to process a single SKU or upload a CSV file for bulk processing?", ("Single SKU", "Bulk Upload"))

# Ensure session state is available for storing preferences in bulk
if "preferences" not in st.session_state:
    st.session_state["preferences"] = {}

# Function to process a single SKU
def process_single_sku(gtin, title, short_description, long_description, product_type):
    try:
        data = api_client.process_single_sku(gtin, title, short_description, long_description, product_type)
        st.success("Enrichment generated successfully!")
        model_responses = display_model_responses(data)

        # Display model responses in a table
        if model_responses:
            response_df = pd.DataFrame([
                {"Model": model_name, "Enhanced Title": enhanced_title} for model_name, enhanced_title in model_responses.items()
            ])
            st.table(response_df)

            # Select preferred response
            selected_response = st.radio(
                "Select your preferred response:",
                options=[(model_name, enhanced_title) for model_name, enhanced_title in model_responses.items()],
                format_func=lambda x: f"{x[0]}: {x[1]}"
            )

            # Save preference
            if st.button("Save Preference", key=f"save_{gtin}"):
                db_handler.save_preference(gtin, product_type, "title_enhancement", model_responses, selected_response[1])
                st.success("Preference saved successfully!")
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")

# Function to handle single SKU flow
def process_single_sku_flow():
    gtin, title, short_description, long_description, product_type = display_single_sku_input()

    if st.button("Generate Enrichment"):
        with st.spinner("Generating enrichment..."):
            process_single_sku(gtin, title, short_description, long_description, product_type)

# Function to handle bulk upload flow
def process_bulk_upload_flow():
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
        st.write("CSV file loaded successfully!")

        # Normalize column names for flexible access
        data.columns = [col.lower().replace(" ", "_") for col in data.columns]

        # Required columns with normalized names
        required_columns = {"long_description", "gtin", "product_type", "title", "short_description"}

        if not required_columns.issubset(data.columns):
            missing_cols = required_columns - set(data.columns)
            st.error(f"CSV must contain the following columns: {', '.join(required_columns)}. Missing columns: {', '.join(missing_cols)}")
        else:
            for index, row in data.iterrows():
                gtin = row["gtin"]
                title = row["title"]
                short_desc = row["short_description"]
                long_desc = row["long_description"]
                product_type = row["product_type"]
                
                with st.spinner(f"Processing SKU {gtin}..."):
                    try:
                        response_data = api_client.process_single_sku(gtin, title, short_desc, long_desc, product_type)
                        model_responses = display_model_responses(response_data)

                        if model_responses:
                            st.markdown(f"**SKU: {gtin} ({product_type} - {title}) - Model Responses**")
                            response_df = pd.DataFrame([
                                {"Model": model_name, "Enhanced Title": enhanced_title} for model_name, enhanced_title in model_responses.items()
                            ])
                            st.table(response_df)

                            selected_response = st.radio(
                                f"Select your preferred response for SKU {gtin}:",
                                options=[(model_name, enhanced_title) for model_name, enhanced_title in model_responses.items()],
                                format_func=lambda x: f"{x[0]}: {x[1]}",
                                key=f"response_{index}"
                            )

                            # Store preference in session state
                            st.session_state["preferences"][gtin] = {
                                "gtin": gtin,
                                "product_type": product_type,
                                "task_type": "title_enhancement",
                                "model_responses": model_responses,
                                "winner_response": selected_response[1] if selected_response else "NA"
                            }
                        else:
                            st.warning(f"No model responses available for SKU {gtin}.")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error processing SKU {gtin}: {e}")

            # Bulk save preferences after collecting all
            if st.button("Save All Preferences"):
                for pref in st.session_state["preferences"].values():
                    db_handler.save_preference(
                        pref["gtin"], pref["product_type"], pref["task_type"],
                        pref["model_responses"], pref["winner_response"]
                    )
                st.success("All preferences saved successfully!")
                # Clear session state preferences after saving
                st.session_state["preferences"].clear()

# Route the logic based on user choice
if choice == "Single SKU":
    process_single_sku_flow()
elif choice == "Bulk Upload":
    process_bulk_upload_flow()

# Leaderboard Section
st.markdown('<div class="subheader">Leaderboard</div>', unsafe_allow_html=True)
display_leaderboard(db_handler)
