from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ScenarioParams:
    """
    Holds scenario configuration parameters for selecting high-quality responses.
    If eval_task_metric is None, we attempt to derive it from evaluation_tasks.
    """
    project_id: str
    dataset_id: str
    generation_model: str
    generation_tasks: List[str]
    evaluation_tasks: Optional[List[str]] = None
    eval_task_metric: Optional[str] = None
    scenario_type: str = "all_eval_models"  # could be "specific_eval_model" or "multiple_tasks"
    eval_model: Optional[str] = None
    min_score: Optional[float] = None
    top_n: int = 100
