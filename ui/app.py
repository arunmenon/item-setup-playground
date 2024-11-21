import gradio as gr
import pandas as pd
from utils import load_product_types_from_file
from handlers import process_single_sku, save_preference, get_leaderboard, next_index, prev_index
from plots import generate_leaderboard_plot
from ui_components import create_item_enrichment_tab, create_leaderboard_tab, create_analytics_tab
import os

# Load product types from 'product_types.txt'
product_types = load_product_types_from_file('product_types.txt')
if not product_types:
    # Provide default product types if the file is empty or not found
    product_types = ["Electronics", "Clothing", "Home Goods", "Toys", "Books", "Other"]

# Gradio Interface
with gr.Blocks(css="styles.css") as app:
    gr.Markdown("# Item Setup Playground Interface")

    with gr.Tabs():
        create_item_enrichment_tab(process_single_sku, save_preference, product_types, next_index, prev_index)
        create_leaderboard_tab(get_leaderboard)
        create_analytics_tab(generate_leaderboard_plot, get_leaderboard)

if __name__ == "__main__":
    app.launch()
