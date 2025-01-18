# File: ui/tabs/leaderboard_tab.py

import gradio as gr
import json
import logging
import plotly.express as px

def create_leaderboard_tab(
    get_leaderboard_bq_fn,
    get_leaderboard_with_metrics_fn,
    get_leaderboard_with_buckets_fn,  # NEW aggregator for buckets
    get_datasets_fn,
    get_generation_tasks_fn,
    get_eval_tasks_for_gen_fn,
    get_evaluation_task_details_fn,
    product_types
):
    with gr.TabItem("Leaderboard"):
        gr.Markdown("## Leaderboard (Multi-metric + Score Buckets)")

        # 1) Load Datasets
        dataset_rows = get_datasets_fn()
        if not dataset_rows:
            dataset_map = {}
            dataset_labels = ["No Datasets Found"]
        else:
            dataset_map = {}
            for ds_id, ds_name, tenant_id in dataset_rows:
                label = f"{ds_name} (Tenant {tenant_id})"
                dataset_map[label] = ds_id
            dataset_labels = list(dataset_map.keys())

        # 2) Generation tasks
        gen_tasks = get_generation_tasks_fn()
        if not gen_tasks:
            generation_task_map = {}
            generation_task_labels = ["No Generation Tasks Found"]
        else:
            generation_task_map = {}
            for (g_id, g_name) in gen_tasks:
                generation_task_map[g_name] = g_id
            generation_task_labels = list(generation_task_map.keys())

        with gr.Row():
            dataset_selector = gr.Dropdown(
                label="Dataset",
                choices=dataset_labels,
                value=dataset_labels[0] if dataset_labels else None
            )
            generation_task_selector = gr.Dropdown(
                label="Generation Task",
                choices=generation_task_labels,
                value=generation_task_labels[0] if generation_task_labels else None
            )
            evaluation_task_selector = gr.Dropdown(
                label="Evaluation Task",
                choices=["All"],
                value="All"
            )
            product_type_selector = gr.Dropdown(
                label="Product Type",
                choices=["All"] + product_types,
                value="All"
            )

        # Visualization dropdown
        visualization_selector = gr.Dropdown(
            label="Visualization",
            choices=[
                "Table",
                "Bar Chart by Model",
                "Bar Chart by Product Type",
                "Pie Chart by Model (Count)",
                "Score Buckets (Stacked Bar)"  # <--- new!
            ],
            value="Table"
        )

        leaderboard_df = gr.Dataframe()
        leaderboard_plot = gr.Plot()

        def update_evaluation_tasks(gen_task_name):
            if not gen_task_name
