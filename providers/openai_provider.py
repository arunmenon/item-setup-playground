# providers/openai_provider.py
import os
import openai
import logging

from providers.base_provider import BaseProvider

class OpenAIProvider(BaseProvider):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def create_chat_completion(self, model: str, messages: list, temperature: float, max_tokens: int):
        try:
            response = openai.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            content = response.choices[0].message.content
            return {"choices": [{"message": {"content": content}}]}
        except Exception as e:
            self.logger.error("Error creating OpenAI chat completion: %s", str(e))
            raise