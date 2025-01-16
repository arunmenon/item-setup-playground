# bigquery_leaderboard_handler.py

from google.cloud import bigquery
import pandas as pd

class BigQueryLeaderboardHandler:
    def __init__(self, project_id: str, dataset: str = "item_setup_playground"):
        self.client = bigquery.Client(project=project_id)
        self.dataset = dataset

    def get_leaderboard(
        self,
        dataset_id: int,
        generation_task: str = None,
        evaluation_task: str = None,
        product_type: str = None
    ) -> pd.DataFrame:
        """
        Query evaluation_results, parse 'score' from evaluation_data JSON,
        and produce a grouped/aggregated leaderboard.
        """
        table = f"`{self.client.project}.{self.dataset}.evaluation_results`"
        
        query = f"""
        WITH parsed AS (
          SELECT
            product_identifier_id,
            item_product_type,
            generation_task,
            evaluation_task,
            model_name,
            model_version,
            CAST(JSON_VALUE(evaluation_data, '$.score') AS FLOAT64) AS score,
            dataset_id
          FROM {table}
          WHERE dataset_id = @dataset_id
        """

        # If generation_task is specified, filter
        if generation_task and generation_task != "All":
            query += " AND generation_task = @generation_task"

        # If evaluation_task is specified, filter
        if evaluation_task and evaluation_task != "All":
            query += " AND evaluation_task = @evaluation_task"

        # If product_type is specified, filter
        if product_type and product_type != "All":
            query += " AND item_product_type = @product_type"

        query += """
        )
        SELECT
          item_product_type,
          generation_task,
          evaluation_task,
          model_name,
          model_version,
          AVG(score) AS avg_score,
          COUNT(*) AS num_evaluations
        FROM parsed
        GROUP BY
          item_product_type,
          generation_task,
          evaluation_task,
          model_name,
          model_version
        ORDER BY
          avg_score DESC
        """

        query_params = [
            bigquery.ScalarQueryParameter("dataset_id", "INT64", dataset_id)
        ]
        if generation_task and generation_task != "All":
            query_params.append(bigquery.ScalarQueryParameter("generation_task", "STRING", generation_task))
        if evaluation_task and evaluation_task != "All":
            query_params.append(bigquery.ScalarQueryParameter("evaluation_task", "STRING", evaluation_task))
        if product_type and product_type != "All":
            query_params.append(bigquery.ScalarQueryParameter("product_type", "STRING", product_type))

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        df = self.client.query(query, job_config=job_config).to_dataframe()
        return df
