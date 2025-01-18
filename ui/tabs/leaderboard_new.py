# File: ui/tabs/leaderboard_tab.py

import gradio as gr
import json
import logging
import plotly.express as px

def create_leaderboard_tab(
    get_leaderboard_bq_fn,            # Single "score" aggregator
    get_leaderboard_with_metrics_fn,  # Multi-metric aggregator
    get_leaderboard_with_buckets_fn,  # Bucket-based aggregator (score distribution)
    get_datasets_fn,
    get_generation_tasks_fn,
    get_eval_tasks_for_gen_fn,
    get_evaluation_task_details_fn,
    product_types
):
    """
    Creates a 'Leaderboard' tab in Gradio that:
    1) Loads Datasets, Gen Tasks, and populates an Evaluation Task dropdown dynamically.
    2) Lets the user pick Product Type and Visualization.
    3) Calls one of three aggregator functions:
       - Single "score" aggregator,
       - Multi-metric aggregator,
       - Bucket aggregator (Score Buckets).
    4) Displays the result in a DataFrame plus a Plotly chart (if visualization != "Table").
    """

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

        # UI components for dataset/gen_task/eval_task/product_type
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
                "Score Buckets (Stacked Bar)"
            ],
            value="Table"
        )

        # We'll display a DataFrame plus a Plot
        leaderboard_df = gr.Dataframe()
        leaderboard_plot = gr.Plot()

        # A) Populate evaluation tasks whenever generation task changes
        def update_evaluation_tasks(gen_task_name):
            """
            Called if the user picks a new Generation Task. 
            We'll load evaluation tasks mapped to that gen_task_id.
            """
            if not gen_task_name or gen_task_name == "No Generation Tasks Found":
                return gr.update(choices=["All"], value="All")
            # Map the gen task name -> gen_task_id
            gen_task_id = generation_task_map[gen_task_name]
            # Fetch all evaluation tasks for that generation task
            eval_tasks = get_eval_tasks_for_gen_fn(gen_task_id)
            if not eval_tasks:
                return gr.update(choices=["All"], value="All")
            # We only care about their names
            eval_task_names = [et_name for (et_id, et_name) in eval_tasks]
            return gr.update(choices=["All"] + eval_task_names, value="All")

        generation_task_selector.change(
            fn=update_evaluation_tasks,
            inputs=[generation_task_selector],
            outputs=[evaluation_task_selector]
        )

        # B) The main callback that fetches data & builds a chart
        def refresh_leaderboard(dataset_label, gen_task_name, eval_task_name, product_type, visualization):
            logging.debug(
                "refresh_leaderboard => dataset=%s, gen_task=%s, eval_task=%s, product_type=%s, viz=%s",
                dataset_label, gen_task_name, eval_task_name, product_type, visualization
            )

            # 1) Check dataset & generation task
            if not dataset_label or dataset_label == "No Datasets Found":
                return None, None
            dataset_id = dataset_map[dataset_label]

            if gen_task_name == "No Generation Tasks Found":
                return None, None

            # 2) Convert "All" to None
            if eval_task_name == "All":
                eval_task_name = None
            if product_type == "All":
                product_type = None

            # 3) See if chosen eval task has custom metrics in expected_metrics
            metrics_list = None
            if eval_task_name:
                task_row = get_evaluation_task_details_fn(eval_task_name)
                if task_row and task_row.expected_metrics:
                    try:
                        em = json.loads(task_row.expected_metrics)
                        if isinstance(em, str):
                            # double-encoded scenario
                            em = json.loads(em)
                        metrics_list = em.get("metrics", [])
                    except:
                        metrics_list = []

            # 4) aggregator calls
            df = None
            fig = None

            if visualization == "Score Buckets (Stacked Bar)":
                # We specifically call the "bucket aggregator"
                df = get_leaderboard_with_buckets_fn(
                    dataset_id=dataset_id,
                    generation_task=gen_task_name,
                    evaluation_task=eval_task_name,
                    product_type=product_type
                )
                if df is None or df.empty:
                    return df, None
                # Suppose the DF has: model_name, model_version, bucket, count_in_bucket
                fig = px.bar(
                    df,
                    x="model_name",         # each model on x-axis
                    y="count_in_bucket",    # how many items in that bucket
                    color="bucket",         # bucket categories
                    barmode="stack",
                    title="Quality Score Buckets by Model"
                )
                return df, fig

            # If not Score Buckets, we do either multi-metric or single aggregator
            if metrics_list:
                df = get_leaderboard_with_metrics_fn(
                    dataset_id=dataset_id,
                    generation_task=gen_task_name,
                    evaluation_task=eval_task_name,
                    product_type=product_type,
                    metrics=metrics_list
                )
            else:
                df = get_leaderboard_bq_fn(
                    dataset_id=dataset_id,
                    generation_task=gen_task_name,
                    evaluation_task=eval_task_name,
                    product_type=product_type
                )

            # If empty data
            if df is None or df.empty:
                return df, None

            # 5) Build a Plotly figure if user picks a chart
            if visualization == "Table":
                pass  # no figure
            else:
                # If aggregator returned e.g. "avg_score" or "avg_quality_score" columns, 
                # we'll pick the first to use as y
                numeric_cols = [c for c in df.columns if c.startswith("avg_")]
                ycol = numeric_cols[0] if numeric_cols else "num_evaluations"

                if visualization == "Bar Chart by Model":
                    if "model_name" in df.columns:
                        fig = px.bar(
                            df,
                            x="model_name",
                            y=ycol,
                            color="model_name",
                            title=f"Bar Chart by Model ({ycol})"
                        )
                elif visualization == "Bar Chart by Product Type":
                    if "item_product_type" in df.columns:
                        fig = px.bar(
                            df,
                            x="item_product_type",
                            y=ycol,
                            color="item_product_type",
                            title=f"Bar Chart by Product Type ({ycol})"
                        )
                elif visualization == "Pie Chart by Model (Count)":
                    if "model_name" in df.columns and "num_evaluations" in df.columns:
                        fig = px.pie(
                            df,
                            names="model_name",
                            values="num_evaluations",
                            title="Pie: #Evaluations by Model"
                        )

            return df, fig

        def unified_callback(*args):
            # unify the outputs => (df, fig)
            df, fig = refresh_leaderboard(*args)
            return df, fig

        # C) Whenever any dropdown changes, we call 'unified_callback' => (df, fig)
        all_inputs = [
            dataset_selector,
            generation_task_selector,
            evaluation_task_selector,
            product_type_selector,
            visualization_selector
        ]
        for inp in all_inputs:
            inp.change(
                fn=unified_callback,
                inputs=all_inputs,
                outputs=[leaderboard_df, leaderboard_plot]
            )
