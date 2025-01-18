# File: bigquery_leaderboard_handler.py

import logging
from google.cloud import bigquery
import pandas as pd

def build_metric_sql_snippet(metric_def):
    """
    Build a per-metric SELECT expression based on type, e.g.:
      {"name":"decision","type":"yes_no"} -> yes/no => 1/0
      {"name":"clarity","type":"integer"} -> CAST(JSON_VALUE(...))
    """
    metric_name = metric_def["name"]
    metric_type = metric_def.get("type", "float")  # fallback

    # We'll parse from evaluation_data.<metric_name>
    json_extract = f"JSON_VALUE(evaluation_data, '$.{metric_name}')"

    if metric_type in ("yes_no", "boolean"):
        # Convert yes/no => 1/0
        return f"""
        CASE
          WHEN {json_extract} = "Yes" OR {json_extract} = "True" THEN 1
          WHEN {json_extract} = "No"  OR {json_extract} = "False" THEN 0
          ELSE NULL
        END AS {metric_name}
        """
    elif metric_type == "categorical":
        cats = metric_def.get("categories", [])
        if not cats:
            return f"CAST({json_extract} AS FLOAT64) AS {metric_name}"

        case_lines = []
        for i, cat in enumerate(cats):
            case_lines.append(f'WHEN {json_extract} = "{cat}" THEN {i}')
        case_sql = "\n".join(case_lines)
        return f"""
        CASE
          {case_sql}
          ELSE NULL
        END AS {metric_name}
        """
    else:
        # integer, float, or default
        return f"CAST({json_extract} AS FLOAT64) AS {metric_name}"

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
        Single metric aggregator:
        - De-duplicates by picking the latest run for each row 
          via run_sequence_id DESC, run_date DESC (window function).
        - Then parses 'score' from evaluation_data.
        - Groups by item_product_type, model_name, etc., computing AVG(score).
        """
        table = f"`{self.client.project}.{self.dataset}.evaluation_results`"

        query = f"""
        WITH ranked AS (
          SELECT
            product_identifier_id,
            item_product_type,
            generation_task,
            evaluation_task,
            model_name,
            model_version,
            -- parse 'score' from JSON
            CAST(JSON_VALUE(evaluation_data, '$.score') AS FLOAT64) AS score,
            dataset_id,
            run_sequence_id,
            run_date,
            ROW_NUMBER() OVER (
              PARTITION BY product_identifier_id, generation_task, evaluation_task, model_name, model_version, dataset_id
              ORDER BY run_sequence_id DESC, run_date DESC
            ) AS rn
          FROM {table}
          WHERE dataset_id = @dataset_id
        """

        # optional filters
        if generation_task and generation_task != "All":
            query += " AND generation_task = @generation_task"
        if evaluation_task and evaluation_task != "All":
            query += " AND evaluation_task = @evaluation_task"
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
        FROM ranked
        WHERE rn = 1   -- keep only the latest row per group
        GROUP BY
          item_product_type,
          generation_task,
          evaluation_task,
          model_name,
          model_version
        ORDER BY
          avg_score DESC
        """

        params = [
            bigquery.ScalarQueryParameter("dataset_id", "INT64", dataset_id)
        ]
        if generation_task and generation_task != "All":
            params.append(bigquery.ScalarQueryParameter("generation_task", "STRING", generation_task))
        if evaluation_task and evaluation_task != "All":
            params.append(bigquery.ScalarQueryParameter("evaluation_task", "STRING", evaluation_task))
        if product_type and product_type != "All":
            params.append(bigquery.ScalarQueryParameter("product_type", "STRING", product_type))

        logging.debug("get_leaderboard query:\n%s", query)
        logging.debug("get_leaderboard params: %s", params)

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        df = self.client.query(query, job_config=job_config).to_dataframe()
        return df

    def get_leaderboard_with_metrics(
        self,
        dataset_id: int,
        generation_task: str = None,
        evaluation_task: str = None,
        product_type: str = None,
        metrics: list = None
    ) -> pd.DataFrame:
        """
        Multi-metric aggregator:
        - De-duplicates by picking the latest run (row_number).
        - If no metrics are provided, fallback to "quality_score" (as integer).
        """
        table = f"`{self.client.project}.{self.dataset}.evaluation_results`"

        # If user didn't define metrics in expected_metrics, fallback to "quality_score"
        # (If your data uses something else, adapt accordingly).
        if not metrics or len(metrics) == 0:
            metrics = [{
                "name": "quality_score",
                "type": "integer"
            }]

        # Build the snippet for each metric
        selects = []
        for mdef in metrics:
            snippet = build_metric_sql_snippet(mdef)
            selects.append(snippet)
        metrics_sql = ",\n".join(selects)

        query = f"""
        WITH ranked AS (
          SELECT
            product_identifier_id,
            item_product_type,
            generation_task,
            evaluation_task,
            model_name,
            model_version,
            dataset_id,
            run_sequence_id,
            run_date,
            {metrics_sql},
            ROW_NUMBER() OVER (
              PARTITION BY product_identifier_id, generation_task, evaluation_task, model_name, model_version, dataset_id
              ORDER BY run_sequence_id DESC, run_date DESC
            ) AS rn
          FROM {table}
          WHERE dataset_id = @dataset_id
        """

        if generation_task and generation_task != "All":
            query += " AND generation_task = @generation_task"
        if evaluation_task and evaluation_task != "All":
            query += " AND evaluation_task = @evaluation_task"
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
        """

        # For each metric, compute an AVG(...)
        agg_expressions = []
        for mdef in metrics:
            mname = mdef["name"]
            agg_expressions.append(f"AVG({mname}) AS avg_{mname}")
        agg_sql = ",\n".join(agg_expressions)

        query += f"""
          {agg_sql},
          COUNT(*) AS num_evaluations
        FROM ranked
        WHERE rn = 1
        GROUP BY
          item_product_type,
          generation_task,
          evaluation_task,
          model_name,
          model_version
        ORDER BY
        """

        # We sort by the first metric
        first_metric = metrics[0]["name"]
        query += f"avg_{first_metric} DESC"

        params = [
            bigquery.ScalarQueryParameter("dataset_id", "INT64", dataset_id)
        ]
        if generation_task and generation_task != "All":
            params.append(bigquery.ScalarQueryParameter("generation_task", "STRING", generation_task))
        if evaluation_task and evaluation_task != "All":
            params.append(bigquery.ScalarQueryParameter("evaluation_task", "STRING", evaluation_task))
        if product_type and product_type != "All":
            params.append(bigquery.ScalarQueryParameter("product_type", "STRING", product_type))

        logging.debug("get_leaderboard_with_metrics query:\n%s", query)
        logging.debug("get_leaderboard_with_metrics params: %s", params)

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        df = self.client.query(query, job_config=job_config).to_dataframe()
        return df
