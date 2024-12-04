import argparse
import gradio as gr
import pandas as pd
from ui.db.admin_database_handler import AdminDatabaseHandler
from ui.admin_tabs.styling_guide_manager_tab import create_styling_guide_manager_tab
from ui.admin_tabs.provider_manager_tab import create_provider_configuration_tab
from ui.admin_tabs.task_management_tab import create_task_management_tab
from ui.admin_tabs.template_manager_tab import create_prompt_template_management_tab
from ui.admin_tabs.task_mapping_tab import create_task_mapping_tab  # Import the new tab
from ui.tabs.analytics_tab import create_analytics_tab
from ui.tabs.leaderboard_tab import create_leaderboard_tab
from ui.tabs.item_enrichment_tab import create_item_enrichment_tab
from ui.db.database_handler import DatabaseHandler
from utils import load_product_types_from_file
from ui.handlers import process_single_sku, save_preference
from plots import (
    generate_aggregated_plot,
    generate_leaderboard_plot,
    generate_winner_model_comparison_plot,
    generate_confidence_level_breakdown,
    generate_correlation_heatmap,
    generate_variance_distribution_plot
)

from ui.tabs.feedback_tab import create_feedback_tab
import os

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Run Gradio application with a specific database path.")
parser.add_argument("--db-path", type=str, default="/Users/n0s09lj/Workspace/item-setup-playground/results.db", help="Path to the SQLite database")
args = parser.parse_args()

# Initialize database handler and create tables
db_handler = DatabaseHandler(db_path=args.db_path)
db_handler.create_tables()
admin_db_handler = AdminDatabaseHandler(db_path=args.db_path)

# Load product types from 'product_types.txt'
product_types = load_product_types_from_file('product_types.txt')
if not product_types:
    # Provide default product types if the file is empty or not found
    product_types = ["Electronics", "Clothing", "Home Goods", "Toys", "Books", "Other"]

# Gradio Interface
with gr.Blocks(css="styles.css") as app:
    gr.Markdown("# Item Setup Playground Interface")

    with gr.Tabs():
        # User-Facing Tabs
        create_item_enrichment_tab(process_single_sku, save_preference, product_types)
        create_leaderboard_tab(db_handler.get_leaderboard,
            admin_db_handler.get_evaluation_tasks,
            product_types)
        create_analytics_tab(
            generate_leaderboard_plot,
            db_handler.get_leaderboard,
            generate_winner_model_comparison_plot,
            db_handler.get_evaluations,
            db_handler.get_aggregated_evaluations,
            generate_aggregated_plot,
            generate_variance_distribution_plot,
            generate_confidence_level_breakdown,
            admin_db_handler.get_evaluation_tasks,
            product_types
        )
        create_feedback_tab(db_handler.get_evaluations, product_types)

        # Admin Tabs
        create_task_management_tab(admin_db_handler)
        create_task_mapping_tab(admin_db_handler)  # Added the new tab
        create_prompt_template_management_tab(admin_db_handler)
        create_provider_configuration_tab(admin_db_handler)
        create_styling_guide_manager_tab(admin_db_handler, product_types)

if __name__=="__main__":
    app.launch()