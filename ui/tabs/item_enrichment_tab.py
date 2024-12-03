import gradio as gr


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