# File: bigquery_leaderboard_handler.py

from google.cloud import bigquery
import pandas as pd

class BigQueryLeaderboardHandler:
    def __init__(self, project_id: str, dataset: str = "item_setup_playground"):
        """
        Args:
            project_id: GCP project (e.g. "wmt-rg-dev").
            dataset:    BigQuery dataset name ("item_setup_playground" by default).
        """
        self.client = bigquery.Client(project=project_id)
        self.dataset = dataset

    def get_leaderboard(
        self,
        dataset_id: int,
        product_type: str = None,
        generation_task: str = None,
    ) -> pd.DataFrame:
        """
        Query wmt-rg-dev.item_setup_playground.evaluation_results, parse 'score' from evaluation_data JSON.
        Return DataFrame with columns:
            item_product_type, generation_task, model_name, model_version, avg_score, num_evaluations
        ordered by avg_score DESC.
        """
        table = f"`{self.client.project}.{self.dataset}.evaluation_results`"
        
        # We'll parse the 'score' from JSON in a CTE
        query = f"""
        WITH parsed AS (
          SELECT
            product_identifier_id,
            item_product_type,
            generation_task,
            model_name,
            model_version,
            CAST(JSON_VALUE(evaluation_data, '$.score') AS FLOAT64) AS score,
            dataset_id
          FROM {table}
          WHERE dataset_id = @dataset_id
        """

        # Additional optional filters
        if product_type and product_type != "All":
            query += " AND item_product_type = @product_type"
        if generation_task and generation_task != "All":
            query += " AND generation_task = @generation_task"

        query += """
        )
        SELECT
          item_product_type,
          generation_task,
          model_name,
          model_version,
          AVG(score) AS avg_score,
          COUNT(*) AS num_evaluations
        FROM parsed
        GROUP BY
          item_product_type,
          generation_task,
          model_name,
          model_version
        ORDER BY
          avg_score DESC
        """

        query_params = [
            bigquery.ScalarQueryParameter("dataset_id", "INT64", dataset_id),
        ]
        if product_type and product_type != "All":
            query_params.append(bigquery.ScalarQueryParameter("product_type", "STRING", product_type))
        if generation_task and generation_task != "All":
            query_params.append(bigquery.ScalarQueryParameter("generation_task", "STRING", generation_task))

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        df = self.client.query(query, job_config=job_config).to_dataframe()
        return df
