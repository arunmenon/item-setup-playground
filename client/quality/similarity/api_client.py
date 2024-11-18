# api_client.py

import aiohttp
import asyncio
import logging
from tqdm import tqdm

# Asynchronous method with concurrency limit
async def fetch_single_response(semaphore, session, item, payload, api_endpoint):
    async with semaphore:
        try:
            async with session.post(api_endpoint, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data, item
                else:
                    logging.error(
                        f"Failed to get response for SKU {item.get('SKU')} with status code {response.status}"
                    )
                    return None, item
        except Exception as e:
            logging.error(f"Request failed for SKU {item.get('SKU')}: {e}")
            return None, item

async def fetch_model_responses_async(sku_data, api_endpoint, max_concurrent_requests=5):
    results = []
    semaphore = asyncio.Semaphore(max_concurrent_requests)  # Limit concurrency
    async with aiohttp.ClientSession() as session:
        tasks = []
        for item in sku_data:
            required_fields = ["Title", "Short_Description", "Long_Description", "Product_Type"]
            if not all(field in item and item[field] for field in required_fields):
                logging.warning(f"Missing required fields for SKU {item.get('SKU')}")
                continue
            payload = {
                "item_title": item["Title"],
                "short_description": item["Short_Description"],
                "long_description": item["Long_Description"],
                "item_product_type": item["Product_Type"]
            }
            tasks.append(
                fetch_single_response(semaphore, session, item, payload, api_endpoint)
            )
        for future in tqdm(
            asyncio.as_completed(tasks), total=len(tasks), desc="Processing SKUs", unit="SKU"
        ):
            data, item = await future
            if data:
                results.append((data, item))
    return results

# Serial method
async def fetch_single_response_serial(session, item, payload, api_endpoint):
    try:
        async with session.post(api_endpoint, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data, item
            else:
                logging.error(
                    f"Failed to get response for SKU {item.get('SKU')} with status code {response.status}"
                )
                return None, item
    except Exception as e:
        logging.error(f"Request failed for SKU {item.get('SKU')}: {e}")
        return None, item

async def fetch_model_responses_serial(sku_data, api_endpoint):
    results = []
    async with aiohttp.ClientSession() as session:
        for item in tqdm(sku_data, desc="Processing SKUs", unit="SKU"):
            required_fields = ["Title", "Short_Description", "Long_Description", "Product_Type"]
            if not all(field in item and item[field] for field in required_fields):
                logging.warning(f"Missing required fields for SKU {item.get('SKU')}")
                continue
            payload = {
                "item_title": item["Title"],
                "short_description": item["Short_Description"],
                "long_description": item["Long_Description"],
                "item_product_type": item["Product_Type"]
            }
            data, item = await fetch_single_response_serial(session, item, payload, api_endpoint)
            if data:
                results.append((data, item))
    return results
