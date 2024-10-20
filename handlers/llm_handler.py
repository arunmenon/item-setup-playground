import openai
import logging
from typing import Dict, Any
import asyncio
import time
from models.llm_request_models import BaseLLMRequest
from openai import RateLimitError, AuthenticationError, OpenAIError, APIConnectionError, Timeout
import os
from openai import OpenAI

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class BaseModelHandler:
    def __init__(self, provider: str = None, api_key: str = None, api_base: str = None, model: str = "gpt-4", max_tokens: int = None, temperature: float = 0.7):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.provider = provider
        self.client = self._initialize_client(api_key, api_base)

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def _initialize_client(self, api_key: str, api_base: str):
        if self.provider == "runpod":
            return self._initialize_runpod_client()
        elif self.provider == "openai":
            return self._initialize_openai_client(api_key, api_base)
        else:
            raise ValueError("Unsupported provider specified.")

    def _initialize_runpod_client(self):
        runpod_access_key = os.getenv("RUNPOD_ACCESS_KEY")
        runpod_endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")
        if runpod_access_key and runpod_endpoint_id:
            return OpenAI(
                api_key=runpod_access_key,
                base_url=f"https://api.runpod.ai/v2/{runpod_endpoint_id}/openai/v1"
            )
        else:
            raise ValueError("RunPod access key or endpoint ID not found in environment variables.")

    def _initialize_openai_client(self, api_key: str, api_base: str):
        if api_key:
            openai.api_key = api_key
        if api_base:
            openai.api_base = api_base
        return openai

    async def invoke(self, request: BaseLLMRequest, llm_name: str, task: str, retries: int = 3) -> Dict[str, Any]:
        model = request.parameters.get("model") if request.parameters else self.model
        max_tokens = request.parameters.get("max_tokens") if request.parameters else self.max_tokens
        temperature = request.parameters.get("temperature") if request.parameters else self.temperature
        prompt = request.prompt

        self.logger.debug("Invoking model: %s with prompt: %s", model, prompt)

        for attempt in range(retries):
            try:
                response = await asyncio.to_thread(
                    self.client.ChatCompletion.acreate,
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                self.logger.debug("Received response: %s", response)
                return {"llm_name": llm_name, "task": task, "response": response['choices'][0]['message']['content']}
            except (APIConnectionError, Timeout) as e:
                self.logger.warning("Network-related error during model invocation, attempt %d/%d: %s", attempt + 1, retries, str(e))
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
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
