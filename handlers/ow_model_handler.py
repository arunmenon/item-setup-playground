from urllib.parse import urlparse
from handlers.llm_handler import BaseModelHandler


class OpenWeightsModelHandler(BaseModelHandler):
    def __init__(self, endpoint: str, max_tokens: int = None, temperature: float = 0.7):
        if not self._is_valid_url(endpoint):
            raise ValueError(f"Invalid endpoint URL: {endpoint}")
        super().__init__(api_base=endpoint, max_tokens=max_tokens, temperature=temperature)

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        parsed = urlparse(url)
        return all([parsed.scheme, parsed.netloc])