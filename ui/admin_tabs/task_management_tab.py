from models.models import EvaluationTask, GenerationTask
import gradio as gr
import json

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

        # Dataframe for metrics configuration (only for Evaluation tasks)
        # Columns: name, type, range, required (bool), categories (comma-separated)
        metrics_table = gr.Dataframe(
            headers=["name", "type", "range", "required", "categories"],
            row_count=3,
            col_count=5,
            type="array",
            visible=False,  # Initially hidden; will be shown if Evaluation is selected
            interactive=True
        )

        with gr.Row():
            save_button = gr.Button("Save", variant="primary")
            delete_button = gr.Button("Delete", variant="stop", visible=False)

        feedback = gr.Markdown("")

        # Update form when task type changes
        def update_form(task_type):
            options = get_task_options(task_type)
            # If Evaluation, show metrics_table
            show_metrics = True if task_type == 'Evaluation' else False
            return (gr.update(choices=options, value=None), 
                    "", "", "", "JSON", 
                    gr.update(visible=False),  # delete_button
                    "", 
                    gr.update(visible=show_metrics) # metrics_table visibility
                   )

        task_type_selector.change(
            fn=update_form,
            inputs=[task_type_selector],
            outputs=[selected_task, task_name, description, max_tokens, output_format, delete_button, feedback, metrics_table]
        )

        # Load task details when existing task is selected
        def load_task(task_name_val, task_type_val):
            tasks = get_task_options(task_type_val)
            show_metrics = (task_type_val == 'Evaluation')
            if task_name_val in tasks:
                task_model = GenerationTask if task_type_val=='Generation' else EvaluationTask
                task = admin_db_handler.db_session.query(task_model).filter_by(task_name=task_name_val).first()
                if task:
                    # If it's an evaluation task, try to load existing expected_metrics
                    metrics_data = []
                    if task_type_val == 'Evaluation' and hasattr(task, 'expected_metrics') and task.expected_metrics:
                        # expected_metrics is assumed to be JSON with "metrics" key
                        # Format: {"metrics": [{"name":...,"type":...}, ...]}
                        # Convert it back to list of rows for the dataframe
                        em = json.loads(task.expected_metrics)
                        for m in em.get("metrics", []):
                            row = [
                                m.get("name", ""),
                                m.get("type", ""),
                                m.get("range", ""),
                                m.get("required", False),
                                ", ".join(m.get("categories", [])) if "categories" in m else ""
                            ]
                            metrics_data.append(row)

                    return (str(task.task_id), 
                            task.task_name, 
                            task.description or "", 
                            str(task.max_tokens) if task.max_tokens else "", 
                            task.output_format or "JSON", 
                            gr.update(visible=True),  # delete_button
                            "", # feedback
                            gr.update(value=metrics_data, visible=show_metrics)
                           )
            # If no task found or new creation scenario
            return ("", task_name_val, "", "", "JSON", gr.update(visible=False), "Ready to create a new task.", gr.update(visible=(task_type_val=='Evaluation'), value=[]))

        selected_task.change(
            fn=load_task,
            inputs=[selected_task, task_type_selector],
            outputs=[task_id, task_name, description, max_tokens, output_format, delete_button, feedback, metrics_table]
        )

        def convert_table_to_json(data):
            metrics = []
            for row in data:
                # row: name, type, range, required, categories
                if not any(row):
                    continue
                metric = {
                    "name": row[0].strip() if row[0] else "",
                    "type": row[1].strip() if row[1] else ""
                }
                if metric["type"] == "integer":
                    metric["range"] = row[2].strip() if row[2] else ""
                # required is boolean
                metric["required"] = bool(row[3]) if row[3] else False

                if metric["type"] == "categorical":
                    categories_str = row[4].strip() if row[4] else ""
                    categories = [c.strip() for c in categories_str.split(",") if c.strip()]
                    metric["categories"] = categories
                metrics.append(metric)
            return json.dumps({"metrics": metrics}, indent=2)

        # Save task
        def save_task(task_id_val, task_name_val, description_val, max_tokens_val, output_format_val, task_type_val, metrics_data):
            if not task_name_val.strip():
                return "Task Name cannot be empty.", gr.update()
            try:
                max_tokens_int = int(max_tokens_val) if max_tokens_val else None
                task_data = {
                    "task_name": task_name_val,
                    "description": description_val,
                    "max_tokens": max_tokens_int,
                    "output_format": output_format_val
                }

                # If Evaluation, add expected_metrics field
                if task_type_val == 'Evaluation':
                    metrics_json = convert_table_to_json(metrics_data)
                    task_data["expected_metrics"] = metrics_json

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
            inputs=[task_id, task_name, description, max_tokens, output_format, task_type_selector, metrics_table],
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
