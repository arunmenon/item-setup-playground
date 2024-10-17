# openai_handler.py
import openai
import logging
from typing import Dict, Any
import os
import asyncio

logging.basicConfig(level=logging.DEBUG)

class OpenAIHandler:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

    async def invoke(self, prompt: str, llm_name: str, task: str, model: str = "gpt-4") -> Dict[str, Any]:
        logging.debug("Invoking OpenAI chat with model: %s, prompt: %s", model, prompt)
        try:
            response = await self._openai_chat_async(prompt, model)
            logging.debug("OpenAI chat response: %s", response)
            return {"llm_name": llm_name, "task": task, "response": response}
        except openai.error.RateLimitError as e:
            logging.error("Rate limit exceeded for OpenAI: %s", e)
            return {"llm_name": llm_name, "task": task, "response": {"error": "Rate limit exceeded. Please try again later.", "details": str(e)}}
        except openai.error.AuthenticationError as e:
            logging.error("Authentication error for OpenAI: %s", e)
            return {"llm_name": llm_name, "task": task, "response": {"error": "Authentication error. Please check your credentials.", "details": str(e)}}
        except openai.error.OpenAIError as e:
            logging.error("OpenAI API error: %s", e)
            return {"llm_name": llm_name, "task": task, "response": {"error": "OpenAI API error", "details": str(e)}}
        except Exception as e:
            logging.error("Unexpected error while invoking OpenAI chat: %s", e)
            return {"llm_name": llm_name, "task": task, "response": {"error": str(e)}}

    async def _openai_chat_async(self, prompt: str, model: str) -> Dict[str, Any]:
        logging.debug("Running OpenAI chat asynchronously with model: %s", model)
        return await asyncio.to_thread(self._openai_chat, prompt, model)

    def _openai_chat(self, prompt: str, model: str) -> Dict[str, Any]:
        logging.debug("Running OpenAI chat with prompt: %s and model: %s", prompt, model)
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        logging.debug("Received OpenAI response: %s", response)
        return response.choices[0].message["content"]
