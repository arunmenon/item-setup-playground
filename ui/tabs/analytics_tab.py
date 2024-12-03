from ui.components.ui_components import generate_confidence_level_breakdown, generate_variance_distribution_plot


import gradio as gr
import plotly.graph_objects as go


import gradio as gr
import plotly.graph_objects as go

def create_analytics_tab(
    generate_leaderboard_plot_fn,
    get_leaderboard_fn,
    generate_winner_model_comparison_plot_fn,
    get_evaluations_fn,
    get_aggregated_evaluations_fn,
    generate_aggregated_plot_fn,
    generate_variance_distribution_plot_fn,
    generate_confidence_level_breakdown_fn,
    get_evaluation_tasks_fn,
    product_types
):
    with gr.TabItem("Analytics"):
        gr.Markdown("## Analytics")

        # Filters
        with gr.Row():
            generation_task_selector = gr.Dropdown(
                label="Generation Task",
                choices=["All", "title_enhancement", "description_enrichment"],
                value="All"
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
            data_type_selector = gr.Dropdown(
                label="Data Type",
                choices=["Individual Evaluations", "Aggregated Evaluations"],
                value="Individual Evaluations"
            )

        visualization_selector = gr.Dropdown(
            label="Select Visualization",
            choices=[
                "Leaderboard",
                "Winner Model Comparison",
                "Metric Distribution",
                "Aggregated Metrics",
                "Variance Distribution",
                "Confidence Level Breakdown"
            ],
            value="Leaderboard"
        )

        analytics_plot = gr.Plot()

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

        def update_analytics(generation_task, evaluation_task, product_type, data_type, visualization):
            filters = {}
            if generation_task != "All":
                filters['generation_task'] = generation_task
            if evaluation_task != "All":
                filters['evaluation_task'] = evaluation_task
            if product_type != "All":
                filters['item_product_type'] = product_type

            if data_type == "Individual Evaluations":
                if visualization == "Leaderboard":
                    leaderboard_df = get_leaderboard_fn(**filters)
                    plot = generate_leaderboard_plot_fn(leaderboard_df)
                elif visualization == "Winner Model Comparison":
                    evaluation_df = get_evaluations_fn(**filters)
                    plot = generate_winner_model_comparison_plot_fn(evaluation_df)
                elif visualization == "Metric Distribution":
                    evaluation_df = get_evaluations_fn(**filters)
                    plot = generate_metric_distribution_plot(evaluation_df)
                else:
                    plot = go.Figure()
            elif data_type == "Aggregated Evaluations":
                aggregated_df = get_aggregated_evaluations_fn(**filters)
                if visualization == "Aggregated Metrics":
                    plot = generate_aggregated_plot_fn(aggregated_df)
                elif visualization == "Variance Distribution":
                    plot = generate_variance_distribution_plot_fn(aggregated_df)
                elif visualization == "Confidence Level Breakdown":
                    plot = generate_confidence_level_breakdown_fn(aggregated_df)
                else:
                    plot = go.Figure()
            else:
                plot = go.Figure()

            return plot

        inputs = [
            generation_task_selector,
            evaluation_task_selector,
            product_type_selector,
            data_type_selector,
            visualization_selector
        ]
        for input_component in inputs:
            input_component.change(fn=update_analytics, inputs=inputs, outputs=analytics_plot)
