# config.py

from argparse import ArgumentParser

def parse_args():
    parser = ArgumentParser(description="Process SKU data and compute similarity scores.")
    parser.add_argument('--input_file', default='enhanced_input_skus.csv', help='Input CSV file with SKU data.')
    parser.add_argument('--api_endpoint', default='http://localhost:5000/enrich-item', help='API endpoint to fetch model responses.')
    parser.add_argument('--max_concurrent_requests', type=int, default=1, help='Maximum number of concurrent API requests.')
    parser.add_argument('--serial', action='store_true', help='Process requests serially.')

    return parser.parse_args()
