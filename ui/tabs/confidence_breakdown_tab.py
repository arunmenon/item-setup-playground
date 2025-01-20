# File: confidence_breakdown_tab.py

import os
import json
import logging

import gradio as gr
import plotly.express as px
import pandas as pd
from google.cloud import bigquery

class ConfidenceBreakdownHandler:
    """
    Minimal aggregator class for demonstration.
    Connects to BigQuery, runs a single query on 'aggregated_evaluations' table 
    grouping by (model_name, metric_confidence).
    """

    def __init__(self, project_id: str, dataset: str = "item_setup_playground"):
        self.client = bigquery.Client(project=project_id)
        self.dataset = dataset

    def get_confidence_breakdown(
        self,
        dataset_id: int,
        generation_task: str = None,
        evaluation_task: str = None,
        product_type: str = None
    ) -> pd.DataFrame:
        """
        Queries aggregated_evaluations for confidence breakdown, returning:
          model_name, model_version, metric_confidence, count_confidence
        """
        table = f"`{self.client.project}.{self.dataset}.aggregated_evaluations`"

        query = f"""
        SELECT
          model_name,
          model_version,
          metric_confidence AS confidence_level,
          COUNT(*) AS count_confidence
        FROM {table}
        WHERE dataset_id = @dataset_id
        """

        if generation_task and generation_task != "All":
            query += " AND generation_task = @generation_task"
        if evaluation_task and evaluation_task != "All":
            query += " AND evaluation_task = @evaluation_task"
        if product_type and product_type != "All":
            query += " AND item_product_type = @product_type"

        query += """
        GROUP BY
          model_name, model_version, metric_confidence
        ORDER BY
          model_name, metric_confidence
        """

        params = [
            bigquery.ScalarQueryParameter("dataset_id", "INT64", dataset_id)
        ]
        if generation_task and generation_task != "All":
            params.append(bigquery.ScalarQueryParameter("generation_task", "STRING", generation_task))
        if evaluation_task and evaluation_task != "All":
            params.append(bigquery.ScalarQueryParameter("evaluation_task", "STRING", evaluation_task))
        if product_type and product_type != "All":
            params.append(bigquery.ScalarQueryParameter("product_type", "STRING", product_type))

        logging.debug("confidence breakdown query:\n%s", query)
        logging.debug("params: %s", params)

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        df = self.client.query(query, job_config=job_config).to_dataframe()
        return df

def create_confidence_breakdown_tab(
    get_datasets_fn,
    get_generation_tasks_fn,
    get_eval_tasks_for_gen_fn,
    project_id: str,
    default_dataset="item_setup_playground",
    product_types=None
):
    """
    Creates a new Gradio tab: "Confidence Breakdown"
    - We do the typical dataset, generation task, eval task, product type pickers
    - Then we call ConfidenceBreakdownHandler to get a stacked bar chart of confidence levels
    """

    if product_types is None:
        product_types = ["All", "Clothing", "Electronics", "Toys"]

    # We'll instantiate a local aggregator
    aggregator = ConfidenceBreakdownHandler(project_id=project_id, dataset=default_dataset)

    with gr.TabItem("Confidence Breakdown"):
        gr.Markdown("## Confidence Breakdown at Model Level")

        # 1) Load Datasets from local DB
        dataset_rows = get_datasets_fn()  # e.g. [(1, 'Dataset A', 10), (2, 'Dataset B', 11)]
        if not dataset_rows:
            dataset_map = {}
            dataset_labels = ["No Datasets Found"]
        else:
            dataset_map = {}
            for ds_id, ds_name, tenant_id in dataset_rows:
                label = f"{ds_name} (Tenant {tenant_id})"
                dataset_map[label] = ds_id
            dataset_labels = list(dataset_map.keys())

        # 2) Load Generation Tasks
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

        # The output: a DataFrame + a Plot
        confidence_df = gr.Dataframe()
        confidence_plot = gr.Plot()

        # We'll populate evaluation task on generation_task change
        def update_evaluation_tasks(gen_task_name):
            if not gen_task_name or gen_task_name == "No Generation Tasks Found":
                return gr.update(choices=["All"], value="All")
            # map name -> id
            gen_task_id = generation_task_map[gen_task_name]
            eval_tasks = get_eval_tasks_for_gen_fn(gen_task_id)
            if not eval_tasks:
                return gr.update(choices=["All"], value="All")
            eval_names = [et_name for (et_id, et_name) in eval_tasks]
            return gr.update(choices=["All"] + eval_names, value="All")

        generation_task_selector.change(
            fn=update_evaluation_tasks,
            inputs=[generation_task_selector],
            outputs=[evaluation_task_selector]
        )

        # main callback
        def refresh_confidence_breakdown(dataset_label, gen_task_name, eval_task_name, product_type):
            # convert dataset_label -> dataset_id
            if not dataset_label or dataset_label=="No Datasets Found":
                return None, None

            dataset_id = dataset_map[dataset_label]

            # convert "All" to None
            if gen_task_name=="No Generation Tasks Found":
                return None, None
            if eval_task_name=="All":
                eval_task_name = None
            if product_type=="All":
                product_type = None

            # call aggregator
            df = aggregator.get_confidence_breakdown(
                dataset_id=dataset_id,
                generation_task=gen_task_name,
                evaluation_task=eval_task_name,
                product_type=product_type
            )
            if df is None or df.empty:
                return df, None

            # we expect: model_name, model_version, confidence_level, count_confidence
            fig = px.bar(
                df,
                x="model_name",
                y="count_confidence",
                color="confidence_level",
                barmode="stack",
                title="Confidence Breakdown by Model"
            )
            return df, fig

        # whenever inputs change, call refresh
        inputs = [dataset_selector, generation_task_selector, evaluation_task_selector, product_type_selector]
        for inp in inputs:
            inp.change(
                fn=refresh_confidence_breakdown,
                inputs=inputs,
                outputs=[confidence_df, confidence_plot]
            )
