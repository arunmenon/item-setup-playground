import gradio as gr
import plotly.graph_objects as go

from models.models import ProviderConfig, StylingGuide, TaskConfig, Template


def create_prompt_template_management_tab(admin_db_handler):
    with gr.TabItem("Prompt Template Management"):
        gr.Markdown("## Manage Prompt Templates")

        # Fetch existing templates
        templates = admin_db_handler.get_templates()
        template_options = [f"{t.template_name} (v{t.version})" for t in templates]

        with gr.Row():
            selected_template = gr.Dropdown(
                label="Select Template",
                choices=template_options,
                value=None
            )
            action_selector = gr.Dropdown(
                label="Action",
                choices=["View", "Edit", "Create New", "Delete"],
                value="View"
            )

        # Template fields
        template_id = gr.Textbox(label="Template ID", visible=False)
        template_name = gr.Textbox(label="Template Name")
        template_type = gr.Radio(label="Template Type", choices=["base", "model"])
        parent_template_id = gr.Textbox(label="Parent Template ID (optional)")
        model_family = gr.Textbox(label="Model Family (optional)")
        task_name = gr.Textbox(label="Task Name")
        content = gr.Textbox(label="Content", lines=10)
        version = gr.Number(label="Version", value=1)
        is_active = gr.Checkbox(label="Is Active", value=True)

        save_button = gr.Button("Save Changes")
        create_button = gr.Button("Create Template")
        delete_button = gr.Button("Delete Template")

        feedback = gr.Textbox(label="Feedback", interactive=False)

        # Define actions
        def load_template(template_option):
            if not template_option or template_option == "":
                return [gr.update(value="")] * 8  # Return empty fields

            template_name_version = template_option.split(" (v")
            template_name_str = template_name_version[0]
            version_str = template_name_version[1][:-1]

            template = admin_db_handler.db_session.query(Template).filter(
                Template.template_name == template_name_str,
                Template.version == int(version_str)
            ).first()

            if template:
                return [
                    gr.update(value=str(template.template_id)),
                    gr.update(value=template.template_name),
                    gr.update(value=template.template_type),
                    gr.update(value=str(template.parent_template_id) if template.parent_template_id else ""),
                    gr.update(value=template.model_family if template.model_family else ""),
                    gr.update(value=template.task_name),
                    gr.update(value=template.content),
                    gr.update(value=template.version),
                    gr.update(value=template.is_active),
                ]
            else:
                return [gr.update(value="")] * 8  # Return empty fields

        def handle_action(action, *args):
            if action == "View" or action == "Edit":
                return
            elif action == "Create New":
                return
            elif action == "Delete":
                return

        selected_template.change(
            fn=load_template,
            inputs=[selected_template],
            outputs=[template_id, template_name, template_type, parent_template_id, model_family, task_name, content, version, is_active]
        )

        # Save changes
        def save_template(template_id_val, template_name_val, template_type_val, parent_template_id_val,
                          model_family_val, task_name_val, content_val, version_val, is_active_val):
            try:
                updated_data = {
                    "template_name": template_name_val,
                    "template_type": template_type_val,
                    "parent_template_id": int(parent_template_id_val) if parent_template_id_val else None,
                    "model_family": model_family_val,
                    "task_name": task_name_val,
                    "content": content_val,
                    "version": int(version_val),
                    "is_active": is_active_val,
                }
                if template_id_val and template_id_val != "":
                    # Update existing template
                    admin_db_handler.update_template(int(template_id_val), updated_data)
                    msg = "Template updated successfully."
                else:
                    # Create new template
                    admin_db_handler.create_template(updated_data)
                    msg = "Template created successfully."
                return msg
            except Exception as e:
                return f"Error: {str(e)}"

        save_button.click(
            fn=save_template,
            inputs=[template_id, template_name, template_type, parent_template_id, model_family, task_name, content, version, is_active],
            outputs=feedback
        )

        # Delete template
        def delete_template_action(template_id_val):
            try:
                if template_id_val and template_id_val != "":
                    admin_db_handler.delete_template(int(template_id_val))
                    return "Template deleted successfully."
                else:
                    return "No template selected."
            except Exception as e:
                return f"Error: {str(e)}"

        delete_button.click(
            fn=delete_template_action,
            inputs=[template_id],
            outputs=feedback
        )

def create_task_management_tab(admin_db_handler):
    with gr.TabItem("Task Management"):
        gr.Markdown("## Manage Tasks")

        # Fetch existing tasks
        tasks = admin_db_handler.get_tasks()
        task_options = [t.task_name for t in tasks]

        with gr.Row():
            selected_task = gr.Dropdown(
                label="Select Task",
                choices=task_options,
                value=None
            )
            action_selector = gr.Dropdown(
                label="Action",
                choices=["View", "Edit", "Create New", "Delete"],
                value="View"
            )

        # Task fields
        task_id = gr.Textbox(label="Task ID", visible=False)
        task_name = gr.Textbox(label="Task Name")
        max_tokens = gr.Number(label="Max Tokens")
        output_format = gr.Textbox(label="Output Format")

        save_button = gr.Button("Save Changes")
        create_button = gr.Button("Create Task")
        delete_button = gr.Button("Delete Task")

        feedback = gr.Textbox(label="Feedback", interactive=False)

        # Define actions
        def load_task(task_option):
            if not task_option or task_option == "":
                return [gr.update(value="")] * 4  # Return empty fields

            task = admin_db_handler.db_session.query(TaskConfig).filter(
                TaskConfig.task_name == task_option
            ).first()

            if task:
                return [
                    gr.update(value=str(task.task_id)),
                    gr.update(value=task.task_name),
                    gr.update(value=task.max_tokens),
                    gr.update(value=task.output_format),
                ]
            else:
                return [gr.update(value="")] * 4  # Return empty fields

        selected_task.change(
            fn=load_task,
            inputs=[selected_task],
            outputs=[task_id, task_name, max_tokens, output_format]
        )

        # Save changes
        def save_task(task_id_val, task_name_val, max_tokens_val, output_format_val):
            try:
                updated_data = {
                    "task_name": task_name_val,
                    "max_tokens": int(max_tokens_val),
                    "output_format": output_format_val,
                }
                if task_id_val and task_id_val != "":
                    # Update existing task
                    admin_db_handler.update_task(int(task_id_val), updated_data)
                    msg = "Task updated successfully."
                else:
                    # Create new task
                    admin_db_handler.create_task(updated_data)
                    msg = "Task created successfully."
                return msg
            except Exception as e:
                return f"Error: {str(e)}"

        save_button.click(
            fn=save_task,
            inputs=[task_id, task_name, max_tokens, output_format],
            outputs=feedback
        )

        # Delete task
        def delete_task_action(task_id_val):
            try:
                if task_id_val and task_id_val != "":
                    admin_db_handler.delete_task(int(task_id_val))
                    return "Task deleted successfully."
                else:
                    return "No task selected."
            except Exception as e:
                return f"Error: {str(e)}"

        delete_button.click(
            fn=delete_task_action,
            inputs=[task_id],
            outputs=feedback
        )

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
        
def create_styling_guide_manager_tab(admin_db_handler, product_types):
    with gr.TabItem("Styling Guide Manager"):
        gr.Markdown("## Manage Styling Guides")

        # Fetch existing styling guides
        styling_guides = admin_db_handler.get_styling_guides()
        guide_options = [f"{sg.product_type} - {sg.task_name} (v{sg.version})" for sg in styling_guides]

        with gr.Row():
            selected_guide = gr.Dropdown(
                label="Select Styling Guide",
                choices=guide_options,
                value=None
            )
            action_selector = gr.Dropdown(
                label="Action",
                choices=["View", "Edit", "Create New", "Delete"],
                value="View"
            )

        # Styling guide fields
        guide_id = gr.Textbox(label="Guide ID", visible=False)
        product_type = gr.Dropdown(
            label="Product Type",
            choices=product_types,
            value=None
        )
        task_name = gr.Textbox(label="Task Name")
        content = gr.Textbox(label="Content", lines=10)
        version = gr.Number(label="Version", value=1)
        is_active = gr.Checkbox(label="Is Active", value=True)

        save_button = gr.Button("Save Changes")
        create_button = gr.Button("Create Styling Guide")
        delete_button = gr.Button("Delete Styling Guide")

        feedback = gr.Textbox(label="Feedback", interactive=False)

        # Define actions
        def load_styling_guide(guide_option):
            if not guide_option or guide_option == "":
                return [gr.update(value="")] * 6  # Return empty fields

            parts = guide_option.split(" - ")
            product_type_str = parts[0]
            task_and_version = parts[1].split(" (v")
            task_name_str = task_and_version[0]
            version_str = task_and_version[1][:-1]

            guide = admin_db_handler.db_session.query(StylingGuide).filter(
                StylingGuide.product_type == product_type_str,
                StylingGuide.task_name == task_name_str,
                StylingGuide.version == int(version_str)
            ).first()

            if guide:
                return [
                    gr.update(value=str(guide.styling_guide_id)),
                    gr.update(value=guide.product_type),
                    gr.update(value=guide.task_name),
                    gr.update(value=guide.content),
                    gr.update(value=guide.version),
                    gr.update(value=guide.is_active),
                ]
            else:
                return [gr.update(value="")] * 6  # Return empty fields

        selected_guide.change(
            fn=load_styling_guide,
            inputs=[selected_guide],
            outputs=[guide_id, product_type, task_name, content, version, is_active]
        )

        # Save changes
        def save_styling_guide(guide_id_val, product_type_val, task_name_val, content_val, version_val, is_active_val):
            try:
                updated_data = {
                    "product_type": product_type_val,
                    "task_name": task_name_val,
                    "content": content_val,
                    "version": int(version_val),
                    "is_active": is_active_val,
                }
                if guide_id_val and guide_id_val != "":
                    # Update existing styling guide
                    admin_db_handler.update_styling_guide(int(guide_id_val), updated_data)
                    msg = "Styling guide updated successfully."
                else:
                    # Create new styling guide
                    admin_db_handler.create_styling_guide(updated_data)
                    msg = "Styling guide created successfully."
                return msg
            except Exception as e:
                return f"Error: {str(e)}"

        save_button.click(
            fn=save_styling_guide,
            inputs=[guide_id, product_type, task_name, content, version, is_active],
            outputs=feedback
        )

        # Delete styling guide
        def delete_styling_guide_action(guide_id_val):
            try:
                if guide_id_val and guide_id_val != "":
                    admin_db_handler.delete_styling_guide(int(guide_id_val))
                    return "Styling guide deleted successfully."
                else:
                    return "No styling guide selected."
            except Exception as e:
                return f"Error: {str(e)}"

        delete_button.click(
            fn=delete_styling_guide_action,
            inputs=[guide_id],
            outputs=feedback
        )
