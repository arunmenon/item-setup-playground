from models.models import (
    EvaluationPromptTemplate, EvaluationTask,
    GenerationPromptTemplate, GenerationTask,
    ModelFamily
)
import gradio as gr

def create_prompt_template_management_tab(admin_db_handler):
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
            tasks = admin_db_handler.get_generation_tasks() if task_type == 'Generation' else admin_db_handler.get_evaluation_tasks()
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

        version = gr.Slider(
            label="Version:",
            value=1,
            minimum=1,
            step=1,
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

        # Action Buttons
        with gr.Row():
            save_button = gr.Button("Save", variant="primary")
            create_button = gr.Button("Create New", variant="secondary")
            delete_button = gr.Button("Delete", variant="stop", visible=False)

        feedback = gr.Markdown("")

        # Update task options when task type changes
        def update_task_options(task_type):
            options = get_task_options(task_type)
            return (
                gr.update(choices=options, value=None),  # selected_task
                gr.update(value=None),                   # selected_model_family
                gr.update(visible=False),                # delete_button
                "",                                      # template_text
                "",                                      # template_id
                1,                                       # version
                ""                                       # feedback
            )

        task_type_selector.change(
            fn=update_task_options,
            inputs=[task_type_selector],
            outputs=[selected_task, selected_model_family, delete_button, template_text, template_id, version, feedback]
        )

        # Reset fields when task changes
        def reset_fields_task_change():
            return (
                gr.update(value=None),           # selected_model_family
                gr.update(visible=False),        # delete_button
                "",                              # template_text
                "",                              # template_id
                1,                               # version
                ""                               # feedback
            )

        selected_task.change(
            fn=reset_fields_task_change,
            inputs=[],
            outputs=[selected_model_family, delete_button, template_text, template_id, version, feedback]
        )

        # Reset fields when model family changes
        def reset_fields_model_family_change():
            return (
                gr.update(visible=False),        # delete_button
                "",                              # template_text
                "",                              # template_id
                1,                               # version
                ""                               # feedback
            )

        selected_model_family.change(
            fn=reset_fields_model_family_change,
            inputs=[],
            outputs=[delete_button, template_text, template_id, version, feedback]
        )

        # Load template when any of the selections change
        def load_template(task_name, task_type, model_family_name, version_val):
            if not task_name or not model_family_name:
                return "", "", gr.update(visible=False), "Please select both Task and Model Family."

            # Fetch the template
            task_model = GenerationTask if task_type == 'Generation' else EvaluationTask
            template_model = GenerationPromptTemplate if task_type == 'Generation' else EvaluationPromptTemplate

            task = admin_db_handler.db_session.query(task_model).filter_by(task_name=task_name).first()
            model_family = admin_db_handler.db_session.query(ModelFamily).filter_by(name=model_family_name).first()

            template = admin_db_handler.db_session.query(template_model).filter_by(
                task_id=task.task_id,
                model_family_id=model_family.model_family_id,
                version=int(version_val)
            ).first()

            if template:
                return template.template_text, str(template.template_id), gr.update(visible=True), ""
            else:
                return "", "", gr.update(visible=False), "No template found. You can create a new one."

        def load_template_wrapper(task_name, task_type, model_family_name, version_val):
            return load_template(task_name, task_type, model_family_name, version_val)

        selected_task.change(
            fn=load_template_wrapper,
            inputs=[selected_task, task_type_selector, selected_model_family, version],
            outputs=[template_text, template_id, delete_button, feedback]
        )
        selected_model_family.change(
            fn=load_template_wrapper,
            inputs=[selected_task, task_type_selector, selected_model_family, version],
            outputs=[template_text, template_id, delete_button, feedback]
        )
        version.change(
            fn=load_template_wrapper,
            inputs=[selected_task, task_type_selector, selected_model_family, version],
            outputs=[template_text, template_id, delete_button, feedback]
        )

        # Save template
        def save_template(template_text_val, task_name, task_type, model_family_name, version_val, template_id_val):
            if not template_text_val.strip():
                return "Template Text cannot be empty.", gr.update(), gr.update()

            try:
                task_model = GenerationTask if task_type == 'Generation' else EvaluationTask
                template_model = GenerationPromptTemplate if task_type == 'Generation' else EvaluationPromptTemplate

                task = admin_db_handler.db_session.query(task_model).filter_by(task_name=task_name).first()
                model_family = admin_db_handler.db_session.query(ModelFamily).filter_by(name=model_family_name).first()

                if not task or not model_family:
                    return "Invalid Task or Model Family selected.", gr.update(), gr.update()

                # Prepare template data
                template_data = {
                    "task_id": task.task_id,
                    "model_family_id": model_family.model_family_id,
                    "template_text": template_text_val,
                    "version": int(version_val)
                }

                if template_id_val:
                    # Update existing template
                    existing_template = admin_db_handler.db_session.query(template_model).get(int(template_id_val))
                    if existing_template:
                        for key, value in template_data.items():
                            setattr(existing_template, key, value)
                        admin_db_handler.db_session.commit()
                        msg = "Template updated successfully."
                    else:
                        return "Template not found.", gr.update(), gr.update()
                else:
                    # Create new template
                    new_template = template_model(**template_data)
                    admin_db_handler.db_session.add(new_template)
                    admin_db_handler.db_session.commit()
                    msg = "Template created successfully."
                    # Update the template_id with the new template's ID
                    template_id_val = str(new_template.template_id)

                return msg, gr.update(value=template_id_val), gr.update(visible=True)
            except Exception as e:
                return f"Error: {str(e)}", gr.update(), gr.update()

        save_button.click(
            fn=save_template,
            inputs=[template_text, selected_task, task_type_selector, selected_model_family, version, template_id],
            outputs=[feedback, template_id, delete_button]
        )

        # Delete template
        def delete_template_action(task_name, task_type, model_family_name, version_val, template_id_val):
            try:
                if not template_id_val:
                    return "No template selected.", "", "", 1, gr.update(visible=False)
                task_model = GenerationTask if task_type == 'Generation' else EvaluationTask
                template_model = GenerationPromptTemplate if task_type == 'Generation' else EvaluationPromptTemplate

                task = admin_db_handler.db_session.query(task_model).filter_by(task_name=task_name).first()
                model_family = admin_db_handler.db_session.query(ModelFamily).filter_by(name=model_family_name).first()

                template = admin_db_handler.db_session.query(template_model).get(int(template_id_val))

                if template:
                    admin_db_handler.db_session.delete(template)
                    admin_db_handler.db_session.commit()
                    # Clear fields
                    return "Template deleted successfully.", "", "", 1, gr.update(visible=False)
                else:
                    return "Template not found.", "", "", 1, gr.update(visible=False)

            except Exception as e:
                return f"Error: {str(e)}", "", "", 1, gr.update(visible=False)

        delete_button.click(
            fn=delete_template_action,
            inputs=[selected_task, task_type_selector, selected_model_family, version, template_id],
            outputs=[feedback, template_text, template_id, version, delete_button]
        )

        # Create new template
        def create_new_template():
            return "", "", 1, gr.update(visible=False), "Ready to create a new template."

        create_button.click(
            fn=create_new_template,
            inputs=[],
            outputs=[template_text, template_id, version, delete_button, feedback]
        )
