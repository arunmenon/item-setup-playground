import re
from models.models import (
    EvaluationPromptTemplate, EvaluationTask,
    GenerationPromptTemplate, GenerationTask,
    ModelFamily
)
import gradio as gr


def create_prompt_template_management_tab(admin_db_handler):
    # Apply custom CSS
    custom_css = """
    .gradio-container {
        background-color: #f9f9f9;
    }
    .component-container {
        background-color: #ffffff;
        padding: 10px;
        border: 1px solid #dddddd;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .component-container h3 {
        margin-top: 0;
    }
    .gr-button {
        padding: 10px 20px;
        font-size: 14px;
    }
    .gr-text-input, .gr-textbox, .gr-dropdown, .gr-radio {
        border: 1px solid #cccccc;
        border-radius: 3px;
        padding: 5px;
    }
    """

    with gr.TabItem("Prompt Template Management"):
        gr.Markdown("## Manage Prompt Templates")

        # Task Type Selection
        task_type_selector = gr.Radio(
            choices=['Generation', 'Evaluation'],
            label='Select Task Type:',
            value='Generation'
        )

        # Fetch existing tasks and model families
        def get_task_options(task_type):
            tasks = admin_db_handler.get_generation_tasks() if task_type=='Generation' else admin_db_handler.get_evaluation_tasks()
            return [t.task_name for t in tasks]

        def get_model_family_options():
            model_families = admin_db_handler.get_model_families()
            return [mf.name for mf in model_families]

        # Components
        selected_task = gr.Dropdown(
            label="Task:",
            choices=get_task_options('Generation'),
            value=None,
            interactive=True
        )

        selected_model_family = gr.Dropdown(
            label="Model Family:",
            choices=get_model_family_options(),
            value=None,
            interactive=True
        )

        # Define template_id here
        template_id = gr.Textbox(
            label="Template ID:",
            value="",
            visible=False,
            interactive=False
        )

        template_text = gr.Textbox(
            label="Template Text:",
            lines=15,
            placeholder="Enter the prompt template here...",
            interactive=True
        )

        # Version selection dropdown
        version_dropdown = gr.Dropdown(
            label="Version:",
            choices=[],
            value=None,
            interactive=True
        )

        # Display extracted placeholders
        placeholders_display = gr.Textbox(
            label="Extracted Placeholders:",
            lines=3,
            interactive=False,
            placeholder="Placeholders will be displayed here after you enter the template text."
        )

        # Action Buttons
        with gr.Row():
            save_button = gr.Button("Save", variant="primary")
            delete_button = gr.Button("Delete", variant="stop", visible=False)
            clear_button = gr.Button("Clear", variant="secondary")

        feedback = gr.Markdown("")

        # Function to extract placeholders
        def extract_placeholders(template_text):
            # Improved regex to match placeholders
            placeholders = re.findall(r"{([a-zA-Z0-9_]+)}", template_text)
            placeholders = list(set(placeholders))  # Remove duplicates
            placeholders_str = ', '.join(placeholders)
            return placeholders_str

        # Update placeholders display when template text changes
        template_text.change(
            fn=extract_placeholders,
            inputs=[template_text],
            outputs=[placeholders_display]
        )

        # Update task options when task type changes
        def update_task_options(task_type):
            options = get_task_options(task_type)
            return (
                gr.update(choices=options, value=None),  # selected_task
                gr.update(value=None),  # selected_model_family
                gr.update(choices=[], value=None),  # version_dropdown
                gr.update(visible=False),  # delete_button
                "",  # template_text
                "",  # template_id
                "",  # feedback
                ""  # placeholders_display
            )

        task_type_selector.change(
            fn=update_task_options,
            inputs=[task_type_selector],
            outputs=[selected_task, selected_model_family, version_dropdown, delete_button, template_text, template_id,
                     feedback, placeholders_display]
        )

        # Reset fields when task changes
        def reset_fields_task_change():
            return (
                gr.update(value=None),  # selected_model_family
                gr.update(choices=[], value=None),  # version_dropdown
                gr.update(visible=False),  # delete_button
                "",  # template_text
                "",  # template_id
                "",  # feedback
                ""  # placeholders_display
            )

        selected_task.change(
            fn=reset_fields_task_change,
            inputs=[],
            outputs=[selected_model_family, version_dropdown, delete_button, template_text, template_id, feedback,
                     placeholders_display]
        )

        # Reset fields when model family changes
        def reset_fields_model_family_change():
            return (
                gr.update(choices=[], value=None),  # version_dropdown
                gr.update(visible=False),  # delete_button
                "",  # template_text
                "",  # template_id
                "",  # feedback
                ""  # placeholders_display
            )

        selected_model_family.change(
            fn=reset_fields_model_family_change,
            inputs=[],
            outputs=[version_dropdown, delete_button, template_text, template_id, feedback, placeholders_display]
        )

        # Load versions when task or model family changes
        def load_versions(task_name, task_type, model_family_name):
            if not task_name or not model_family_name:
                return gr.update(choices=[], value=None), "", "", gr.update(visible=False), "Please select both Task and Model Family.", ""

            # Fetch available versions
            task_model = GenerationTask if task_type=='Generation' else EvaluationTask
            template_model = GenerationPromptTemplate if task_type=='Generation' else EvaluationPromptTemplate
            task = admin_db_handler.db_session.query(task_model).filter_by(task_name=task_name).first()
            model_family = admin_db_handler.db_session.query(ModelFamily).filter_by(name=model_family_name).first()

            templates = admin_db_handler.db_session.query(template_model).filter_by(
                task_id=task.task_id,
                model_family_id=model_family.model_family_id
            ).order_by(template_model.version.desc()).all()

            if templates:
                versions = [str(t.version) for t in templates]
                versions.insert(0, "New Version")  # Add 'New Version' option at the top
                latest_template = templates[0]  # Latest version
                return (
                    gr.update(choices=versions, value=versions[1]),  # version_dropdown (select latest version)
                    latest_template.template_text,  # template_text
                    str(latest_template.template_id),  # template_id
                    gr.update(visible=True),  # delete_button
                    "",  # feedback
                    extract_placeholders(latest_template.template_text)  # placeholders_display
                )
            else:
                # No templates available
                return (
                    gr.update(choices=["New Version"], value="New Version"),  # version_dropdown
                    "",  # template_text
                    "",  # template_id
                    gr.update(visible=False),  # delete_button
                    "No template found. You can create a new one.",  # feedback
                    ""  # placeholders_display
                )

        selected_task.change(
            fn=load_versions,
            inputs=[selected_task, task_type_selector, selected_model_family],
            outputs=[version_dropdown, template_text, template_id, delete_button, feedback, placeholders_display]
        )
        selected_model_family.change(
            fn=load_versions,
            inputs=[selected_task, task_type_selector, selected_model_family],
            outputs=[version_dropdown, template_text, template_id, delete_button, feedback, placeholders_display]
        )

        # Load the selected version's template text
        def load_selected_version(task_name, task_type, model_family_name, selected_version):
            if not task_name or not model_family_name or not selected_version:
                return "", "", gr.update(visible=False), "Please select Task, Model Family, and Version.", ""

            if selected_version=="New Version":
                # Reset fields for new template
                return "", "", gr.update(visible=False), "Creating a new template version.", ""

            # Fetch the selected version
            task_model = GenerationTask if task_type=='Generation' else EvaluationTask
            template_model = GenerationPromptTemplate if task_type=='Generation' else EvaluationPromptTemplate

            task = admin_db_handler.db_session.query(task_model).filter_by(task_name=task_name).first()
            model_family = admin_db_handler.db_session.query(ModelFamily).filter_by(name=model_family_name).first()

            template = admin_db_handler.db_session.query(template_model).filter_by(
                task_id=task.task_id,
                model_family_id=model_family.model_family_id,
                version=int(selected_version)
            ).first()

            if template:
                return template.template_text, str(template.template_id), gr.update(visible=True), "", extract_placeholders(template.template_text)
            else:
                return "", "", gr.update(visible=False), "Template not found for the selected version.", ""

        version_dropdown.change(
            fn=load_selected_version,
            inputs=[selected_task, task_type_selector, selected_model_family, version_dropdown],
            outputs=[template_text, template_id, delete_button, feedback, placeholders_display]
        )

        # Save template
        def save_template(template_text_val, task_name, task_type, model_family_name, selected_version):
            if not template_text_val.strip():
                return "Template Text cannot be empty.", gr.update(), gr.update(), gr.update(choices=[], value=None), ""

            try:
                task_model = GenerationTask if task_type=='Generation' else EvaluationTask
                template_model = GenerationPromptTemplate if task_type=='Generation' else EvaluationPromptTemplate

                task = admin_db_handler.db_session.query(task_model).filter_by(task_name=task_name).first()
                model_family = admin_db_handler.db_session.query(ModelFamily).filter_by(name=model_family_name).first()

                if not task or not model_family:
                    return "Invalid Task or Model Family selected.", gr.update(), gr.update(), gr.update(choices=[], value=None), ""

                # Fetch all existing templates for the task and model family
                existing_templates = admin_db_handler.db_session.query(template_model).filter_by(
                    task_id=task.task_id,
                    model_family_id=model_family.model_family_id
                ).order_by(template_model.version.asc()).all()

                # Determine the next version
                next_version = 1
                if existing_templates:
                    next_version = existing_templates[-1].version + 1

                # Check if the template text matches any existing version
                for template in existing_templates:
                    if template.template_text.strip()==template_text_val.strip():
                        # No changes detected, inform the user
                        return (
                            f"No changes detected. This template matches version {template.version}.",
                            gr.update(value=str(template.template_id)),
                            gr.update(visible=True),
                            gr.update(choices=[str(t.version) for t in
                                               existing_templates], value=str(template.version)),
                            extract_placeholders(template.template_text)
                        )

                # Extract placeholders
                placeholders = re.findall(r"{([a-zA-Z0-9_]+)}", template_text_val)
                placeholders = list(set(placeholders))  # Remove duplicates

                # Prepare template data
                template_data = {
                    "task_id"        : task.task_id,
                    "model_family_id": model_family.model_family_id,
                    "template_text"  : template_text_val,
                    "version"        : next_version,
                    "placeholders"   : placeholders  # Store placeholders
                }

                # Create new template with incremented version
                new_template = template_model(**template_data)
                admin_db_handler.db_session.add(new_template)
                admin_db_handler.db_session.commit()

                # Update versions list
                updated_versions = [str(t.version) for t in existing_templates] + [str(next_version)]
                updated_versions.insert(0, "New Version")  # Add 'New Version' at the top

                msg = f"Template saved as new version {next_version}."
                template_id_val = str(new_template.template_id)

                return msg, gr.update(value=template_id_val), gr.update(visible=True), gr.update(choices=updated_versions, value=str(next_version)), extract_placeholders(template_text_val)
            except Exception as e:
                return f"Error: {str(e)}", gr.update(), gr.update(), gr.update(choices=[], value=None), ""

        save_button.click(
            fn=save_template,
            inputs=[template_text, selected_task, task_type_selector, selected_model_family, version_dropdown],
            outputs=[feedback, template_id, delete_button, version_dropdown, placeholders_display]
        )

        # Delete template
        def delete_template_action(task_name, task_type, model_family_name, selected_version):
            try:
                if not selected_version or selected_version=="New Version":
                    return "No version selected.", "", "", gr.update(choices=[], value=None), gr.update(visible=False), ""

                task_model = GenerationTask if task_type=='Generation' else EvaluationTask
                template_model = GenerationPromptTemplate if task_type=='Generation' else EvaluationPromptTemplate

                task = admin_db_handler.db_session.query(task_model).filter_by(task_name=task_name).first()
                model_family = admin_db_handler.db_session.query(ModelFamily).filter_by(name=model_family_name).first()

                template = admin_db_handler.db_session.query(template_model).filter_by(
                    task_id=task.task_id,
                    model_family_id=model_family.model_family_id,
                    version=int(selected_version)
                ).first()

                if template:
                    admin_db_handler.db_session.delete(template)
                    admin_db_handler.db_session.commit()

                    # Fetch updated templates
                    updated_templates = admin_db_handler.db_session.query(template_model).filter_by(
                        task_id=task.task_id,
                        model_family_id=model_family.model_family_id
                    ).order_by(template_model.version.desc()).all()

                    if updated_templates:
                        # Load the latest template
                        latest_template = updated_templates[0]
                        versions = [str(t.version) for t in updated_templates]
                        versions.insert(0, "New Version")
                        return (
                            "Template deleted successfully.",
                            latest_template.template_text,
                            str(latest_template.template_id),
                            gr.update(choices=versions, value=versions[1]),
                            gr.update(visible=True),
                            extract_placeholders(latest_template.template_text)
                        )
                    else:
                        # No templates left
                        return (
                            "Template deleted successfully.",
                            "",
                            "",
                            gr.update(choices=["New Version"], value="New Version"),
                            gr.update(visible=False),
                            ""
                        )
                else:
                    return "Template not found.", "", "", gr.update(choices=[], value=None), gr.update(visible=False), ""
            except Exception as e:
                return f"Error: {str(e)}", "", "", gr.update(choices=[], value=None), gr.update(visible=False), ""

        delete_button.click(
            fn=delete_template_action,
            inputs=[selected_task, task_type_selector, selected_model_family, version_dropdown],
            outputs=[feedback, template_text, template_id, version_dropdown, delete_button, placeholders_display]
        )

        # Clear template
        def clear_template():
            return "", "", gr.update(value="New Version"), gr.update(visible=False), "Fields have been cleared.", ""

        clear_button.click(
            fn=clear_template,
            inputs=[],
            outputs=[template_text, template_id, version_dropdown, delete_button, feedback, placeholders_display]
        )