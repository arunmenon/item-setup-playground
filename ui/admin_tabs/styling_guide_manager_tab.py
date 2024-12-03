from models.models import StylingGuide


import gradio as gr


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