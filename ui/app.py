# File: main.py (or your main Gradio entry point)

import argparse
import gradio as gr
import pandas as pd
import os

# Local imports
from ui.db.admin_database_handler import AdminDatabaseHandler
from ui.admin_tabs.styling_guide_manager_tab import create_styling_guide_manager_tab
from ui.admin_tabs.provider_manager_tab import create_provider_configuration_tab
from ui.admin_tabs.task_management_tab import create_task_management_tab
from ui.admin_tabs.template_manager_tab import create_prompt_template_management_tab
from ui.admin_tabs.task_mapping_tab import create_task_mapping_tab
from ui.tabs.analytics_tab import create_analytics_tab
from ui.tabs.item_enrichment_tab import create_item_enrichment_tab
from ui.db.database_handler import DatabaseHandler
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
from ui.tabs.leaderboard_tab import create_leaderboard_tab  # Our updated tab
from utils import load_product_types_from_file

# NEW: Our BigQuery Leaderboard Handler
from bigquery_leaderboard_handler import BigQueryLeaderboardHandler

# ---------------------------
# Parse command-line arguments
# ---------------------------
parser = argparse.ArgumentParser(description="Run Gradio application with a specific database path.")
parser.add_argument("--db-path", type=str, default="/Users/xxx/Workspace/item-setup-playground/results.db",
                    help="Path to the SQLite database")
args = parser.parse_args()

# ---------------------------
# Initialize local DB
# ---------------------------
db_handler = DatabaseHandler(db_path=args.db_path)
db_handler.create_tables()

admin_db_handler = AdminDatabaseHandler(db_path=args.db_path)

# ---------------------------
# Initialize BigQuery Handler
# ---------------------------
project_id = "wmt-rg-dev"  # Replace with your actual GCP project ID
bq_leaderboard = BigQueryLeaderboardHandler(project_id=project_id)

def get_leaderboard_bq(**filters):
    """
    Adapts the filter dict from the UI into parameters for BigQueryLeaderboardHandler.
    Example filters might include:
      - dataset_id
      - product_type
      - generation_task
    """
    dataset_id = filters.get("dataset_id")
    product_type = filters.get("product_type")
    generation_task = filters.get("generation_task")

    if dataset_id is None:
        return pd.DataFrame()  # or None

    df = bq_leaderboard.get_leaderboard(
        dataset_id=dataset_id,
        product_type=product_type,
        generation_task=generation_task
    )
    return df

# ---------------------------
# Load product types
# ---------------------------
product_types = load_product_types_from_file('product_types.txt')
if not product_types:
    product_types = ["Electronics", "Clothing", "Home Goods", "Toys", "Books", "Other"]

# ---------------------------
# Build Gradio Interface
# ---------------------------
with gr.Blocks(css="styles.css") as app:
    gr.Markdown("# Item Setup Playground Interface")

    with gr.Tabs():
        # User-Facing Tabs
        create_item_enrichment_tab(
            process_single_sku,
            save_preference,
            product_types
        )

        # Our new, updated Leaderboard Tab
        # Note we pass:
        #   1) get_leaderboard_bq (the BigQuery aggregator)
        #   2) admin_db_handler.get_evaluation_tasks (for dynamic eval tasks)
        #   3) product_types
        #   4) admin_db_handler.get_datasets (the local DB method)
        create_leaderboard_tab(
            get_leaderboard_bq_fn=get_leaderboard_bq,
            get_evaluation_tasks_fn=admin_db_handler.get_evaluation_tasks,
            product_types=product_types,
            get_datasets_fn=admin_db_handler.get_datasets
        )

        # Analytics, Feedback, etc.
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
        create_task_mapping_tab(admin_db_handler)
        create_prompt_template_management_tab(admin_db_handler)
        create_provider_configuration_tab(admin_db_handler)
        create_styling_guide_manager_tab(admin_db_handler, product_types)

if __name__=="__main__":
    app.launch()
