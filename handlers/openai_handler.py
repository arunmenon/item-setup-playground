from handlers.llm_handler import BaseModelHandler

class OpenAIHandler(BaseModelHandler):
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)
