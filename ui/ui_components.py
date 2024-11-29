import gradio as gr
import plotly.graph_objects as go

def create_item_enrichment_tab(process_single_sku_fn, save_preference_fn, product_types, next_index_fn, prev_index_fn):
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

                with gr.TabItem("Title"):
                    model_responses_output_t = gr.Radio(label="Select your preferred response:")

                    gr.Markdown("### Provide Detailed Feedback")
                    with gr.Row():
                        relevance_t = gr.Slider(label="Relevance", minimum=1, maximum=5, step=1, value=3)
                        clarity_t = gr.Slider(label="Clarity", minimum=1, maximum=5, step=1, value=3)
                    with gr.Row():
                        compliance_t = gr.Slider(label="Compliance", minimum=1, maximum=5, step=1, value=3)
                        accuracy_t = gr.Slider(label="Accuracy", minimum=1, maximum=5, step=1, value=3)
                    comments_t = gr.Textbox(label="Additional Comments", placeholder="Enter any additional feedback here...", lines=2)

                    save_btn_t = gr.Button("Save Preference")
                    feedback_output_t = gr.Textbox(label="Feedback", interactive=False)
                    model_responses_json_t = gr.JSON(visible=False)  # Hidden component
                with gr.TabItem("Short Desc"):
                    model_responses_output_sd = gr.Radio(label="Select your preferred response:")

                    gr.Markdown("### Provide Detailed Feedback")
                    with gr.Row():
                        relevance_sd = gr.Slider(label="Relevance", minimum=1, maximum=5, step=1, value=3)
                        clarity_sd = gr.Slider(label="Clarity", minimum=1, maximum=5, step=1, value=3)
                    with gr.Row():
                        compliance_sd = gr.Slider(label="Compliance", minimum=1, maximum=5, step=1, value=3)
                        accuracy_sd = gr.Slider(label="Accuracy", minimum=1, maximum=5, step=1, value=3)
                    comments_sd = gr.Textbox(label="Additional Comments",
                                          placeholder="Enter any additional feedback here...", lines=2)

                    save_btn_sd = gr.Button("Save Preference")
                    feedback_output_sd = gr.Textbox(label="Feedback", interactive=False)
                    model_responses_json_sd = gr.JSON(visible=False)  # Hidden component
                with gr.TabItem("Long Desc"):
                    model_responses_output_ld = gr.Radio(label="Select your preferred response:")

                    gr.Markdown("### Provide Detailed Feedback")
                    with gr.Row():
                        relevance_ld = gr.Slider(label="Relevance", minimum=1, maximum=5, step=1, value=3)
                        clarity_ld = gr.Slider(label="Clarity", minimum=1, maximum=5, step=1, value=3)
                    with gr.Row():
                        compliance_ld = gr.Slider(label="Compliance", minimum=1, maximum=5, step=1, value=3)
                        accuracy_ld = gr.Slider(label="Accuracy", minimum=1, maximum=5, step=1, value=3)
                    comments_ld = gr.Textbox(label="Additional Comments",
                                          placeholder="Enter any additional feedback here...", lines=2)

                    save_btn_ld = gr.Button("Save Preference")
                    feedback_output_ld = gr.Textbox(label="Feedback", interactive=False)
                    model_responses_json_ld = gr.JSON(visible=False)  # Hidden component
                with gr.TabItem("Attribute Enrichment"):
                    attribute_ae = gr.Textbox(label="attribute", interactive=False)
                    model_responses_output_ae = gr.Radio(label="Select your preferred response:")
                    atr_index = gr.State(0)
                    attrwise_model_response = gr.JSON(visible=False)
                    attr_list = gr.State([])

                    gr.Markdown("### Provide Detailed Feedback")
                    with gr.Row():
                        relevance_ae = gr.Slider(label="Relevance", minimum=1, maximum=5, step=1, value=3)
                        clarity_ae = gr.Slider(label="Clarity", minimum=1, maximum=5, step=1, value=3)
                    with gr.Row():
                        compliance_ae = gr.Slider(label="Compliance", minimum=1, maximum=5, step=1, value=3)
                        accuracy_ae = gr.Slider(label="Accuracy", minimum=1, maximum=5, step=1, value=3)
                    comments_ae = gr.Textbox(label="Additional Comments",
                                          placeholder="Enter any additional feedback here...", lines=2)

                    save_btn_ae = gr.Button("Save Preference")
                    feedback_output_ae = gr.Textbox(label="Feedback", interactive=False)
                    model_responses_json_ae = gr.JSON(visible=False)  # Hidden component
                    with gr.Row():
                        prev_btn = gr.Button("Prev")      # input attr_list, atr_index, attrwise_model_response, in case out of bound return max index thing
                        next_btn = gr.Button("Next")      #output would have atr_index, attribute, feedback_output_ae, model_responses_json_ae


        # Define actions for buttons ---- on generate all 4 should be populated with respective values
        generate_btn.click(
            fn=process_single_sku_fn,
            inputs=[gtin, title, short_desc, long_desc, product_type],
            outputs=[model_responses_output_t, model_responses_json_t, feedback_output_t,
                     model_responses_output_sd, model_responses_json_sd, feedback_output_sd,
                     model_responses_output_ld, model_responses_json_ld, feedback_output_ld,
                     model_responses_output_ae, model_responses_json_ae, feedback_output_ae,
                     attribute_ae, attr_list, attrwise_model_response, atr_index]
        )

        save_btn_t.click(
            fn=save_preference_fn,
            inputs=[
                model_responses_output_t,
                model_responses_json_t,
                gtin,
                product_type,
                relevance_t,
                clarity_t,
                compliance_t,
                accuracy_t,
                comments_t,
                gr.State("title_enhancement")
            ],
            outputs=feedback_output_t
        )
        save_btn_sd.click(
            fn=save_preference_fn,
            inputs=[
                model_responses_output_sd,
                model_responses_json_sd,
                gtin,
                product_type,
                relevance_sd,
                clarity_sd,
                compliance_sd,
                accuracy_sd,
                comments_sd,
                gr.State("short_desc_enhancement")
            ],
            outputs=feedback_output_sd
        )
        save_btn_ld.click(
            fn=save_preference_fn,
            inputs=[
                model_responses_output_ld,
                model_responses_json_ld,
                gtin,
                product_type,
                relevance_ld,
                clarity_ld,
                compliance_ld,
                accuracy_ld,
                comments_ld,
                gr.State("long_desc_enhancement")
            ],
            outputs=feedback_output_ld
        )
        save_btn_ae.click(
            fn=save_preference_fn,
            inputs=[
                model_responses_output_ae,
                model_responses_json_ae,
                gtin,
                product_type,
                relevance_ae,
                clarity_ae,
                compliance_ae,
                accuracy_ae,
                comments_ae,
                attribute_ae
            ],
            outputs=feedback_output_ae
        )

        next_btn.click(
            fn=next_index_fn,
            inputs=[atr_index, attr_list, attrwise_model_response],
            outputs=[atr_index, attribute_ae, model_responses_output_ae, model_responses_json_ae]
        )

        prev_btn.click(
            fn=prev_index_fn,
            inputs=[atr_index, attr_list, attrwise_model_response],
            outputs=[atr_index, attribute_ae, model_responses_output_ae, model_responses_json_ae]
        )


def create_leaderboard_tab(get_leaderboard_fn, product_types):
    with gr.TabItem("Leaderboard"):
        gr.Markdown("## Leaderboard")

        with gr.Row():
            task_type_selector = gr.Dropdown(
                label="Select Task Type",
                choices=["All", "title_enhancement", "short_desc_enhancement", "long_desc_enhancement"],
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

def create_feedback_tab(get_detailed_feedback_fn,product_types):
    with gr.TabItem("Detailed Feedback"):
        gr.Markdown("## Feedback Details")

        # Filters
        task_selector = gr.Dropdown(
            label="Select Task Type",
            choices=["All", "title_enhancement", "short_desc_enhancement", "long_desc_enhancement"],
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

def generate_variance_distribution_plot(aggregated_df):
    import plotly.express as px
    import numpy as np
    import pandas as pd

    if aggregated_df.empty:
        return go.Figure()

    metrics = ['quality_score', 'relevance', 'clarity', 'compliance', 'accuracy']
    plot_data = []

    for metric in metrics:
        variance_col = f'{metric}_variance'
        temp_df = aggregated_df[['model_name', variance_col]]
        temp_df = temp_df.rename(columns={variance_col: 'variance'})
        temp_df['Metric'] = metric.capitalize()
        plot_data.append(temp_df)

    plot_df = pd.concat(plot_data, ignore_index=True)

    # Remove rows with NaN variance
    plot_df = plot_df.dropna(subset=['variance'])

    # Create box plot to show variance distribution
    fig = px.box(
        plot_df,
        x='Metric',
        y='variance',
        points='all',
        color='Metric',
        title='Variance Distribution Across Metrics',
        labels={'variance': 'Variance', 'Metric': 'Metric'}
    )

    fig.update_layout(
        xaxis_title='Metric',
        yaxis_title='Variance',
        showlegend=False
    )

    return fig


def generate_confidence_level_breakdown(aggregated_df):
    import plotly.express as px
    import pandas as pd

    if aggregated_df.empty:
        return go.Figure()

    metrics = ['quality_score', 'relevance', 'clarity', 'compliance', 'accuracy']
    plot_data = []

    # Extract confidence levels for each metric
    for metric in metrics:
        confidence_col = f'{metric}_confidence'
        temp_df = aggregated_df[[confidence_col]]
        temp_df = temp_df.rename(columns={confidence_col: 'confidence_level'})
        temp_df['Metric'] = metric.capitalize()
        plot_data.append(temp_df)

    plot_df = pd.concat(plot_data, ignore_index=True)

    # Count of predictions per confidence level and metric
    count_df = plot_df.groupby(['Metric', 'confidence_level']).size().reset_index(name='Count')

    # Calculate totals per metric and merge with count_df
    total_counts = plot_df.groupby('Metric').size().reset_index(name='Total')
    count_df = count_df.merge(total_counts, on='Metric')

    # Calculate percentage and format it
    count_df['Percentage'] = (count_df['Count'] / count_df['Total']) * 100
    count_df['Percentage'] = count_df['Percentage'].map(lambda x: f'{x:.2f}%')

    # Create bar plot
    fig = px.bar(
        count_df,
        x='Metric',
        y='Count',
        color='confidence_level',
        text='Percentage',
        barmode='group',
        title='Percentage of Predictions by Confidence Level and Metric',
        labels={'Count': 'Percentage of Predictions', 'Metric': 'Metric', 'confidence_level': 'Confidence Level'}
    )

    fig.update_layout(
        xaxis_title='Metric',
        yaxis_title='Percentage of Predictions',
        legend_title='Confidence Level'
    )

    return fig

