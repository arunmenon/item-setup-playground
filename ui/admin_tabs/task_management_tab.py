from models.models import EvaluationTask, GenerationTask
import gradio as gr


def create_task_management_tab(admin_db_handler):
    with gr.TabItem("Task Management"):
        gr.Markdown("## Manage Tasks")

        # Task Type Selection
        task_type_selector = gr.Radio(
            choices=['Generation', 'Evaluation'],
            label='Select Task Type:',
            value='Generation'
        )

        # Fetch existing tasks
        def get_task_options(task_type):
            tasks = admin_db_handler.get_generation_tasks() if task_type=='Generation' else admin_db_handler.get_evaluation_tasks()
            return [t.task_name for t in tasks]

        selected_task = gr.Dropdown(
            label="Select or Create Task:",
            choices=get_task_options('Generation'),
            value=None,
            allow_custom_value=True,
            info="Select an existing task to view/edit or type a new task name to create.",
            interactive=True
        )

        task_id = gr.Textbox(label="Task ID:", visible=False)
        task_name = gr.Textbox(label="Task Name:", placeholder="Enter task name", interactive=True)
        description = gr.Textbox(label="Description:", lines=3, placeholder="Enter task description", interactive=True)
        max_tokens = gr.Textbox(label="Max Token:", placeholder="Enter max token", interactive=True)
        output_format = gr.Dropdown(
            label="Output Format:",
            choices=['JSON', 'MARKDOWN'],
            value='JSON',  # Set JSON as the default selected option
            interactive=True
        )

        with gr.Row():
            save_button = gr.Button("Save", variant="primary")
            delete_button = gr.Button("Delete", variant="stop", visible=False)

        feedback = gr.Markdown("")

        # Update form when task type changes
        def update_form(task_type):
            options = get_task_options(task_type)
            return gr.update(choices=options, value=None), "", "", "", "JSON", gr.update(visible=False), ""

        task_type_selector.change(
            fn=update_form,
            inputs=[task_type_selector],
            outputs=[selected_task, task_name, description, max_tokens, output_format, delete_button, feedback]
        )

        # Load task details when existing task is selected
        def load_task(task_name_val, task_type_val):
            tasks = get_task_options(task_type_val)
            if task_name_val in tasks:
                task_model = GenerationTask if task_type_val=='Generation' else EvaluationTask
                task = admin_db_handler.db_session.query(task_model).filter_by(task_name=task_name_val).first()
                if task:
                    return str(task.task_id), task.task_name, task.description, str(task.max_tokens), task.output_format, gr.update(visible=True), ""
            return "", task_name_val, "", "", "JSON", gr.update(visible=False), "Ready to create a new task."

        selected_task.change(
            fn=load_task,
            inputs=[selected_task, task_type_selector],
            outputs=[task_id, task_name, description, max_tokens, output_format, delete_button, feedback]
        )

        # Save task
        def save_task(task_id_val, task_name_val, description_val, max_tokens_val, output_format_val, task_type_val):
            if not task_name_val.strip():
                return "Task Name cannot be empty.", gr.update()
            try:
                task_data = {
                    "task_name"    : task_name_val,
                    "description"  : description_val,
                    "max_tokens"   : int(max_tokens_val),
                    "output_format": output_format_val
                }
                task_model = GenerationTask if task_type_val=='Generation' else EvaluationTask
                if task_id_val:
                    # Update existing task
                    task = admin_db_handler.db_session.query(task_model).get(int(task_id_val))
                    if task:
                        for key, value in task_data.items():
                            setattr(task, key, value)
                        admin_db_handler.db_session.commit()
                        msg = "Task updated successfully."
                    else:
                        return "Task not found.", gr.update()
                else:
                    # Create new task
                    new_task = task_model(**task_data)
                    admin_db_handler.db_session.add(new_task)
                    admin_db_handler.db_session.commit()
                    msg = "Task created successfully."

                return msg, gr.update(choices=get_task_options(task_type_val), value=task_name_val)
            except Exception as e:
                return f"Error: {str(e)}", gr.update()

        save_button.click(
            fn=save_task,
            inputs=[task_id, task_name, description, max_tokens, output_format, task_type_selector],
            outputs=[feedback, selected_task]
        )

        # Delete task
        def delete_task(task_id_val, task_type_val):
            if not task_id_val:
                return "No task selected.", gr.update()
            try:
                task_model = GenerationTask if task_type_val=='Generation' else EvaluationTask
                task = admin_db_handler.db_session.query(task_model).get(int(task_id_val))
                if task:
                    admin_db_handler.db_session.delete(task)
                    admin_db_handler.db_session.commit()
                    return "Task deleted successfully.", gr.update(choices=get_task_options(task_type_val), value=None)
                else:
                    return "Task not found.", gr.update()
            except Exception as e:
                return f"Error: {str(e)}", gr.update()

        delete_button.click(
            fn=delete_task,
            inputs=[task_id, task_type_selector],
            outputs=[feedback, selected_task]
        )