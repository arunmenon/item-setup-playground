from models.models import EvaluationTask, GenerationTask


import gradio as gr


def create_task_management_tab(admin_db_handler):
    with gr.TabItem("Task Management"):
        gr.Markdown("## Manage Tasks")

        # Task Type Selection
        task_type_selector = gr.Radio(
            choices=['Generation', 'Evaluation'],
            label='Select Task Type',
            value='Generation'
        )

        # Fetch existing tasks
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

        action_selector = gr.Dropdown(
            label="Action",
            choices=["View", "Edit", "Create New", "Delete"],
            value="View"
        )

        # Task fields
        task_id = gr.Textbox(label="Task ID", visible=False)
        task_name = gr.Textbox(label="Task Name")
        description = gr.Textbox(label="Description", lines=3)

        save_button = gr.Button("Save Changes")
        create_button = gr.Button("Create Task")
        delete_button = gr.Button("Delete Task")

        feedback = gr.Textbox(label="Feedback", interactive=False)

        # Update task options when task type changes
        def update_task_options(task_type):
            options = get_task_options(task_type)
            return gr.update(choices=options, value=None)

        task_type_selector.change(
            fn=update_task_options,
            inputs=[task_type_selector],
            outputs=[selected_task]
        )

        # Load task details when task is selected
        def load_task(task_name, task_type):
            if not task_name or task_name == "":
                return [gr.update(value="")] * 3  # Return empty fields

            if task_type == 'Generation':
                task = admin_db_handler.db_session.query(GenerationTask).filter_by(task_name=task_name).first()
            else:
                task = admin_db_handler.db_session.query(EvaluationTask).filter_by(task_name=task_name).first()

            if task:
                return [
                    gr.update(value=str(task.task_id)),
                    gr.update(value=task.task_name),
                    gr.update(value=task.description)
                ]
            else:
                return [gr.update(value="")] * 3  # Return empty fields

        selected_task.change(
            fn=load_task,
            inputs=[selected_task, task_type_selector],
            outputs=[task_id, task_name, description]
        )

        # Save changes
        def save_task(task_id_val, task_name_val, description_val, task_type):
            try:
                updated_data = {
                    "task_name": task_name_val,
                    "description": description_val
                }
                if task_type == 'Generation':
                    if task_id_val and task_id_val != "":
                        # Update existing task
                        admin_db_handler.update_generation_task(int(task_id_val), updated_data)
                        msg = "Generation Task updated successfully."
                    else:
                        # Create new task
                        admin_db_handler.create_generation_task(updated_data)
                        msg = "Generation Task created successfully."
                else:
                    if task_id_val and task_id_val != "":
                        # Update existing task
                        admin_db_handler.update_evaluation_task(int(task_id_val), updated_data)
                        msg = "Evaluation Task updated successfully."
                    else:
                        # Create new task
                        admin_db_handler.create_evaluation_task(updated_data)
                        msg = "Evaluation Task created successfully."
                # Update task options after save
                options = get_task_options(task_type)
                return msg, gr.update(choices=options)
            except Exception as e:
                return f"Error: {str(e)}", gr.update()

        save_button.click(
            fn=save_task,
            inputs=[task_id, task_name, description, task_type_selector],
            outputs=[feedback, selected_task]
        )

        # Delete task
        def delete_task_action(task_id_val, task_type):
            try:
                if task_id_val and task_id_val != "":
                    if task_type == 'Generation':
                        admin_db_handler.delete_generation_task(int(task_id_val))
                        msg = "Generation Task deleted successfully."
                    else:
                        admin_db_handler.delete_evaluation_task(int(task_id_val))
                        msg = "Evaluation Task deleted successfully."
                    # Update task options after delete
                    options = get_task_options(task_type)
                    return msg, gr.update(choices=options)
                else:
                    return "No task selected.", gr.update()
            except Exception as e:
                return f"Error: {str(e)}", gr.update()

        delete_button.click(
            fn=delete_task_action,
            inputs=[task_id, task_type_selector],
            outputs=[feedback, selected_task]
        )