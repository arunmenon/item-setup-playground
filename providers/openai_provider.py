# providers/openai_provider.py
import json
import os
import logging
import httpx
import requests
from providers.base_provider import BaseProvider


class OpenAIProvider(BaseProvider):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.use_elements_llm = True
        self.base_api = os.getenv("ELEMENTS_API_BASE", "https://wmtllmgateway.prod.walmart.com/wmtllmgateway/v1/openai")
        self.api_key = os.getenv("ELEMENTS_API_KEY")
        self.client = self.setup_http_client(self.api_key)

    def setup_http_client(self, api_key: str) -> httpx.Client:
        ca_bundle_path = os.getenv("WMT_CA_PATH")
        cert_file_name = "ca-bundle.crt"
        self.resolved_file_path = os.path.join(ca_bundle_path, cert_file_name)
        self.headers = {
            "X-Api-Key"   : api_key,
            "Content-Type": "application/json"
        }


    def create_chat_completion(self, model: str, messages: list, temperature: float, max_tokens: int):
        payload = {
            "model"            : model,
            "task"             : "chat/completions",
            "api-version"      : '2024-02-01',
            "model-params"     : {
                "messages": messages
            },
            "temperature"      : temperature,
            "max_tokens"       : max_tokens,
            "top_p"            : 0.95,
            "frequency_penalty": 0,
            "presence_penalty" : 0,
            "stop"             : None
        }

        try:
            response = requests.request("POST", self.base_api, headers=self.headers, data=json.dumps(payload), verify=self.resolved_file_path)
            response_data = response.json()
            content = response_data['choices'][0]['message']['content']
            return {"choices": [{"message": {"content": content}}]}
        except BaseException as e:
            self.logger.error("Error creating OpenAI chat completion: %s", str(e))
            raise
