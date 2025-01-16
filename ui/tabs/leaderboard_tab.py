# File: ui/tabs/leaderboard_tab.py

import gradio as gr

def create_leaderboard_tab(
    get_leaderboard_bq_fn,    # Function that calls BigQueryLeaderboardHandler
    get_evaluation_tasks_fn,  # (Optional) to populate evaluation_task dropdown
    product_types,
    get_datasets_fn           # NEW: retrieve (dataset_id, name, tenant_id) from local DB
):
    with gr.TabItem("Leaderboard"):
        gr.Markdown("## Leaderboard")

        # 1) Build dataset dropdown from local DB
        dataset_rows = get_datasets_fn()  # e.g. [(1, 'Dataset A', 10), (2, 'Dataset B', 11), ...]
        if not dataset_rows:
            dataset_labels = ["No Datasets Found"]
            dataset_map = {}
        else:
            # We'll store them in a dict: { "Dataset A (tenant=10)": (1, 10), ... }
            # or just "Dataset A" -> (1, 10) if you prefer. 
            # This is to show tenant info if you want. Otherwise ignore tenant_id in the label.
            dataset_map = {}
            for ds_id, ds_name, tenant_id in dataset_rows:
                label = f"{ds_name} (Tenant {tenant_id})"
                dataset_map[label] = (ds_id, tenant_id)

            dataset_labels = list(dataset_map.keys())

        with gr.Row():
            dataset_selector = gr.Dropdown(
                label="Dataset",
                choices=dataset_labels,
                value=dataset_labels[0] if dataset_labels else None
            )

            generation_task_selector = gr.Dropdown(
                label="Generation Task",
                choices=["All", "title_enhancement", "description_enrichment"],
                value="All"
            )
            evaluation_task_selector = gr.Dropdown(
                label="Evaluation Task",
                choices=["All"],  # Updated dynamically by update_evaluation_tasks
                value="All"
            )
            product_type_selector = gr.Dropdown(
                label="Product Type",
                choices=["All"] + product_types,
                value="All"
            )

        evaluator_type_selector = gr.Dropdown(
            label="Evaluator Type",
            choices=["All", "LLM", "Human"],
            value="All"
        )

        leaderboard_output = gr.Dataframe()

        def update_evaluation_tasks(generation_task):
            """
            If generation_task == 'All', we show all tasks. Otherwise, get tasks for that generation_task.
            """
            if generation_task == "All":
                eval_tasks = get_evaluation_tasks_fn()
            else:
                eval_tasks = get_evaluation_tasks_fn(generation_task)
            return gr.update(choices=["All"] + eval_tasks, value="All")

        generation_task_selector.change(
            fn=update_evaluation_tasks,
            inputs=[generation_task_selector],
            outputs=[evaluation_task_selector]
        )

        def refresh_leaderboard(
            dataset_label,
            generation_task,
            evaluation_task,
            product_type,
            evaluator_type
        ):
            if not dataset_label or dataset_label == "No Datasets Found":
                return None

            # 2) Convert the selected dataset label -> (dataset_id, tenant_id)
            ds_id, tenant_id = dataset_map[dataset_label]

            # Collect filters for BQ
            filters = {
                "dataset_id": ds_id,
                "generation_task": None if generation_task == "All" else generation_task,
                "product_type": None if product_type == "All" else product_type,
                "evaluation_task": None if evaluation_task == "All" else evaluation_task,
                "evaluator_type": None if evaluator_type == "All" else evaluator_type,
            }

            # 3) Call BigQuery function (we only pass what it actually needs)
            leaderboard_df = get_leaderboard_bq_fn(
                dataset_id=filters["dataset_id"],
                product_type=filters["product_type"],
                generation_task=filters["generation_task"]
            )

            return leaderboard_df

        inputs = [
            dataset_selector,
            generation_task_selector,
            evaluation_task_selector,
            product_type_selector,
            evaluator_type_selector
        ]
        for inp in inputs:
            inp.change(
                fn=refresh_leaderboard,
                inputs=inputs,
                outputs=leaderboard_output
            )
