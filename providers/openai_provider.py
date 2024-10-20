# providers/openai_provider.py
import openai
import logging

from providers.base_provider import BaseProvider

class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str, api_base: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        openai.api_key = api_key
        openai.api_base = api_base

    def create_chat_completion(self, model: str, messages: list, temperature: float, max_tokens: int):
        try:
            response = openai.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response
        except Exception as e:
            self.logger.error("Error creating OpenAI chat completion: %s", str(e))
            raise