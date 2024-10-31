# parsers/json_response_parser.py

import json
import logging
import re
from parsers.response_parser import ResponseParser

class JsonResponseParser(ResponseParser):
    def __init__(self):
        super().__init__()  # Assuming ResponseParser can be initialized without parameters

    def parse(self, response: str) -> dict:
        """
        Parses the JSON response from the LLM.

        Args:
            response (str): The raw response string from the LLM.

        Returns:
            dict: Parsed JSON data.
        """
        try:
            # Use regex to extract JSON content between triple backticks if present
            json_content = re.search(r'```json\s*\n?(.*?)\n?```', response, re.DOTALL)
            if json_content:
                json_str = json_content.group(1)
                logging.debug("Extracted JSON from code block.")
            else:
                json_str = response.strip()
                logging.debug("No code block found. Using stripped response.")

            if not json_str.startswith(('{', '[')):
                logging.warning("Response does not start with JSON object or array.")
                raise ValueError("Response does not contain valid JSON.")
            
            parsed_json = json.loads(json_str)
            
            return parsed_json
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")
