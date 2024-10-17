# llm_request_models.py
from pydantic import BaseModel
from typing import Dict, List, Union

class LLMRequest(BaseModel):
    """
    Request model for enriching an item using multiple LLMs.

    Attributes:
        metadata (Dict[str, Union[str, int, float, List[str]]]): A dictionary containing metadata about the item to be enriched.
        tasks (List[str]): A list of tasks to be performed on the metadata by the LLMs.
    """
    metadata: Dict[str, Union[str, int, float, List[str]]]
    tasks: List[str]

class GPT4Request(BaseModel):
    """
    Request model for interacting with GPT-4.

    Attributes:
        prompt (str): The input prompt to be sent to the GPT-4 model.
    """
    prompt: str
