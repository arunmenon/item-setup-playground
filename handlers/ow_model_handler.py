# open_weights_model_handler.py
import openai
import logging
from typing import Dict, Any
import asyncio
import re
from urllib.parse import urlparse
import time

logging.basicConfig(level=logging.DEBUG)

class OpenWeightsModelHandler:
    def __init__(self, endpoint: str, model: str = "gpt-4"):
        if not self._is_valid_url(endpoint):
            raise ValueError(f"Invalid endpoint URL: {endpoint}")
        self.endpoint = endpoint
        self.model = model
        openai.api_base = endpoint

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        parsed = urlparse(url)
        return all([parsed.scheme, parsed.netloc])

    async def invoke(self, prompt: str, llm_name: str, task: str) -> Dict[str, Any]:
        logging.debug("Invoking open weights model chat at endpoint: %s with prompt: %s", self.endpoint, prompt)
        retries = 3
        for attempt in range(retries):
            try:
                response = await self._openai_chat_async(prompt)
                logging.debug("open weights model response: %s", response)
                return {"llm_name": llm_name, "task": task, "response": response}
            except (openai.error.APIConnectionError, openai.error.Timeout) as e:
                logging.warning("Network-related error during open weights model invocation, attempt %d/%d: %s", attempt + 1, retries, e)
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    logging.error("Failed after %d attempts: %s", retries, e)
                    return {"llm_name": llm_name, "task": task, "response": {"error": "Network error. Please try again later.", "details": str(e)}}
            except openai.error.RateLimitError as e:
                logging.error("Rate limit exceeded at open weights model endpoint: %s", e)
                return {"llm_name": llm_name, "task": task, "response": {"error": "Rate limit exceeded. Please try again later.", "details": str(e)}}
            except openai.error.AuthenticationError as e:
                logging.error("Authentication error at open weights model endpoint: %s", e)
                return {"llm_name": llm_name, "task": task, "response": {"error": "Authentication error. Please check your credentials.", "details": str(e)}}
            except openai.error.OpenAIError as e:
                logging.error("General OpenAI API error at open weights model endpoint: %s", e)
                return {"llm_name": llm_name, "task": task, "response": {"error": "OpenAI API error", "details": str(e)}}
            except Exception as e:
                logging.error("Unexpected error while invoking open weights model chat: %s", e)
                return {"llm_name": llm_name, "task": task, "response": {"error": str(e)}}

    async def _openai_chat_async(self, prompt: str) -> Dict[str, Any]:
        logging.debug("Running open weights model chat asynchronously with prompt: %s", prompt)
        try:
            return await asyncio.wait_for(asyncio.to_thread(self._openai_chat, prompt), timeout=30)
        except asyncio.TimeoutError:
            logging.error("Timeout occurred while running open weights model chat asynchronously with prompt: %s", prompt)
            raise

    def _openai_chat(self, prompt: str) -> Dict[str, Any]:
        logging.debug("Running open weights model chat with prompt: %s", prompt)
        try:
            response = openai.ChatCompletion.create(
                model=self.model,  # Configurable model
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            logging.debug("Received open weights model response: %s", response)
            return response.choices[0].message["content"]
        except openai.error.RateLimitError as e:
            logging.error("Rate limit error during open weights model invocation: %s", e)
            raise e
        except openai.error.AuthenticationError as e:
            logging.error("Authentication error during open weights model invocation: %s", e)
            raise e
        except openai.error.OpenAIError as e:
            logging.error("General OpenAI API error during open weights model invocation: %s", e)
            raise e
