import gradio as gr
import plotly.graph_objects as go

def create_item_enrichment_tab(process_single_sku_fn, save_preference_fn, product_types):
    with gr.TabItem("Item Enrichment"):
        gr.Markdown("## Enter Product Information")
        with gr.Row():
            # Left Column: Input Fields
            with gr.Column():
                gtin = gr.Textbox(label="GTIN", placeholder="Enter GTIN", max_lines=1)
                product_type = gr.Dropdown(
                    label="Product Type",
                    choices=product_types,
                    value=None
                )
                title = gr.Textbox(label="Title", placeholder="Enter Title", lines=1)
                short_desc = gr.Textbox(label="Short Description", placeholder="Enter Short Description", lines=2)
                long_desc = gr.Textbox(label="Long Description", placeholder="Enter Long Description", lines=3)
                generate_btn = gr.Button("Generate Enrichment")
            # Right Column: Generated Enrichments and Feedback
            with gr.Column():
                gr.Markdown("### Generated Enrichments")
                model_responses_output = gr.Radio(label="Select your preferred response:")

                gr.Markdown("### Provide Detailed Feedback")
                with gr.Row():
                    relevance = gr.Slider(label="Relevance", minimum=1, maximum=5, step=1, value=3)
                    clarity = gr.Slider(label="Clarity", minimum=1, maximum=5, step=1, value=3)
                with gr.Row():
                    compliance = gr.Slider(label="Compliance", minimum=1, maximum=5, step=1, value=3)
                    accuracy = gr.Slider(label="Accuracy", minimum=1, maximum=5, step=1, value=3)
                comments = gr.Textbox(label="Additional Comments", placeholder="Enter any additional feedback here...", lines=2)

                save_btn = gr.Button("Save Preference")
                feedback_output = gr.Textbox(label="Feedback", interactive=False)
                model_responses_json = gr.JSON(visible=False)  # Hidden component

        # Define actions for buttons
        generate_btn.click(
            fn=process_single_sku_fn,
            inputs=[gtin, title, short_desc, long_desc, product_type],
            outputs=[model_responses_output, model_responses_json, feedback_output]
        )

        save_btn.click(
            fn=save_preference_fn,
            inputs=[
                model_responses_output,
                model_responses_json,
                gtin,
                product_type,
                relevance,
                clarity,
                compliance,
                accuracy,
                comments
            ],
            outputs=feedback_output
        )


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

        

def create_analytics_tab(generate_leaderboard_plot_fn, get_leaderboard_fn, generate_winner_model_comparison_plot_fn,get_evaluations_fn, product_types):
    with gr.TabItem("Analytics"):
        gr.Markdown("## Analytics")

        # Filters
        with gr.Row():
            task_type_selector = gr.Dropdown(
                label="Task",
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

        visualization_selector = gr.Dropdown(
            label="Select Visualization",
            choices=["Leaderboard", "Winner Model Comparison"],
            value="Leaderboard"
        )

        analytics_plot = gr.Plot()

        def update_analytics(task, product_type, evaluator_type, visualization):
            task_filter = None if task == "All" else task
            product_type_filter = None if product_type == "All" else product_type
            evaluator_type_filter = None if evaluator_type == "All" else evaluator_type

            if visualization == "Leaderboard":
                leaderboard_df = get_leaderboard_fn(task_filter, product_type_filter, evaluator_type_filter)
                plot = generate_leaderboard_plot_fn(leaderboard_df)
            elif visualization == "Winner Model Comparison":
                evaluation_df = get_evaluations_fn(task=task_filter, product_type=product_type_filter)
                plot = generate_winner_model_comparison_plot_fn(evaluation_df)
            else:
                plot = go.Figure()

            return plot

        inputs = [task_type_selector, product_type_selector, evaluator_type_selector, visualization_selector]
        for input_component in inputs:
            input_component.change(fn=update_analytics, inputs=inputs, outputs=analytics_plot)

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