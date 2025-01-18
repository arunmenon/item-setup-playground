# File: bigquery_leaderboard_handler.py

import logging
from google.cloud import bigquery
import pandas as pd

def build_metric_sql_snippet(metric_def):
    """
    For multi-metrics aggregator. Builds a SELECT expression, e.g.:
      { "name":"decision","type":"yes_no" } -> yes/no => 1/0
      { "name":"clarity","type":"integer"} -> CAST(JSON_VALUE(...))
    """
    metric_name = metric_def["name"]
    metric_type = metric_def.get("type", "float")

    json_extract = f"JSON_VALUE(evaluation_data, '$.{metric_name}')"
    if metric_type in ("yes_no", "boolean"):
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
        # integer, float, default
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
        Single metric aggregator (score). De-duplicates with ROW_NUMBER. 
        We parse JSON_VALUE(evaluation_data, '$.score') as float, then do AVG(score).
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
        WHERE rn = 1
        GROUP BY
          item_product_type,
          generation_task,
          evaluation_task,
          model_name,
          model_version
        ORDER BY
          avg_score DESC
        """

        params = [bigquery.ScalarQueryParameter("dataset_id", "INT64", dataset_id)]
        if generation_task and generation_task != "All":
            params.append(bigquery.ScalarQueryParameter("generation_task", "STRING", generation_task))
        if evaluation_task and evaluation_task != "All":
            params.append(bigquery.ScalarQueryParameter("evaluation_task", "STRING", evaluation_task))
        if product_type and product_type != "All":
            params.append(bigquery.ScalarQueryParameter("product_type", "STRING", product_type))

        logging.debug("get_leaderboard query:\n%s", query)
        logging.debug("params: %s", params)

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
        Multi-metrics aggregator. De-duplicates. If no metrics, fallback to 'quality_score'.
        We compute AVG(...) for each metric => columns like avg_compliance, avg_clarity, etc.
        """
        table = f"`{self.client.project}.{self.dataset}.evaluation_results`"
        if not metrics or len(metrics) == 0:
            # fallback
            metrics = [{"name": "quality_score", "type": "integer"}]

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

        first_metric = metrics[0]["name"]
        query += f"avg_{first_metric} DESC"

        params = [bigquery.ScalarQueryParameter("dataset_id", "INT64", dataset_id)]
        if generation_task and generation_task != "All":
            params.append(bigquery.ScalarQueryParameter("generation_task", "STRING", generation_task))
        if evaluation_task and evaluation_task != "All":
            params.append(bigquery.ScalarQueryParameter("evaluation_task", "STRING", evaluation_task))
        if product_type and product_type != "All":
            params.append(bigquery.ScalarQueryParameter("product_type", "STRING", product_type))

        logging.debug("get_leaderboard_with_metrics query:\n%s", query)
        logging.debug("params: %s", params)

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        df = self.client.query(query, job_config=job_config).to_dataframe()
        return df

    def get_leaderboard_with_buckets(
        self,
        dataset_id: int,
        generation_task: str = None,
        evaluation_task: str = None,
        product_type: str = None
    ) -> pd.DataFrame:
        """
        Bucket aggregator: 
        - De-duplicates by picking latest row via ROW_NUMBER. 
        - Then we do a CASE expression to categorize score into:
            Bad (score <30), Average (score<60), Good (score<80), Excellent (>=80).
        - We group by (model_name, model_version, bucket), then do COUNT(*).
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
            dataset_id,
            run_sequence_id,
            run_date,
            CAST(JSON_VALUE(evaluation_data, '$.quality_score') AS FLOAT64) AS qscore,
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
          model_name,
          model_version,
          CASE
            WHEN qscore < 30 THEN "Bad"
            WHEN qscore < 60 THEN "Average"
            WHEN qscore < 80 THEN "Good"
            ELSE "Excellent"
          END AS bucket,
          COUNT(*) AS count_in_bucket
        FROM ranked
        WHERE rn = 1
        GROUP BY
          model_name, model_version, bucket
        ORDER BY
          model_name, bucket
        """

        params = [bigquery.ScalarQueryParameter("dataset_id", "INT64", dataset_id)]
        if generation_task and generation_task != "All":
            params.append(bigquery.ScalarQueryParameter("generation_task", "STRING", generation_task))
        if evaluation_task and evaluation_task != "All":
            params.append(bigquery.ScalarQueryParameter("evaluation_task", "STRING", evaluation_task))
        if product_type and product_type != "All":
            params.append(bigquery.ScalarQueryParameter("product_type", "STRING", product_type))

        logging.debug("get_leaderboard_with_buckets query:\n%s", query)
        logging.debug("params: %s", params)

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        df = self.client.query(query, job_config=job_config).to_dataframe()
        return df
