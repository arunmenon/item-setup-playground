# File: ui/tabs/leaderboard_tab.py

import gradio as gr
import json

def create_leaderboard_tab(
    get_leaderboard_bq_fn,            # Original "score-based" aggregator
    get_leaderboard_with_metrics_fn,  # NEW aggregator for multi-metrics
    get_datasets_fn,
    get_generation_tasks_fn,
    get_eval_tasks_for_gen_fn,
    get_evaluation_task_details_fn,   # function to fetch the row from local DB for an evaluation task
    product_types
):
    with gr.TabItem("Leaderboard"):
        gr.Markdown("## Leaderboard (Multi-metric)")

        # 1. Load datasets from local DB
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

        # 2. Generation tasks
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

        leaderboard_output = gr.Dataframe()

        # 3. Populate evaluation tasks whenever generation task changes
        def update_evaluation_tasks(gen_task_name):
            if not gen_task_name or gen_task_name == "No Generation Tasks Found":
                return gr.update(choices=["All"], value="All")
            gen_task_id = generation_task_map[gen_task_name]
            eval_tasks = get_eval_tasks_for_gen_fn(gen_task_id)
            if not eval_tasks:
                return gr.update(choices=["All"], value="All")
            eval_task_names = [et_name for (et_id, et_name) in eval_tasks]
            return gr.update(choices=["All"] + eval_task_names, value="All")

        generation_task_selector.change(
            fn=update_evaluation_tasks,
            inputs=[generation_task_selector],
            outputs=[evaluation_task_selector]
        )

        # 4. Refresh the leaderboard
        def refresh_leaderboard(dataset_label, gen_task_name, eval_task_name, product_type):
            if not dataset_label or dataset_label == "No Datasets Found":
                return None
            dataset_id = dataset_map[dataset_label]

            if gen_task_name == "No Generation Tasks Found":
                return None

            # Convert "All" to None
            if eval_task_name == "All":
                eval_task_name = None
            if product_type == "All":
                product_type = None

            # If we have a real evaluation task chosen, see if it has custom metrics
            metrics_list = None
            if eval_task_name:
                # load the evaluation task details from local DB
                task_row = get_evaluation_task_details_fn(eval_task_name)  # returns an object or dict
                if task_row and task_row.expected_metrics:
                    em = json.loads(task_row.expected_metrics)  # { "metrics": [ {name, type}, ... ] }
                    metrics_list = em.get("metrics", [])

            # If we have metrics_list (and not empty), use get_leaderboard_with_metrics
            if metrics_list:
                df = get_leaderboard_with_metrics_fn(
                    dataset_id=dataset_id,
                    generation_task=gen_task_name,
                    evaluation_task=eval_task_name,
                    product_type=product_type,
                    metrics=metrics_list
                )
                return df
            else:
                # fallback to simple "score" aggregator
                df = get_leaderboard_bq_fn(
                    dataset_id=dataset_id,
                    generation_task=gen_task_name,
                    evaluation_task=eval_task_name,
                    product_type=product_type
                )
                return df

        inputs = [
            dataset_selector,
            generation_task_selector,
            evaluation_task_selector,
            product_type_selector
        ]
        for inp in inputs:
            inp.change(
                fn=refresh_leaderboard,
                inputs=inputs,
                outputs=leaderboard_output
            )
