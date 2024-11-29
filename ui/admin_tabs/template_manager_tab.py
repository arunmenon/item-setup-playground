from models.models import EvaluationPromptTemplate, EvaluationTask, GenerationPromptTemplate, GenerationTask, ModelFamily
import gradio as gr


def create_prompt_template_management_tab(admin_db_handler):
    with gr.TabItem("Prompt Template Management"):
        gr.Markdown("## Manage Prompt Templates")

        # Task Type Selection
        task_type_selector = gr.Radio(
            choices=['Generation', 'Evaluation'],
            label='Select Task Type',
            value='Generation'
        )

        # Fetch existing tasks based on task type
        def get_task_options(task_type):
            if task_type == 'Generation':
                tasks = admin_db_handler.get_generation_tasks()
            else:
                tasks = admin_db_handler.get_evaluation_tasks()
            return [t.task_name for t in tasks]

        task_options = get_task_options('Generation')
        selected_task = gr.Dropdown(
            label="Select Task",
            choices=task_options,
            value=None
        )

        # Fetch existing templates for the selected task
        def get_template_options(task_name, task_type):
            if task_type == 'Generation':
                task = admin_db_handler.db_session.query(GenerationTask).filter_by(task_name=task_name).first()
                templates = admin_db_handler.get_generation_prompt_templates(task_id=task.task_id)
            else:
                task = admin_db_handler.db_session.query(EvaluationTask).filter_by(task_name=task_name).first()
                templates = admin_db_handler.get_evaluation_prompt_templates(task_id=task.task_id)
            return [f"{admin_db_handler.db_session.query(ModelFamily).get(t.model_family_id).name} (v{t.version})" for t in templates]

        selected_template = gr.Dropdown(
            label="Select Template",
            choices=[],
            value=None
        )

        action_selector = gr.Dropdown(
            label="Action",
            choices=["View", "Edit", "Create New", "Delete"],
            value="View"
        )

        # Template fields
        template_id = gr.Textbox(label="Template ID", visible=False)
        model_family_name = gr.Textbox(label="Model Family")
        template_text = gr.Textbox(label="Template Text", lines=10)
        version = gr.Number(label="Version", value=1)
        # Add other fields as needed

        save_button = gr.Button("Save Changes")
        create_button = gr.Button("Create Template")
        delete_button = gr.Button("Delete Template")

        feedback = gr.Textbox(label="Feedback", interactive=False)

        # Update task options when task type changes
        def update_task_options(task_type):
            options = get_task_options(task_type)
            return gr.update(choices=options, value=None), gr.update(choices=[], value=None)

        task_type_selector.change(
            fn=update_task_options,
            inputs=[task_type_selector],
            outputs=[selected_task, selected_template]
        )

        # Update template options when task changes
        def update_template_options(task_name, task_type):
            options = get_template_options(task_name, task_type)
            return gr.update(choices=options, value=None)

        selected_task.change(
            fn=update_template_options,
            inputs=[selected_task, task_type_selector],
            outputs=selected_template
        )

        # Load template details when template is selected
        def load_template(template_option, task_name, task_type):
            if not template_option or template_option == "":
                return [gr.update(value="")] * 4  # Return empty fields

            model_family_name, version_str = template_option.split(' (v')
            version = int(version_str[:-1])  # Remove closing parenthesis
            if task_type == 'Generation':
                task = admin_db_handler.db_session.query(GenerationTask).filter_by(task_name=task_name).first()
                model_family = admin_db_handler.db_session.query(ModelFamily).filter_by(name=model_family_name).first()
                template = admin_db_handler.db_session.query(GenerationPromptTemplate).filter(
                    GenerationPromptTemplate.task_id == task.task_id,
                    GenerationPromptTemplate.model_family_id == model_family.model_family_id,
                    GenerationPromptTemplate.version == version
                ).first()
            else:
                task = admin_db_handler.db_session.query(EvaluationTask).filter_by(task_name=task_name).first()
                model_family = admin_db_handler.db_session.query(ModelFamily).filter_by(name=model_family_name).first()
                template = admin_db_handler.db_session.query(EvaluationPromptTemplate).filter(
                    EvaluationPromptTemplate.task_id == task.task_id,
                    EvaluationPromptTemplate.model_family_id == model_family.model_family_id,
                    EvaluationPromptTemplate.version == version
                ).first()

            if template:
                return [
                    gr.update(value=str(template.template_id)),
                    gr.update(value=model_family_name),
                    gr.update(value=template.template_text),
                    gr.update(value=template.version)
                ]
            else:
                return [gr.update(value="")] * 4  # Return empty fields

        selected_template.change(
            fn=load_template,
            inputs=[selected_template, selected_task, task_type_selector],
            outputs=[template_id, model_family_name, template_text, version]
        )

        # Save changes
        def save_template(template_id_val, model_family_name_val, template_text_val, version_val, task_name, task_type):
            try:
                updated_data = {
                    "model_family": model_family_name_val,
                    "template_text": template_text_val,
                    "version": int(version_val)
                }
                if task_type == 'Generation':
                    task = admin_db_handler.db_session.query(GenerationTask).filter_by(task_name=task_name).first()
                    updated_data['task_id'] = task.task_id
                    if template_id_val and template_id_val != "":
                        # Update existing template
                        admin_db_handler.update_generation_prompt_template(int(template_id_val), updated_data)
                        msg = "Generation Prompt Template updated successfully."
                    else:
                        # Create new template
                        admin_db_handler.create_generation_prompt_template(updated_data)
                        msg = "Generation Prompt Template created successfully."
                else:
                    task = admin_db_handler.db_session.query(EvaluationTask).filter_by(task_name=task_name).first()
                    updated_data['task_id'] = task.task_id
                    if template_id_val and template_id_val != "":
                        # Update existing template
                        admin_db_handler.update_evaluation_prompt_template(int(template_id_val), updated_data)
                        msg = "Evaluation Prompt Template updated successfully."
                    else:
                        # Create new template
                        admin_db_handler.create_evaluation_prompt_template(updated_data)
                        msg = "Evaluation Prompt Template created successfully."

                # Update template options after save
                options = get_template_options(task_name, task_type)
                return msg, gr.update(choices=options)
            except Exception as e:
                return f"Error: {str(e)}", gr.update()

        save_button.click(
            fn=save_template,
            inputs=[template_id, model_family_name, template_text, version, selected_task, task_type_selector],
            outputs=[feedback, selected_template]
        )

        # Delete template
        def delete_template_action(template_id_val, task_name, task_type):
            try:
                if template_id_val and template_id_val != "":
                    if task_type == 'Generation':
                        admin_db_handler.delete_generation_prompt_template(int(template_id_val))
                        msg = "Generation Prompt Template deleted successfully."
                    else:
                        admin_db_handler.delete_evaluation_prompt_template(int(template_id_val))
                        msg = "Evaluation Prompt Template deleted successfully."
                    # Update template options after delete
                    options = get_template_options(task_name, task_type)
                    return msg, gr.update(choices=options)
                else:
                    return "No template selected.", gr.update()
            except Exception as e:
                return f"Error: {str(e)}", gr.update()

        delete_button.click(
            fn=delete_template_action,
            inputs=[template_id, selected_task, task_type_selector],
            outputs=[feedback, selected_template]
        )