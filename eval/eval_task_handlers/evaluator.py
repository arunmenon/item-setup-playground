import logging
import json
from models.llm_request_models import BaseLLMRequest
from parsers.parser_factory import ParserFactory


class Evaluator:
    def __init__(self, task_mapping, template_renderer, styling_guide_manager, handler):
        self.task_mapping = task_mapping
        self.template_renderer = template_renderer
        self.styling_guide_manager = styling_guide_manager
        self.handler = handler  # Injected dependency for model invocation

    async def evaluate_task(self, item_data, product_type, task, model_name, enriched_content):
        """
        Evaluate the enriched content for a specific task using the LLM handler.

        Args:
            item_data (dict): The item data being processed.
            product_type (str): The product type (e.g., "T-Shirts").
            task (str): The task to evaluate (e.g., "title").
            model_name (str): The name of the LLM model.
            enriched_content (str): The enriched content to evaluate.

        Returns:
            dict: A structured evaluation result, or None if an error occurs.
        """
        logging.debug(f"Evaluating  '{task}' generated  for item '{item_data['item_id']}'  using model '{model_name}'")
        try:
            # Fetch the styling guide for the given product type and task
            styling_guide = self.styling_guide_manager.get_styling_guide(product_type, self.task_mapping[task])

            # Render the evaluation prompt
            context = {
                'response_content': enriched_content,
                'styling_guide': styling_guide
            }
            prompt = self.template_renderer.render_template(f'{task}_eval.jinja2', context)

            logging.debug(f"Generated prompt: {prompt}")

            # Invoke the LLM handler asynchronously
            response = await self.handler.invoke(
                request=BaseLLMRequest(prompt=prompt, parameters={'max_tokens': 2400}), task=f'{task}_eval'
            )

            logging.debug(f"LLM Eval handler response for model {model_name} for {task}: {response}")

            # Parse and return the LLM's response
            return self.parse_llm_response(response.get('response', ''))
        except Exception as e:
            logging.error(f"Error evaluating task '{task}' for item '{item_data['item_id']}': {e}")
            return None

    def parse_llm_response(self, response_text):
        logging.debug(f"Raw LLM response: {response_text}")
        try:
            parser = ParserFactory.get_parser("json")
            parsed = parser.parse(response_text)
            # parsed = json.loads(response_text)
            return {
                "quality_score": parsed.get("quality_score"),
                "reasoning": {
                    "adherence_to_style_guide": parsed.get("reasoning", {}).get("adherence_to_style_guide", "No reasoning provided."),
                    "clarity": parsed.get("reasoning", {}).get("clarity", "No reasoning provided."),
                    "relevance": parsed.get("reasoning", {}).get("relevance", "No reasoning provided."),
                    "length": parsed.get("reasoning", {}).get("length", "No reasoning provided."),
                    "keywords": parsed.get("reasoning", {}).get("keywords", "No reasoning provided.")
                },
                "suggestions": parsed.get("suggestions", "No suggestions provided.")
            }
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM response: {e}")
            return {
                "quality_score": None,
                "reasoning": "Parsing error",
                "suggestions": "Parsing error",
            }

