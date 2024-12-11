from typing import List
from .scenario_params import ScenarioParams

class QueryBuilder:
    """
    Helper class to build BigQuery SQL queries based on the ScenarioParams.
    """
    @staticmethod
    def build_evaluation_query(cfg: ScenarioParams, metric_name: str) -> str:
        conditions = [f"generation_model = '{cfg.generation_model}'"]
        if cfg.generation_tasks:
            gen_task_condition = " OR ".join([f"task_name='{t}'" for t in cfg.generation_tasks])
            conditions.append(f"({gen_task_condition})")

        if cfg.evaluation_tasks:
            eval_task_condition = " OR ".join([f"evaluation_task_name='{et}'" for et in cfg.evaluation_tasks])
            conditions.append(f"({eval_task_condition})")

        if cfg.eval_model and cfg.scenario_type == "specific_eval_model":
            conditions.append(f"evaluation_model = '{cfg.eval_model}'")

        metric_path = f"$.{metric_name}"
        if cfg.min_score is not None:
            conditions.append(
                f"CAST(JSON_EXTRACT_SCALAR(eval_metrics, '{metric_path}') AS FLOAT64) >= {cfg.min_score}"
            )

        where_clause = " AND ".join(conditions)
        query = f"""
        SELECT
          dataset_id,
          item_id,
          task_name,
          JSON_EXTRACT_SCALAR(eval_metrics, '{metric_path}') AS metric_value,
          generation_model,
          evaluation_task_name,
          evaluation_model,
          model_response
        FROM `{cfg.project_id}.{cfg.dataset_id}.evaluation_results`
        WHERE {where_clause}
        ORDER BY CAST(JSON_EXTRACT_SCALAR(eval_metrics, '{metric_path}') AS FLOAT64) DESC
        LIMIT {cfg.top_n}
        """
        return query

    @staticmethod
    def build_task_input_query(project_id: str, dataset_id: str, dataset_item_pairs: List[tuple]) -> str:
        if not dataset_item_pairs:
            return ""
        pairs_condition = " OR ".join([f"(dataset_id={did} AND item_id={iid})" for (did, iid) in dataset_item_pairs])
        query = f"""
        SELECT
          item_id,
          dataset_id,
          title,
          short_desc,
          long_desc,
          product_type
        FROM `{project_id}.{dataset_id}.task_input`
        WHERE {pairs_condition}
        """
        return query
