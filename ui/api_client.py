import requests

class APIClient:
    def __init__(self, endpoint="http://10.56.16.163:5001/enrich-item"):
        self.endpoint = endpoint

    def process_single_sku(self, gtin, title, short_desc, long_desc, product_type):
        """
        Sends a request to the enrichment API with SKU details.
        """
        payload = {
            "item_title": title,
            "short_description": short_desc,
            "long_description": long_desc,
            "item_product_type": product_type
        }
        response = requests.post(self.endpoint, json=payload)
        response.raise_for_status()
        return response.json()
