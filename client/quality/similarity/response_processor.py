# response_processor.py

import logging

def process_responses(responses):
    processed_results = []
    model_names = set()
    for data, item in responses:
        for task, handlers in data.items():
            task_results = {"SKU": item.get("SKU"), "GTIN": item.get("GTIN"), "Task": task}
            for handler_name, handler_response in handlers.items():
                response_text = handler_response.get("response")
                error_message = handler_response.get("error")

                if response_text and error_message is None:
                    enhanced_title = response_text.get("enhanced_title") if isinstance(response_text, dict) else "NA"
                    task_results[handler_name] = enhanced_title
                else:
                    logging.error(f"Error from {handler_name} for SKU {item.get('SKU')}: {error_message}")
                    task_results[handler_name] = "NA"
                model_names.add(handler_name)
            processed_results.append(task_results)
    return processed_results, model_names
