import gradio as gr


def create_feedback_tab(get_detailed_feedback_fn,product_types):
    with gr.TabItem("Detailed Feedback"):
        gr.Markdown("## Feedback Details")

        # Filters
        task_selector = gr.Dropdown(
            label="Task",
            choices=["All", "title_enhancement", "description_enhancement"],
            value="All"
        )
        item_selector = gr.Textbox(
            label="Item ID",
            placeholder="Enter Item ID (optional)"
        )
        product_type_selector = gr.Dropdown(
            label="Product Type",
            choices=product_types,
            value="All"
        )
        model_selector = gr.Textbox(
            label="Model Name",
            placeholder="Enter Model Name (optional)"
        )

        # Feedback table
        # Feedback table
        feedback_table = gr.Dataframe(headers=[
            "Item ID", "Product Type", "Task", "Model Name", "Model Version",
            "Quality Score", "Reasoning", "Suggestions", "Is Winner"
        ])


        def load_feedback(task, item_id, product_type, model_name):
            task_filter = None if task == "All" else task
            product_type_filter = None if product_type == "All" else product_type
            return get_detailed_feedback_fn(
                task=task_filter,
                item_id=item_id if item_id else None,
                product_type=product_type_filter,
                model_name=model_name if model_name else None
            )

        # Trigger on filter changes
        inputs = [task_selector, item_selector, product_type_selector, model_selector]
        for input_component in inputs:
            input_component.change(fn=load_feedback, inputs=inputs, outputs=feedback_table)