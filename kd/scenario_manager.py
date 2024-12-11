import json
from typing import Any, Dict, List
from google.cloud import bigquery
from sqlalchemy.orm import Session
from models.models import EvaluationTask
from .scenario_params import ScenarioParams
from .query_builder import QueryBuilder
import logging

class ScenarioManager:
    """
    Manages retrieval of high-quality model responses from evaluation_results,
    determining the metric if not provided by reading `expected_metrics` from evaluation_tasks.
    """
    def __init__(self, bq_client: bigquery.Client, db_session: Session, params: ScenarioParams):
        self.bq_client = bq_client
        self.db_session = db_session
        self.params = params
        self.metric_name = self._determine_metric()

    def _determine_metric(self) -> str:
        if self.params.eval_task_metric:
            return self.params.eval_task_metric

        # No eval_task_metric specified, derive from evaluation_tasks:
        if not self.params.evaluation_tasks or len(self.params.evaluation_tasks) == 0:
            raise ValueError("No evaluation tasks provided and no eval_task_metric specified.")

        if len(self.params.evaluation_tasks) > 1:
            raise ValueError("Multiple evaluation tasks provided but no eval_task_metric specified.")

        # Single evaluation task
        task_name = self.params.evaluation_tasks[0]
        evaluation_task = self.db_session.query(EvaluationTask).filter_by(task_name=task_name).first()
        if not evaluation_task or not evaluation_task.expected_metrics:
            raise ValueError(f"Could not find expected_metrics for evaluation task '{task_name}' in DB.")

        em = json.loads(evaluation_task.expected_metrics)
        metrics_list = em.get("metrics", [])
        if not metrics_list:
            raise ValueError(f"No metrics defined in expected_metrics for '{task_name}'.")

        numeric_metrics = [m for m in metrics_list if m.get("type", "") == "integer"]
        if not numeric_metrics:
            raise ValueError(f"No numeric (integer) metrics found for eval task '{task_name}'.")

        required_numeric = [m for m in numeric_metrics if m.get("required", False)]
        chosen_metric = required_numeric[0] if required_numeric else numeric_metrics[0]
        metric_name = chosen_metric.get("name")
        if not metric_name:
            raise ValueError(f"Chosen metric has no name for eval task '{task_name}'.")
        return metric_name

    def select_high_quality_responses(self) -> List[Dict[str, Any]]:
        query = QueryBuilder.build_evaluation_query(self.params, self.metric_name)
        rows = list(self.bq_client.query(query).result())
        if not rows:
            return []
        results = [dict(r) for r in rows]
        return self._apply_scenario_logic(results)

    def _apply_scenario_logic(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        from collections import defaultdict
        if self.params.scenario_type == "all_eval_models":
            grouped = defaultdict(list)
            for r in results:
                grouped[(r["dataset_id"], r["item_id"], r["task_name"])].append(r)

            selected = []
            for key, group in grouped.items():
                eval_tasks_to_check = self.params.evaluation_tasks if self.params.evaluation_tasks \
                    else list({g["evaluation_task_name"] for g in group})
                tasks_ok = True
                for et in eval_tasks_to_check:
                    if not any(gr["evaluation_task_name"] == et for gr in group):
                        tasks_ok = False
                        break
                if tasks_ok:
                    selected.append(group[0])
            return selected

        # For 'specific_eval_model' or 'multiple_tasks', we do not apply special logic
        return results
