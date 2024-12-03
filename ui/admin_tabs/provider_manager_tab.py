import gradio as gr

from models.models import ProviderConfig

def create_provider_configuration_tab(admin_db_handler):
    with gr.TabItem("Provider Configuration"):
        gr.Markdown("## Manage Provider Configurations")

        # Fetch existing providers
        providers = admin_db_handler.get_providers()
        provider_options = [p.name for p in providers]

        # Components
        selected_provider = gr.Dropdown(
            label="Select Provider:",
            choices=provider_options,
            value=None,
            interactive=True
        )

        # Define provider_id here
        provider_id = gr.Textbox(
            label="Provider ID:",
            value="",
            visible=False,
            interactive=False
        )

        # Provider fields
        name = gr.Textbox(label="Name", interactive=True)
        provider_name = gr.Textbox(label="Provider Name", interactive=True)
        family = gr.Textbox(label="Family", interactive=True)
        model = gr.Textbox(label="Model", interactive=True)
        max_tokens = gr.Number(label="Max Tokens", interactive=True)
        temperature = gr.Number(label="Temperature", interactive=True)
        is_active = gr.Checkbox(label="Is Active", value=True, interactive=True)

        # Action Buttons
        with gr.Row():
            save_button = gr.Button("Save", variant="primary")
            create_button = gr.Button("Create New", variant="secondary")
            delete_button = gr.Button("Delete", variant="stop", visible=False)

        feedback = gr.Markdown("")

        # Function to load provider details
        def load_provider(provider_option):
            if not provider_option or provider_option == "":
                return [gr.update(value="")] * 8 + [gr.update(visible=False), ""]
            provider = admin_db_handler.db_session.query(ProviderConfig).filter(
                ProviderConfig.name == provider_option
            ).first()
            if provider:
                return [
                    gr.update(value=str(provider.provider_id)),
                    gr.update(value=provider.name),
                    gr.update(value=provider.provider_name),
                    gr.update(value=provider.family),
                    gr.update(value=provider.model),
                    gr.update(value=provider.max_tokens),
                    gr.update(value=provider.temperature),
                    gr.update(value=provider.is_active),
                    gr.update(visible=True),
                    ""
                ]
            else:
                return [gr.update(value="")] * 8 + [gr.update(visible=False), "Provider not found."]

        selected_provider.change(
            fn=load_provider,
            inputs=[selected_provider],
            outputs=[provider_id, name, provider_name, family, model, max_tokens, temperature, is_active, delete_button, feedback]
        )

        # Save provider
        def save_provider(provider_id_val, name_val, provider_name_val, family_val, model_val,
                          max_tokens_val, temperature_val, is_active_val):
            try:
                updated_data = {
                    "name": name_val,
                    "provider_name": provider_name_val,
                    "family": family_val,
                    "model": model_val,
                    "max_tokens": int(max_tokens_val),
                    "temperature": float(temperature_val),
                    "is_active": is_active_val,
                }
                if provider_id_val and provider_id_val != "":
                    # Update existing provider
                    admin_db_handler.update_provider(int(provider_id_val), updated_data)
                    msg = "Provider updated successfully."
                else:
                    # Create new provider
                    admin_db_handler.create_provider(updated_data)
                    msg = "Provider created successfully."
                    provider_id_val = str(updated_data.get('provider_id', ''))
                # Refresh provider options
                providers = admin_db_handler.get_providers()
                provider_options = [p.name for p in providers]
                return msg, gr.update(choices=provider_options, value=name_val), gr.update(visible=True)
            except Exception as e:
                return f"Error: {str(e)}", gr.update(), gr.update()

        save_button.click(
            fn=save_provider,
            inputs=[provider_id, name, provider_name, family, model, max_tokens, temperature, is_active],
            outputs=[feedback, selected_provider, delete_button]
        )

        # Delete provider
        def delete_provider_action(provider_id_val):
            try:
                if provider_id_val and provider_id_val != "":
                    admin_db_handler.delete_provider(int(provider_id_val))
                    # Clear fields and refresh provider options
                    providers = admin_db_handler.get_providers()
                    provider_options = [p.name for p in providers]
                    return (
                        "Provider deleted successfully.",
                        "", "", "", "", "", "", "", True,
                        gr.update(visible=False),
                        gr.update(choices=provider_options, value=None)
                    )
                else:
                    return "No provider selected.", "", "", "", "", "", "", "", True, gr.update(visible=False), gr.update()
            except Exception as e:
                return f"Error: {str(e)}", "", "", "", "", "", "", "", True, gr.update(visible=False), gr.update()

        delete_button.click(
            fn=delete_provider_action,
            inputs=[provider_id],
            outputs=[feedback, provider_id, name, provider_name, family, model, max_tokens, temperature, is_active, delete_button, selected_provider]
        )

        # Create new provider
        def create_new_provider():
            return "", "", "", "", "", "", "", True, gr.update(visible=False), "Ready to create a new provider."

        create_button.click(
            fn=create_new_provider,
            inputs=[],
            outputs=[provider_id, name, provider_name, family, model, max_tokens, temperature, is_active, delete_button, feedback]
        )
