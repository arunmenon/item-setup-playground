import sqlite3
import streamlit as st
import pandas as pd

def display_single_sku_input():
    """
    Displays input fields for a single SKU.
    """
    sku = st.text_input("SKU")
    gtin = st.text_input("GTIN")
    title = st.text_input("Title")
    short_description = st.text_area("Short Description")
    long_description = st.text_area("Long Description")
    product_type = st.selectbox(
        "Product Type",
        ["Casual & Dress Shoes", "Jeans", "Pants", "Sweatshirts & Hoodies", "T-Shirts"]
    )
    return gtin, title, short_description, long_description, product_type

def display_model_responses(data):
    """
    Displays model responses and returns them as a dictionary.
    """
    model_responses = {}
    for model_name, model_response in data["title_enhancement"].items():
        enhanced_title = model_response.get("response", {}).get("enhanced_title", "NA")
        model_responses[model_name] = enhanced_title
        st.markdown(f'<div class="response-box">', unsafe_allow_html=True)
        st.write(f"**Model:** {model_name}")
        st.write(f"**Enhanced Title:** {enhanced_title}")
        st.markdown("</div>", unsafe_allow_html=True)
    return model_responses

def display_leaderboard(database_handler):
    """
    Displays a leaderboard of model preferences.
    """
    conn = sqlite3.connect(database_handler.db_path)
    df = pd.read_sql_query('''
        SELECT task_type, winner_response, COUNT(winner_response) AS count
        FROM responses
        GROUP BY task_type, winner_response
        ORDER BY count DESC
    ''', conn)
    conn.close()
    st.table(df)
