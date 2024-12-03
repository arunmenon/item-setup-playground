import logging
import json
from models.llm_request_models import BaseLLMRequest
from models.models import GenerationTask, EvaluationTask, EvaluationPromptTemplate


class Evaluator:
    def __init__(self, db_session, template_renderer, styling_guide_manager, handler, evaluator_id):
        self.db_session = db_session
        self.template_renderer = template_renderer
        self.styling_guide_manager = styling_guide_manager
        self.handler = handler
        self.id = evaluator_id

    async def evaluate_task(self, item_data, product_type, generation_task_name, model_name, enriched_content, evaluator_id=None):
        evaluator_id = evaluator_id or self.id
        logging.debug(f"Evaluating content for generation task '{generation_task_name}' with evaluator '{evaluator_id}'")

        try:
            # Fetch the GenerationTask from the database
            gen_task = self.db_session.query(GenerationTask).filter_by(task_name=generation_task_name).first()
            if not gen_task:
                logging.error(f"Generation task '{generation_task_name}' not found.")
                return []

            # Fetch associated EvaluationTasks
            eval_tasks = gen_task.evaluation_tasks

            evaluation_results = []
            for eval_task in eval_tasks:
                # Fetch the latest EvaluationPromptTemplate
                template = self.db_session.query(EvaluationPromptTemplate).filter_by(
                    task_id=eval_task.task_id
                ).order_by(EvaluationPromptTemplate.version.desc()).first()

                if not template:
                    logging.warning(f"No template found for evaluation task '{eval_task.task_name}'.")
                    continue

                # Get placeholders from the template
                placeholders = template.placeholders or []

                # Prepare context dynamically
                context = {}
                missing_placeholders = []
                for placeholder in placeholders:
                    if placeholder=='output':
                        context['output'] = enriched_content
                    elif placeholder=='styling_guide':
                        styling_guide = self.styling_guide_manager.get_styling_guide(product_type, generation_task_name)
                        context['styling_guide'] = styling_guide
                    elif placeholder in item_data:
                        context[placeholder] = item_data[placeholder]
                    else:
                        missing_placeholders.append(placeholder)

                if missing_placeholders:
                    logging.error(f"Missing placeholders for evaluation task '{eval_task.task_name}': {missing_placeholders}")
                    continue

                # Render the evaluation prompt
                prompt = self.template_renderer.render_template_from_string(template.template_text, context)

                logging.debug(f"Generated prompt for evaluation task '{eval_task.task_name}': {prompt}")

                # Invoke the LLM handler asynchronously
                response = await self.handler.invoke(
                    request=BaseLLMRequest(prompt=prompt, max_tokens=200),
                    task=eval_task.task_name
                )

                logging.debug(f"LLM response for model {model_name}, evaluation task '{eval_task.task_name}': {response}")

                # Parse and collect the LLM's response
                parsed_result = self.parse_llm_response(response.get('response', ''))

                # Collect evaluation data
                evaluation_results.append({
                    "item_id"          : item_data["item_id"],
                    "item_product_type": product_type,
                    "generation_task"  : generation_task_name,
                    "evaluation_task"  : eval_task.task_name,
                    "model_name"       : model_name,
                    "model_version"    : self.handler.model_version,
                    "evaluator_type"   : 'LLM',
                    "evaluator_id"     : evaluator_id,
                    "evaluation_data"  : parsed_result  # Store the parsed JSON output
                })
            return evaluation_results
        except Exception as e:
            logging.error(f"Error evaluating content for item '{item_data['item_id']}': {e}")
            return []

    def parse_llm_response(self, response_text):
        logging.debug(f"Raw LLM response: {response_text}")
        try:
            parsed = json.loads(response_text)
            return parsed
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM response: {e}")
            return {}