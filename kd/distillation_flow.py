# File: distillation_flow.py

import json
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from google.cloud import bigquery, storage

# We'll assume you have a PromptManager from your code:
from entrypoint import PromptManager


@dataclass
class DistillationParams:
    """
    Configuration for building an instruction-tuning dataset from BigQuery, allowing
    multiple generation tasks, multiple evaluation tasks, and min/max score thresholds.
    """
    project_id: str                   # e.g., "wmt-rg-dev"
    bq_dataset: str                   # e.g., "item_setup_playground"

    generation_tasks: List[str]       # e.g., ["title_enhancement", "description_enrichment"]
    model_names: List[str]            # e.g., ["gpt-4o"]

    evaluation_tasks: Optional[List[str]] = None  # e.g. ["style_guide_check","grammar_check"]
    min_score: Optional[float] = None             # each required eval task must have score >= min_score (if set)
    max_score: Optional[float] = None             # each required eval task must have score <= max_score (if set)

    top_n: int = 1000
    local_output_path: str = "distilled_output.jsonl"

    # Optional GCS output
    gcs_bucket: Optional[str] = None
    gcs_path: Optional[str] = None


class DistillationFlow:
    """
    A pipeline that:
      1) Queries 'evaluation_results' for multiple generation tasks, model names, 
         and evaluation tasks,
      2) Groups rows by (dataset_id, product_id, generation_task, model_name), collecting a 'score' per eval task,
      3) Keeps only groups that pass 'all tasks' within min_score/max_score,
      4) Fetches item data (task_input),
      5) Reconstructs the prompt with PromptManager,
      6) Produces an instruction record -> JSONL (optionally uploaded to GCS).
    """

    def __init__(
        self,
        params: DistillationParams,
        prompt_manager: PromptManager
    ):
        self.params = params
        self.prompt_manager = prompt_manager

        self.bq_client = bigquery.Client(project=params.project_id)
        if params.gcs_bucket and params.gcs_path:
            self.storage_client = storage.Client(project=params.project_id)
        else:
            self.storage_client = None

    def run(self):
        logging.info("[DistillationFlow] Starting flow with multiple gen/eval tasks + min/max threshold...")
        # 1) fetch all relevant rows from BQ
        raw_rows = self._fetch_eval_rows()
        if not raw_rows:
            logging.info("No rows retrieved from BQ. Exiting.")
            return

        # 2) group by (dataset_id, product_id, generation_task, model_name)
        grouped_data = self._group_by_scenario(raw_rows)

        # 3) filter out groups that do not pass "all tasks" within [min_score, max_score]
        final_groups = self._filter_groups(grouped_data)
        if not final_groups:
            logging.info("No groups pass the scenario's min/max threshold. Exiting.")
            return

        # 4) fetch item data
        item_map = self._fetch_item_inputs(final_groups)
        if not item_map:
            logging.info("No item data found for final groups. Exiting.")
            return

        # 5) reconstruct prompt + format
        records = []
        for key, data in final_groups.items():
            ds_id, pid, gen_task, model_name = key
            item_data = item_map.get((ds_id, pid), {})
            if not item_data:
                continue

            prompt_str = self.prompt_manager.generate_prompt(item_data, gen_task)
            record = self._format_instruction_record(prompt_str, data["model_response"])
            records.append(record)

        if not records:
            logging.info("No final records formed. Exiting.")
            return

        # 6) write JSONL
        self._write_jsonl(records, self.params.local_output_path)

        # 7) optional GCS upload
        if self.storage_client:
            self._upload_to_gcs(self.params.local_output_path)
            logging.info(f"Uploaded to gs://{self.params.gcs_bucket}/{self.params.gcs_path}")
        else:
            logging.info(f"Output is at {self.params.local_output_path}")

        logging.info("[DistillationFlow] Done.")

    def _fetch_eval_rows(self) -> List[Dict[str, Any]]:
        """
        Query 'evaluation_results' for generation_tasks, model_names, and evaluation_tasks.
        We only do a partial top_n limit. We'll filter by min/max in Python logic to handle "all tasks" scenario.
        """
        table = f"`{self.params.project_id}.{self.params.bq_dataset}.evaluation_results`"

        # generation tasks
        gen_clause = " OR ".join([f"generation_task='{g}'" for g in self.params.generation_tasks])
        # model names
        model_clause = " OR ".join([f"model_name='{m}'" for m in self.params.model_names])
        # eval tasks
        eval_clause = ""
        if self.params.evaluation_tasks:
            ev_str = " OR ".join([f"evaluation_task='{et}'" for et in self.params.evaluation_tasks])
            eval_clause = f"AND ({ev_str})"

        query = f"""
        SELECT
          dataset_id,
          product_identifier_id AS product_id,
          generation_task,
          model_name,
          evaluation_task,
          CAST(JSON_VALUE(evaluation_data, '$.score') AS FLOAT64) AS score,
          JSON_VALUE(evaluation_data, '$.response') AS model_response
        FROM {table}
        WHERE ({gen_clause})
          AND ({model_clause})
          {eval_clause}
        LIMIT {self.params.top_n}
        """
        logging.debug(f"[DistillationFlow] evaluation query:\n{query}")

        job = self.bq_client.query(query)
        rows = list(job.result())
        return [dict(r) for r in rows]

    def _group_by_scenario(
        self,
        rows: List[Dict[str,Any]]
    ) -> Dict[Tuple[int,str,str,str], Dict[str,Any]]:
        """
        Group rows by (dataset_id, product_id, generation_task, model_name).
        For each group, collect eval_scores: { eval_task_name: max_score } if multiple rows exist,
        and store 'model_response' from any row in that group (assuming they're identical).
        """
        from collections import defaultdict

        grouped = defaultdict(lambda: {
            "eval_scores": {},
            "model_response": None
        })

        for r in rows:
            ds_id = r["dataset_id"]
            pid   = r["product_id"]
            gen_t = r["generation_task"]
            mname = r["model_name"]
            etask = r["evaluation_task"]
            score = r["score"] or 0.0
            resp  = r["model_response"] or ""

            key = (ds_id, pid, gen_t, mname)
            entry = grouped[key]

            # keep max score for each eval task
            current = entry["eval_scores"].get(etask, float("-inf"))
            if score > current:
                entry["eval_scores"][etask] = score

            # store model_response if not set
            if entry["model_response"] is None or not entry["model_response"]:
                entry["model_response"] = resp

        return dict(grouped)

    def _filter_groups(
        self,
        groups: Dict[Tuple[int,str,str,str], Dict[str,Any]]
    ) -> Dict[Tuple[int,str,str,str], Dict[str,Any]]:
        """
        Keep only those groups for which:
          - every required eval task is present in eval_scores
          - each score is >= min_score (if min_score is set)
          - each score is <= max_score (if max_score is set)
        """
        if not self.params.evaluation_tasks:
            # If no eval tasks were specified, we keep them all.
            return groups

        final = {}
        for key, data in groups.items():
            eval_scores = data["eval_scores"]
            pass_all = True
            for et in self.params.evaluation_tasks:
                # must exist
                if et not in eval_scores:
                    pass_all = False
                    break
                sc = eval_scores[et]
                # must be >= min_score if provided
                if self.params.min_score is not None and sc < self.params.min_score:
                    pass_all = False
                    break
                # must be <= max_score if provided
                if self.params.max_score is not None and sc > self.params.max_score:
                    pass_all = False
                    break
            if pass_all:
                final[key] = data
        return final

    def _fetch_item_inputs(self, final_groups: Dict[Tuple[int,str,str,str], Dict[str,Any]]) -> Dict[Tuple[int,str], Dict[str,str]]:
        """
        We only need dataset_id, product_id for the final groups to fetch from 'task_input'.
        Return a dict keyed by (dataset_id, product_id).
        """
        pairs = set()
        for (ds_id, pid, gtask, mname) in final_groups.keys():
            pairs.add((ds_id, pid))

        if not pairs:
            return {}

        or_clauses = []
        for (ds, pid) in pairs:
            or_clauses.append(f"(dataset_id={ds} AND product_identifier_id='{pid}')")

        where_clause = " OR ".join(or_clauses)
        table = f"`{self.params.project_id}.{self.params.bq_dataset}.task_input`"
        query = f"""
        SELECT
          dataset_id,
          product_identifier_id AS product_id,
          product_type,
          product_data.product_name AS title,
          product_data.product_short_description AS short_desc,
          product_data.product_long_description AS long_desc
        FROM {table}
        WHERE {where_clause}
        """
        logging.debug(f"[DistillationFlow] item_inputs query:\n{query}")

        job = self.bq_client.query(query)
        rows = list(job.result())

        item_map = {}
        for r in rows:
            key = (r["dataset_id"], r["product_id"])
            item_map[key] = {
                "product_type": r.get("product_type", ""),
                "title": r.get("title", ""),
                "short_desc": r.get("short_desc", ""),
                "long_desc": r.get("long_desc", "")
            }
        return item_map

    def _format_instruction_record(self, prompt: str, response: str) -> Dict[str,str]:
        """
        Minimal instruction format: {instruction, input, output}.
        """
        overarching = (
            "Below is an instruction describing a task. "
            "Read the prompt and provide the best possible response."
        )
        return {
            "instruction": overarching.strip(),
            "input": prompt.strip(),
            "output": response.strip()
        }

    def _write_jsonl(self, records: List[Dict[str,Any]], filepath: str):
        logging.info(f"Writing {len(records)} records to {filepath}")
        with open(filepath, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def _upload_to_gcs(self, local_path: str):
        if not self.storage_client or not self.params.gcs_bucket or not self.params.gcs_path:
            return
        bucket = self.storage_client.bucket(self.params.gcs_bucket)
        blob = bucket.blob(self.params.gcs_path)
        blob.upload_from_filename(local_path)


# Example usage (adapt or remove if you have your own main)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # from entrypoint import PromptManager
    pm = PromptManager(db_session=None)  # If your manager needs a real session, pass it in

    # Suppose we want each required eval task to have 80 <= score <= 90
    # and multiple generation tasks
    params = DistillationParams(
        project_id="wmt-rg-dev",
        bq_dataset="item_setup_playground",
        generation_tasks=["title_enhancement", "description_enrichment"],
        model_names=["gpt-4o"],
        evaluation_tasks=["style_guide_check", "grammar_check"],
        min_score=80.0,
        max_score=90.0,
        top_n=1000,
        local_output_path="distilled_min_max.jsonl",
        gcs_bucket=None,
        gcs_path=None
    )

    flow = DistillationFlow(params, pm)
    flow.run()
