import os

def load_product_types_from_file(file_path):
    try:
        with open(file_path, 'r') as f:
            product_types = [line.strip() for line in f if line.strip()]
        return product_types
    except Exception as e:
        print(f"Error reading product types from file: {e}")
        return []
