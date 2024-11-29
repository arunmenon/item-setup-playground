import gradio as gr


def create_leaderboard_tab(get_leaderboard_fn, product_types):
    with gr.TabItem("Leaderboard"):
        gr.Markdown("## Leaderboard")

        with gr.Row():
            task_type_selector = gr.Dropdown(
                label="Select Task Type",
                choices=["All", "title_enhancement", "description_enrichment"],
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

        def refresh_leaderboard(task, product_type, evaluator_type):
            task_filter = None if task == "All" else task
            product_type_filter = None if product_type == "All" else product_type
            evaluator_type_filter = None if evaluator_type == "All" else evaluator_type
            return get_leaderboard_fn(task_filter, product_type_filter, evaluator_type_filter)

        inputs = [task_type_selector, product_type_selector, evaluator_type_selector]
        for input_component in inputs:
            input_component.change(fn=refresh_leaderboard, inputs=inputs, outputs=leaderboard_output)