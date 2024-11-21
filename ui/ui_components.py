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
                    value=None  # No default selection
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


def create_leaderboard_tab(get_leaderboard_fn):
    with gr.TabItem("Leaderboard"):
        gr.Markdown("## Leaderboard")
        task_type_selector = gr.Dropdown(
            label="Select Task Type",
            choices=["All", "title_enhancement", "short_desc_enhancement", "long_desc_enhancement"],
            value="All"
        )
        refresh_button = gr.Button("Refresh Data")
        leaderboard_output = gr.Dataframe()

        # Define the refresh function
        def refresh_leaderboard(selected_task_type):
            updated_leaderboard_data = get_leaderboard_fn()
            if not updated_leaderboard_data.empty and selected_task_type != "All":
                updated_leaderboard_data = updated_leaderboard_data[updated_leaderboard_data["task_type"] == selected_task_type]
            return updated_leaderboard_data

        # Action for refresh button
        refresh_button.click(
            fn=refresh_leaderboard,
            inputs=[task_type_selector],
            outputs=leaderboard_output
        )

def create_analytics_tab(generate_leaderboard_plot_fn, get_leaderboard_fn):
    with gr.TabItem("Analytics"):
        gr.Markdown("## Analytics")

        # Initialize the plot with the initial value
        initial_leaderboard_data = get_leaderboard_fn()
        initial_plot = generate_leaderboard_plot_fn(initial_leaderboard_data)
        if initial_plot is None:
            initial_plot = go.Figure()

        analytics_plot = gr.Plot(value=initial_plot)  # Set the initial value here

        task_type_selector = gr.Dropdown(
            label="Select Task Type",
            choices=["All", "title_enhancement", "short_desc_enhancement", "long_desc_enhancement"],
            value="All"
        )

        # Update the plot when the task type changes
        def update_analytics(selected_task_type):
            updated_leaderboard_data = get_leaderboard_fn()
            if not updated_leaderboard_data.empty and selected_task_type != "All":
                updated_leaderboard_data = updated_leaderboard_data[updated_leaderboard_data["task_type"] == selected_task_type]
            updated_plot = generate_leaderboard_plot_fn(updated_leaderboard_data)
            if updated_plot is None:
                updated_plot = go.Figure()
            return updated_plot

        task_type_selector.change(
            fn=update_analytics,
            inputs=[task_type_selector],
            outputs=analytics_plot
        )
