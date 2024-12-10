# bigquery_input_handler.py

from google.cloud import bigquery
import logging
import pandas as pd

class BigQueryInputHandler:
    def __init__(self, project, dataset, table, dataset_id, batch_size=1000):
        self.client = bigquery.Client(project=project)
        self.table = f"{project}.{dataset}.{table}"
        self.dataset_id = dataset_id
        self.batch_size = batch_size
        self.offset = 0
        self.total_rows = None

    def load_next_batch(self):
        if self.total_rows is not None and self.offset >= self.total_rows:
            return None

        query = f"""
        SELECT * FROM `{self.table}`
        WHERE dataset_id = @dataset_id
        ORDER BY item_id
        LIMIT {self.batch_size} OFFSET {self.offset}
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("dataset_id", "INT64", self.dataset_id)]
        )

        query_job = self.client.query(query, job_config=job_config)
        df = query_job.to_dataframe()
        if self.total_rows is None:
            self.total_rows = query_job.total_rows

        self.offset += len(df)
        if df.empty:
            return None
        return df
