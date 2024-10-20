# llm_request_models.py
from pydantic import BaseModel
from typing import Dict, List, Union, Optional

class BaseLLMRequest(BaseModel):
    """
    Base request model for interacting with LLMs.

    Attributes:
        prompt (str): The input prompt to be sent to the LLM.
        parameters (Optional[Dict[str, Union[str, int, float]]]): Additional parameters for LLM configuration.
    """
    prompt: str
    parameters: Optional[Dict[str, Union[str, int, float]]] = None

class LLMRequest(BaseModel):
    """
    Request model for enriching an item using multiple LLMs.

    Attributes:
        metadata (Dict[str, Union[str, int, float, List[str]]]): A dictionary containing metadata about the item to be enriched.
        tasks (List[str]): A list of tasks to be performed on the metadata by the LLMs.
    """
    metadata: Dict[str, Union[str, int, float, List[str]]]
    tasks: List[str]

class GPT4Request(BaseLLMRequest):
    """
    Request model for interacting with GPT-4.
    
    Inherits from BaseLLMRequest and includes attributes specific to GPT-4 requests.
    """
    model: str = "gpt-4"
