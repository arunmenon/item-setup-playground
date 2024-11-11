import gradio as gr
import pandas as pd

def display_single_sku_input():
    """
    Returns input components for single SKU processing.
    """
    gtin = gr.Textbox(label="GTIN", placeholder="Enter GTIN here")
    title = gr.Textbox(label="Title", placeholder="Enter Title here")
    short_description = gr.Textbox(label="Short Description", placeholder="Enter Short Description here")
    long_description = gr.Textbox(label="Long Description", placeholder="Enter Long Description here")
    product_type = gr.Dropdown(["Casual & Dress Shoes", "Jeans", "Pants", "Sweatshirts & Hoodies", "T-Shirts"], label="Product Type")
    return gtin, title, short_description, long_description, product_type

def display_model_responses(data):
    """
    Displays model responses and returns them as a dictionary.
    """
    return {model_name: details["response"]["enhanced_title"] for model_name, details in data["title_enhancement"].items()}

def display_leaderboard(database_handler):
    """
    Displays a leaderboard of model preferences.
    """
    leaderboard_df = database_handler.get_leaderboard()
    return leaderboard_df if not leaderboard_df.empty else pd.DataFrame({"Info": ["No leaderboard data available."]})
