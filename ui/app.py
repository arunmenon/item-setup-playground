import gradio as gr
import pandas as pd
from ui.admin_database_handler import AdminDatabaseHandler
from ui.admin_ui_components import create_prompt_template_management_tab, create_provider_configuration_tab, create_styling_guide_manager_tab, create_task_management_tab
from ui.database_handler import DatabaseHandler
from utils import load_product_types_from_file
from handlers import process_single_sku, save_preference
from plots import generate_aggregated_plot, generate_leaderboard_plot, generate_winner_model_comparison_plot
from ui_components import create_feedback_tab, create_item_enrichment_tab, create_leaderboard_tab, create_analytics_tab
import os

# Initialize database handler and create tables
db_handler = DatabaseHandler()
db_handler.create_tables()
admin_db_handler = AdminDatabaseHandler()

# Load product types from 'product_types.txt'
product_types = load_product_types_from_file('product_types.txt')
if not product_types:
    # Provide default product types if the file is empty or not found
    product_types = ["Electronics", "Clothing", "Home Goods", "Toys", "Books", "Other"]

# Gradio Interface
with gr.Blocks(css="styles.css") as app:
    gr.Markdown("# Item Setup Playground Interface")

    with gr.Tabs():
        create_item_enrichment_tab(process_single_sku, save_preference, product_types)
        create_leaderboard_tab(db_handler.get_leaderboard,product_types)
        create_analytics_tab(generate_leaderboard_plot,
                              db_handler.get_leaderboard,
                              generate_winner_model_comparison_plot,
                              db_handler.get_evaluations,
                              db_handler.get_aggregated_evaluations,  # New function
                              generate_aggregated_plot,  # New plotting function 
                              product_types)
        create_feedback_tab(db_handler.get_evaluations, product_types)
        # Add admin tabs
        create_prompt_template_management_tab(admin_db_handler)
        create_task_management_tab(admin_db_handler)
        create_provider_configuration_tab(admin_db_handler)
        create_styling_guide_manager_tab(admin_db_handler, product_types)

if __name__ == "__main__":
    app.launch()
