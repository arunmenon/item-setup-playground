# File: ui/tabs/leaderboard_tab.py

import gradio as gr

def create_leaderboard_tab(
    get_leaderboard_bq_fn,        # BigQuery aggregator
    get_datasets_fn,              # e.g. admin_db_handler.get_datasets
    get_generation_tasks_fn,      # e.g. admin_db_handler.get_generation_tasks
    get_eval_tasks_for_gen_fn,    # e.g. admin_db_handler.get_evaluation_tasks_for_generation
    product_types
):
    with gr.TabItem("Leaderboard"):
        gr.Markdown("## Leaderboard")

        # 1. Load datasets from local DB
        dataset_rows = get_datasets_fn()  # e.g. [(1, 'Dataset A', 10), (2, 'Dataset B', 10), (3, 'Dataset X', 11)]
        if not dataset_rows:
            dataset_map = {}
            dataset_labels = ["No Datasets Found"]
        else:
            # Suppose dataset_rows is (dataset_id, name, tenant_id)
            dataset_map = {}
            for ds_id, ds_name, tenant_id in dataset_rows:
                label = f"{ds_name} (Tenant {tenant_id})"
                dataset_map[label] = ds_id
            dataset_labels = list(dataset_map.keys())

        # 2. Load generation tasks from local DB
        gen_tasks = get_generation_tasks_fn()  # e.g. [(1, 'title_enhancement'), (2, 'description_enrichment')]
        if not gen_tasks:
            generation_task_map = {}
            generation_task_labels = ["No Generation Tasks Found"]
        else:
            # We'll map the *name* to the ID so we can easily look up the associated eval tasks
            generation_task_map = {}
            for (g_id, g_name) in gen_tasks:
                generation_task_map[g_name] = g_id
            generation_task_labels = list(generation_task_map.keys())

        with gr.Row():
            # Dataset selector
            dataset_selector = gr.Dropdown(
                label="Dataset",
                choices=dataset_labels,
                value=dataset_labels[0] if dataset_labels else None
            )

            # Generation task selector
            generation_task_selector = gr.Dropdown(
                label="Generation Task",
                choices=generation_task_labels,
                value=generation_task_labels[0] if generation_task_labels else None
            )

            # We'll fill evaluation tasks dynamically
            evaluation_task_selector = gr.Dropdown(
                label="Evaluation Task",
                choices=["All"],
                value="All"
            )

            # Product type selector
            product_type_selector = gr.Dropdown(
                label="Product Type",
                choices=["All"] + product_types,
                value="All"
            )

        leaderboard_output = gr.Dataframe()

        # 3. Populate evaluation tasks whenever generation task changes
        def update_evaluation_tasks(gen_task_name):
            if gen_task_name in [None, "No Generation Tasks Found"]:
                return gr.update(choices=["All"], value="All")

            # Convert name -> ID
            gen_task_id = generation_task_map[gen_task_name]
            eval_tasks = get_eval_tasks_for_gen_fn(gen_task_id)
            if not eval_tasks:
                # Means no eval tasks are associated, so just "All"
                return gr.update(choices=["All"], value="All")

            # We only care about the names
            eval_task_names = [et_name for (et_id, et_name) in eval_tasks]
            return gr.update(choices=["All"] + eval_task_names, value="All")

        generation_task_selector.change(
            fn=update_evaluation_tasks,
            inputs=[generation_task_selector],
            outputs=[evaluation_task_selector]
        )

        # 4. Refresh the leaderboard whenever any dropdown changes
        def refresh_leaderboard(dataset_label, gen_task_name, eval_task_name, product_type):
            # Convert dataset label -> ID
            if not dataset_label or dataset_label == "No Datasets Found":
                return None
            dataset_id = dataset_map[dataset_label]

            # If generation tasks are missing, skip
            if gen_task_name == "No Generation Tasks Found":
                return None

            # If eval_task_name is "All", pass None
            if eval_task_name == "All":
                eval_task_name = None

            # If product_type is "All", pass None
            if product_type == "All":
                product_type = None

            # Now call BQ aggregator
            leaderboard_df = get_leaderboard_bq_fn(
                dataset_id=dataset_id,
                generation_task=gen_task_name,
                evaluation_task=eval_task_name,
                product_type=product_type
            )
            return leaderboard_df

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
