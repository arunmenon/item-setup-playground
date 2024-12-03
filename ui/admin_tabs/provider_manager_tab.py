from models.models import ProviderConfig


import gradio as gr


def create_provider_configuration_tab(admin_db_handler):
    with gr.TabItem("Provider Configuration"):
        gr.Markdown("## Manage Provider Configurations")

        # Fetch existing providers
        providers = admin_db_handler.get_providers()
        provider_options = [p.name for p in providers]

        with gr.Row():
            selected_provider = gr.Dropdown(
                label="Select Provider",
                choices=provider_options,
                value=None
            )
            action_selector = gr.Dropdown(
                label="Action",
                choices=["View", "Edit", "Create New", "Delete"],
                value="View"
            )

        # Provider fields
        provider_id = gr.Textbox(label="Provider ID", visible=False)
        name = gr.Textbox(label="Name")
        provider_name = gr.Textbox(label="Provider Name")
        family = gr.Textbox(label="Family")
        model = gr.Textbox(label="Model")
        max_tokens = gr.Number(label="Max Tokens")
        temperature = gr.Number(label="Temperature")
        is_active = gr.Checkbox(label="Is Active", value=True)

        save_button = gr.Button("Save Changes")
        create_button = gr.Button("Create Provider")
        delete_button = gr.Button("Delete Provider")

        feedback = gr.Textbox(label="Feedback", interactive=False)

        # Define actions
        def load_provider(provider_option):
            if not provider_option or provider_option == "":
                return [gr.update(value="")] * 8  # Return empty fields

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
                ]
            else:
                return [gr.update(value="")] * 8  # Return empty fields

        selected_provider.change(
            fn=load_provider,
            inputs=[selected_provider],
            outputs=[provider_id, name, provider_name, family, model, max_tokens, temperature, is_active]
        )

        # Save changes
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
                return msg
            except Exception as e:
                return f"Error: {str(e)}"

        save_button.click(
            fn=save_provider,
            inputs=[provider_id, name, provider_name, family, model, max_tokens, temperature, is_active],
            outputs=feedback
        )

        # Delete provider
        def delete_provider_action(provider_id_val):
            try:
                if provider_id_val and provider_id_val != "":
                    admin_db_handler.delete_provider(int(provider_id_val))
                    return "Provider deleted successfully."
                else:
                    return "No provider selected."
            except Exception as e:
                return f"Error: {str(e)}"

        delete_button.click(
            fn=delete_provider_action,
            inputs=[provider_id],
            outputs=feedback
        )