import gradio as gr
from models.models import GenerationTask, EvaluationTask, ProviderConfig

def create_task_mapping_tab(admin_db_handler):
    with gr.TabItem("Task Mappings"):
        gr.Markdown("## Manage Task Mappings")

        # Select Generation Task
        gen_task_options = [t.task_name for t in admin_db_handler.get_generation_tasks()]
        selected_gen_task = gr.Dropdown(
            label="Select Generation Task:",
            choices=gen_task_options,
            value=None,
            interactive=True
        )

        # Select Evaluation Tasks to map to the Generation Task
        eval_task_options = [t.task_name for t in admin_db_handler.get_evaluation_tasks()]
        selected_eval_tasks = gr.CheckboxGroup(
            label="Associated Evaluation Tasks:",
            choices=eval_task_options,
            value=[],
            interactive=True
        )

        # Select Providers to associate with the Generation Task
        provider_options = [p.name for p in admin_db_handler.get_providers()]
        selected_providers = gr.CheckboxGroup(
            label="Associated Providers:",
            choices=provider_options,
            value=[],
            interactive=True
        )

        save_mappings_button = gr.Button("Save Mappings", variant="primary")
        feedback = gr.Markdown("")

        # Load existing mappings when a generation task is selected
        def load_mappings(gen_task_name):
            if not gen_task_name:
                return [], [], "Please select a Generation Task."
            # Fetch associated evaluation tasks and providers
            gen_task = admin_db_handler.db_session.query(GenerationTask).filter_by(task_name=gen_task_name).first()
            if not gen_task:
                return [], [], "Generation Task not found."
            # Fetch associated evaluation tasks
            eval_tasks = [et.task_name for et in gen_task.evaluation_tasks]
            # Fetch associated providers
            providers = [p.name for p in gen_task.providers]
            return eval_tasks, providers, f"Loaded mappings for '{gen_task_name}'."

        selected_gen_task.change(
            fn=load_mappings,
            inputs=[selected_gen_task],
            outputs=[selected_eval_tasks, selected_providers, feedback]
        )

        # Save mappings
        def save_mappings(gen_task_name, eval_task_names, provider_names):
            if not gen_task_name:
                return "Please select a Generation Task."
            try:
                gen_task = admin_db_handler.db_session.query(GenerationTask).filter_by(task_name=gen_task_name).first()
                if not gen_task:
                    return "Generation Task not found."

                # Update evaluation task mappings
                gen_task.evaluation_tasks = []
                for eval_task_name in eval_task_names:
                    eval_task = admin_db_handler.db_session.query(EvaluationTask).filter_by(task_name=eval_task_name).first()
                    if eval_task:
                        gen_task.evaluation_tasks.append(eval_task)

                # Update provider mappings
                gen_task.providers = []
                for provider_name in provider_names:
                    provider = admin_db_handler.db_session.query(ProviderConfig).filter_by(name=provider_name).first()
                    if provider:
                        gen_task.providers.append(provider)

                admin_db_handler.db_session.commit()
                return f"Mappings for '{gen_task_name}' saved successfully."
            except Exception as e:
                return f"Error: {str(e)}"

        save_mappings_button.click(
            fn=save_mappings,
            inputs=[selected_gen_task, selected_eval_tasks, selected_providers],
            outputs=[feedback]
        )
