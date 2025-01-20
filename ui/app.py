# File: app.py (or your main Gradio entry point)

import sys
import os
import traceback

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.join(base_dir, "../"))

import argparse
import gradio as gr
import pandas as pd
import os
import logging  # If you want to log

# Local imports
from ui.db.admin_database_handler import AdminDatabaseHandler
from ui.admin_tabs.styling_guide_manager_tab import create_styling_guide_manager_tab
from ui.admin_tabs.provider_manager_tab import create_provider_configuration_tab
from ui.admin_tabs.task_management_tab import create_task_management_tab
from ui.admin_tabs.template_manager_tab import create_prompt_template_management_tab
from ui.admin_tabs.task_mapping_tab import create_task_mapping_tab
from ui.tabs.analytics_tab import create_analytics_tab
from ui.tabs.item_enrichment_tab import create_item_enrichment_tab
from ui.tabs.pricing_analysis_tab import create_pricing_analysis_tab
from ui.tabs.confidence_breakdown_tab import create_confidence_breakdown_tab
from ui.tabs.cq_score_tab import create_cq_score_tab
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

# Leaderboard Tab with multi-metrics + fallback
from ui.tabs.leaderboard_tab import create_leaderboard_tab

from utils import load_product_types_from_file
from bigquery_leaderboard_handler import BigQueryLeaderboardHandler

# Optionally set up GCP creds
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f"{os.getenv('WMT_CA_PATH')}/wmt-rg-dev-sa-rg-gfaas-dev.json"

# Uncomment if you want logs:
# logging.basicConfig(level=logging.DEBUG)

# ------------------------------------------------------------------------------
# Parse command-line arguments
# ------------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Run Gradio application with a specific database path.")
parser.add_argument(
    "--db-path",
    type=str,
    default="/Users/xxx/Workspace/item-setup-playground/results.db",
    help="Path to the SQLite database"
)
args = parser.parse_args()

# ------------------------------------------------------------------------------
# Initialize local DB
# ------------------------------------------------------------------------------
db_handler = DatabaseHandler(db_path=args.db_path)
db_handler.create_tables()

admin_db_handler = AdminDatabaseHandler(db_path=args.db_path)

# ------------------------------------------------------------------------------
# Initialize BigQuery Handler
# ------------------------------------------------------------------------------
project_id = "wmt-rg-dev"  # Replace with your GCP project ID
bq_leaderboard = BigQueryLeaderboardHandler(project_id=project_id)

# ------------------------------------------------------------------------------
# 1) Single "score" aggregator
# ------------------------------------------------------------------------------
def get_leaderboard_bq(**filters):
    """
    Adapts the filter dict from the UI into parameters for BigQueryLeaderboardHandler.
    We only parse 'score' from evaluation_data => returning an avg_score, etc.
    """
    dataset_id = filters.get("dataset_id")
    generation_task = filters.get("generation_task")
    evaluation_task = filters.get("evaluation_task")
    product_type = filters.get("product_type")

    if not dataset_id:
        return pd.DataFrame()

    return bq_leaderboard.get_leaderboard(
        dataset_id=dataset_id,
        generation_task=generation_task,
        evaluation_task=evaluation_task,
        product_type=product_type
    )

# ------------------------------------------------------------------------------
# 2) Multi-metric aggregator
# ------------------------------------------------------------------------------
def get_leaderboard_bq_with_metrics(
    dataset_id: int,
    generation_task: str = None,
    evaluation_task: str = None,
    product_type: str = None,
    metrics: list = None
):
    return bq_leaderboard.get_leaderboard_with_metrics(
        dataset_id=dataset_id,
        generation_task=generation_task,
        evaluation_task=evaluation_task,
        product_type=product_type,
        metrics=metrics
    )

# ------------------------------------------------------------------------------
# 3) Score Buckets aggregator
# ------------------------------------------------------------------------------
def get_leaderboard_bq_with_buckets(
    dataset_id: int,
    generation_task: str = None,
    evaluation_task: str = None,
    product_type: str = None
):
    """
    Calls BigQueryLeaderboardHandler.get_leaderboard_with_buckets, 
    returning a DataFrame of [model_name, model_version, bucket, count_in_bucket].
    E.g. "Bad", "Average", "Good", "Excellent" buckets.
    """
    return bq_leaderboard.get_leaderboard_with_buckets(
        dataset_id=dataset_id,
        generation_task=generation_task,
        evaluation_task=evaluation_task,
        product_type=product_type
    )

# ------------------------------------------------------------------------------
# 4) Retrieve local evaluation_task row for .expected_metrics
# ------------------------------------------------------------------------------
def get_evaluation_task_details(task_name: str):
    row = admin_db_handler.db_session.execute(
        """
        SELECT *
        FROM evaluation_tasks
        WHERE task_name = :task_name
        """,
        {"task_name": task_name}
    ).fetchone()
    return row

# ------------------------------------------------------------------------------
# Load product types
# ------------------------------------------------------------------------------
product_types = load_product_types_from_file('product_types.txt')
if not product_types:
    product_types = ["Electronics", "Clothing", "Home Goods", "Toys", "Books", "Other"]

# ------------------------------------------------------------------------------
# Build Gradio Interface
# ------------------------------------------------------------------------------
with gr.Blocks(css="styles.css") as app:
    gr.Markdown("# Item Setup Playground Interface")

    with gr.Tabs():
        # (1) Item Enrichment Tab
        create_item_enrichment_tab(process_single_sku, save_preference, product_types)

        # (2) Our new Leaderboard Tab
        # We pass all three aggregator fns:
        #   - get_leaderboard_bq_fn (single "score")
        #   - get_leaderboard_with_metrics_fn (multi-metrics)
        #   - get_leaderboard_with_buckets_fn (score buckets)
        create_leaderboard_tab(
            get_leaderboard_bq_fn=get_leaderboard_bq,
            get_leaderboard_with_metrics_fn=get_leaderboard_bq_with_metrics,
            get_leaderboard_with_buckets_fn=get_leaderboard_bq_with_buckets,  # <--- new
            get_evaluation_task_details_fn=get_evaluation_task_details,
            get_datasets_fn=admin_db_handler.get_datasets,
            get_generation_tasks_fn=admin_db_handler.get_generation_tasks,
            get_eval_tasks_for_gen_fn=admin_db_handler.get_evaluation_tasks_for_generation,
            product_types=product_types
        )

        # (3) Analytics Tab
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

        # (4) Admin Tabs
        create_task_management_tab(admin_db_handler)
        create_task_mapping_tab(admin_db_handler)
        create_prompt_template_management_tab(admin_db_handler)
        create_provider_configuration_tab(admin_db_handler)
        create_confidence_breakdown_tab(
            get_datasets_fn=admin_db_handler.get_datasets,
            get_generation_tasks_fn=admin_db_handler.get_generation_tasks,
            get_eval_tasks_for_gen_fn=admin_db_handler.get_evaluation_tasks_for_generation,
            project_id="wmt-rg-dev",
            default_dataset="item_setup_playground",
            product_types=["Shoes","Shirts","All"]
        )
        create_cq_score_tab(
            project_id="wmt-rg-dev",
            default_dataset="item_setup_playground"
        )
        create_pricing_analysis_tab()
        create_styling_guide_manager_tab(admin_db_handler, product_types)

if __name__=="__main__":
    app.launch(enable_queue=False)
