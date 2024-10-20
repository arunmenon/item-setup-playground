import openai
import logging
from typing import Dict, Any
import asyncio
import time
from models.llm_request_models import BaseLLMRequest
from openai import RateLimitError, AuthenticationError, OpenAIError, APIConnectionError, Timeout
import os
from openai import OpenAI
from providers.provider_factory import ProviderFactory

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class BaseModelHandler:
    def __init__(self, provider: str = None,  model: str = "gpt-4", max_tokens: int = None, temperature: float = 0.7):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.provider = ProviderFactory.create_provider(provider)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def invoke(self, request: BaseLLMRequest, llm_name: str, task: str, retries: int = 3) -> Dict[str, Any]:
        model = request.parameters.get("model") if request.parameters else self.model
        max_tokens = request.parameters.get("max_tokens") if request.parameters else self.max_tokens
        temperature = request.parameters.get("temperature") if request.parameters else self.temperature
        prompt = request.prompt

        self.logger.debug("Invoking model: %s with prompt: %s", model, prompt)

        return await self._retry_logic(model, prompt, temperature, max_tokens, llm_name, task, retries)

    async def _retry_logic(self, model: str, prompt: str, temperature: float, max_tokens: int, llm_name: str, task: str, retries: int) -> Dict[str, Any]:
        for attempt in range(retries):
            try:
                response = await asyncio.to_thread(
                    self.provider.create_chat_completion,
                    model,
                    [{"role": "user", "content": prompt}],
                    temperature,
                    max_tokens
                )
                self.logger.info("Received response: %s", response)
                return {"llm_name": llm_name, "task": task, "response": response['choices'][0]['message']['content']}
            except (APIConnectionError, Timeout) as e:
                self.logger.warning("Network-related error during model invocation, attempt %d/%d: %s", attempt + 1, retries, str(e))
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    self.logger.error("Failed after %d attempts: %s", retries, str(e))
                    raise
            except RateLimitError as e:
                self.logger.error("Rate limit exceeded for model: %s", e)
                raise
            except AuthenticationError as e:
                self.logger.error("Authentication error for model: %s", e)
                raise
            except OpenAIError as e:
                self.logger.error("General OpenAI API error for model: %s", e)
                raise
            except Exception as e:
                self.logger.error(f"Caught an exception of type: {type(e)}")
                raise
