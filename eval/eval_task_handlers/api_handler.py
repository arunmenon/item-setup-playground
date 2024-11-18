import requests
import logging
import time


class APIHandler:
    def __init__(self, api_url):
        self.api_url = api_url

    def call_api(self, item_data, retries=3, delay=2):
        """
        Calls the enrichment API with the provided item data, retries if needed.

        Args:
            item_data (dict): The data to send to the API.
            retries (int): Number of retry attempts for failed API calls.
            delay (int): Delay (in seconds) between retries.

        Returns:
            dict: The API response as a JSON object if successful, or an empty dict otherwise.
        """
        for attempt in range(retries):
            try:
                logging.info(f"Calling API for item {item_data['item_id']} (Attempt {attempt + 1})")
                response = requests.post(self.api_url, json=item_data)

                if response.status_code == 200:
                    logging.info(f"API call succeeded for item {item_data['item_id']}")
                    return response.json()
                elif response.status_code == 429:  # Handle rate limiting
                    logging.warning(f"Rate limited. Retrying after {delay} seconds.")
                    time.sleep(delay)
                else:
                    logging.error(f"API failed for item '{item_data['item_id']}': {response.text}")
            except requests.exceptions.RequestException as e:
                logging.error(f"API connection failed for item '{item_data['item_id']}': {e}")
                time.sleep(delay)

        # Return an empty dict if all retries fail
        return {}
