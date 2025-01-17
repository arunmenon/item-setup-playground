# File: bigquery_leaderboard_handler.py

from google.cloud import bigquery
import pandas as pd

def build_metric_sql_snippet(metric_def):
    """
    Build a per-metric SELECT expression based on type.
    e.g. {"name":"decision","type":"yes_no"} -> CASE ... THEN 1 ELSE 0 END
         {"name":"clarity","type":"integer"} -> CAST(JSON_VALUE(...))
    """
    metric_name = metric_def["name"]
    metric_type = metric_def.get("type", "float")  # fallback

    json_extract = f"JSON_VALUE(evaluation_data, '$.{metric_name}')"

    # yes/no or boolean
    if metric_type in ("yes_no", "boolean"):
        return f"""
        CASE
          WHEN {json_extract} = "Yes" OR {json_extract} = "True"  THEN 1
          WHEN {json_extract} = "No"  OR {json_extract} = "False" THEN 0
          ELSE NULL
        END AS {metric_name}
        """

    elif metric_type == "categorical":
        # Suppose there's a list of categories, e.g. ["Low","Medium","High"]
        # We'll check if categories exist, else fallback
        cats = metric_def.get("categories", [])
        if not cats:
            # fallback to a float cast
            return f"CAST({json_extract} AS FLOAT64) AS {metric_name}"

        # Build a dynamic CASE
        case_lines = []
        for i, cat in enumerate(cats):
            # e.g. WHEN JSON_VALUE(...) = "Low" THEN 0
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
        Original method: uses 'score' only.
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

        params = [
            bigquery.ScalarQueryParameter("dataset_id", "INT64", dataset_id)
        ]
        if generation_task and generation_task != "All":
            params.append(bigquery.ScalarQueryParameter("generation_task", "STRING", generation_task))
        if evaluation_task and evaluation_task != "All":
            params.append(bigquery.ScalarQueryParameter("evaluation_task", "STRING", evaluation_task))
        if product_type and product_type != "All":
            params.append(bigquery.ScalarQueryParameter("product_type", "STRING", product_type))

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        df = self.client.query(query, job_config=job_config).to_dataframe()
        return df

    def get_leaderboard_with_metrics(
        self,
        dataset_id: int,
        generation_task: str,
        evaluation_task: str,
        product_type: str,
        metrics: list
    ) -> pd.DataFrame:
        """
        A new method: dynamically parse metrics from evaluation_data based on 'metrics'.
        e.g. if metrics = [
              {"name":"compliance","type":"yes_no"},
              {"name":"clarity","type":"integer"}
            ]
        We do a CASE for yes_no, a CAST for integer, etc.
        Then compute the average for each metric.
        """
        table = f"`{self.client.project}.{self.dataset}.evaluation_results`"

        # Build SQL snippets for each metric
        if not metrics:
            # fallback to a single "score" scenario
            metrics = [{"name":"score","type":"float"}]

        selects = []
        for mdef in metrics:
            snippet = build_metric_sql_snippet(mdef)
            selects.append(snippet)

        metrics_sql = ",\n".join(selects)

        query = f"""
        WITH parsed AS (
          SELECT
            product_identifier_id,
            item_product_type,
            generation_task,
            evaluation_task,
            model_name,
            model_version,
            dataset_id,
            {metrics_sql}
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

        # For each metric, compute AVG(...)
        agg_expressions = []
        for mdef in metrics:
            mname = mdef["name"]
            agg_expressions.append(f"AVG({mname}) AS avg_{mname}")
        agg_sql = ",\n".join(agg_expressions)

        query += f"""
          {agg_sql},
          COUNT(*) AS num_evaluations
        FROM parsed
        GROUP BY
          item_product_type,
          generation_task,
          evaluation_task,
          model_name,
          model_version
        ORDER BY
        """

        # Sort by the first metric, or do something more advanced
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

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        df = self.client.query(query, job_config=job_config).to_dataframe()
        return df
