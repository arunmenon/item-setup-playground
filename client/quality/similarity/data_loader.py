# data_loader.py

import csv
import logging

def load_sku_data(filename):
    sku_data = []
    try:
        with open(filename, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                sku_data.append(row)
    except FileNotFoundError:
        logging.error(f"File {filename} not found.")
    except Exception as e:
        logging.error(f"An error occurred while loading SKU data: {e}")
    return sku_data
