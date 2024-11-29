from ui.components.ui_components import generate_confidence_level_breakdown, generate_variance_distribution_plot


import gradio as gr
import plotly.graph_objects as go


def create_analytics_tab(
    generate_leaderboard_plot_fn,
    get_leaderboard_fn,
    generate_winner_model_comparison_plot_fn,
    get_evaluations_fn,
    get_aggregated_evaluations_fn,
    generate_aggregated_plot_fn,
    product_types
):
    with gr.TabItem("Analytics"):
        gr.Markdown("## Analytics")

        # Filters
        with gr.Row():
            task_selector = gr.Dropdown(
                label="Task",
                choices=["All", "title_enhancement", "description_enrichment"],
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
                "Aggregated Metrics",
                "Variance Distribution",
                "Confidence Level Breakdown"
            ],
            value="Leaderboard"
        )

        analytics_plot = gr.Plot()

        def update_analytics(task, product_type, data_type, visualization):
            task_filter = None if task == "All" else task
            product_type_filter = None if product_type == "All" else product_type

            if data_type == "Individual Evaluations":
                if visualization == "Leaderboard":
                    leaderboard_df = get_leaderboard_fn(task_filter, product_type_filter)
                    plot = generate_leaderboard_plot_fn(leaderboard_df)
                elif visualization == "Winner Model Comparison":
                    evaluation_df = get_evaluations_fn(task=task_filter, product_type=product_type_filter)
                    plot = generate_winner_model_comparison_plot_fn(evaluation_df)
                else:
                    plot = go.Figure()
            elif data_type == "Aggregated Evaluations":
                aggregated_df = get_aggregated_evaluations_fn(task_filter, product_type_filter)
                if visualization == "Aggregated Metrics":
                    plot = generate_aggregated_plot_fn(aggregated_df)
                elif visualization == "Variance Distribution":
                    plot = generate_variance_distribution_plot(aggregated_df)
                elif visualization == "Confidence Level Breakdown":
                    plot = generate_confidence_level_breakdown(aggregated_df)
                else:
                    plot = go.Figure()
            else:
                plot = go.Figure()

            return plot

        inputs = [task_selector, product_type_selector, data_type_selector, visualization_selector]
        for input_component in inputs:
            input_component.change(fn=update_analytics, inputs=inputs, outputs=analytics_plot)