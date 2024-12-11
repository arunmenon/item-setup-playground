from typing import Dict, Any, List, Tuple
from google.cloud import bigquery
from .query_builder import QueryBuilder

class ItemInputFetcher:
    """
    Fetches item input data from the task_input table.
    """
    def __init__(self, bq_client: bigquery.Client, project_id: str, dataset_id: str):
        self.bq_client = bq_client
        self.project_id = project_id
        self.dataset_id = dataset_id

    def fetch_item_inputs(self, dataset_item_pairs: List[Tuple[int,int]]) -> Dict[Tuple[int,int], Dict[str,Any]]:
        if not dataset_item_pairs:
            return {}

        query = QueryBuilder.build_task_input_query(self.project_id, self.dataset_id, dataset_item_pairs)
        if not query.strip():
            return {}
        results = self.bq_client.query(query).result()
        input_map = {}
        for row in results:
            key = (row.dataset_id, row.item_id)
            input_map[key] = {
                'product_type': (row.product_type.lower() if row.product_type else 'unknown'),
                'item_title': row.title or '',
                'short_description': row.short_desc or '',
                'long_description': row.long_desc or ''
            }
        return input_map
