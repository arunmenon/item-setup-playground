import gradio as gr

def create_leaderboard_tab(get_leaderboard_fn, get_evaluation_tasks_fn, product_types):
    with gr.TabItem("Leaderboard"):
        gr.Markdown("## Leaderboard")

        with gr.Row():
            generation_task_selector = gr.Dropdown(
                label="Generation Task",
                choices=["All", "title_enhancement", "description_enrichment"],
                value="All"
            )
            evaluation_task_selector = gr.Dropdown(
                label="Evaluation Task",
                choices=["All"],  # To be updated based on generation task
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

        def refresh_leaderboard(generation_task, evaluation_task, product_type, evaluator_type):
            filters = {}
            if generation_task != "All":
                filters['generation_task'] = generation_task
            if evaluation_task != "All":
                filters['evaluation_task'] = evaluation_task
            if product_type != "All":
                filters['item_product_type'] = product_type
            if evaluator_type != "All":
                filters['evaluator_type'] = evaluator_type

            leaderboard_df = get_leaderboard_fn(**filters)
            return leaderboard_df

        inputs = [generation_task_selector, evaluation_task_selector, product_type_selector, evaluator_type_selector]
        for input_component in inputs:
            input_component.change(fn=refresh_leaderboard, inputs=inputs, outputs=leaderboard_output)
