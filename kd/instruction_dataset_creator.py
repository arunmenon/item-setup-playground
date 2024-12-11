import json
import logging
from typing import Optional, Dict, Any
from google.cloud import bigquery, storage
from sqlalchemy.orm import Session

from entrypoint import PromptManager
from .scenario_params import ScenarioParams
from .scenario_manager import ScenarioManager
from .item_input_fetcher import ItemInputFetcher
from .instruction_formatter import InstructionFormatter

class InstructionDatasetCreator:
    """
    Orchestrates the entire process:
    - Selecting high-quality responses (ScenarioManager)
    - Fetching item inputs (ItemInputFetcher)
    - Generating prompts (PromptManager)
    - Formatting results (InstructionFormatter)
    - Saving dataset (JSONL) and uploading to GCS
    """
    def __init__(
        self,
        db_session: Session,
        scenario_params: ScenarioParams,
        instruction_format: Dict[str, str],
        gcs_bucket: str,
        gcs_output_path: str,
        family_name: Optional[str] = None
    ):
        self.db_session = db_session
        self.scenario_params = scenario_params
        self.instruction_format = instruction_format
        self.gcs_bucket = gcs_bucket
        self.gcs_output_path = gcs_output_path
        self.family_name = family_name

        self.bq_client = bigquery.Client()
        self.prompt_manager = PromptManager(self.db_session)
        self.scenario_manager = ScenarioManager(self.bq_client, self.db_session, self.scenario_params)
        self.item_input_fetcher = ItemInputFetcher(
            self.bq_client,
            self.scenario_params.project_id,
            self.scenario_params.dataset_id
        )
        self.instruction_formatter = InstructionFormatter(self.instruction_format)

    def run(self):
        results = self.scenario_manager.select_high_quality_responses()
        if not results:
            logging.info("No responses found for the given scenario.")
            return

        response_map = {}
        dataset_item_pairs = set()
        for r in results:
            key = (r["dataset_id"], r["item_id"], r["task_name"])
            response_map[key] = r["model_response"]
            dataset_item_pairs.add((r["dataset_id"], r["item_id"]))

        dataset_item_pairs = list(dataset_item_pairs)

        input_map = self.item_input_fetcher.fetch_item_inputs(dataset_item_pairs)
        if not input_map:
            logging.warning("No input data found for the selected items.")
            return

        local_file = "/tmp/instruction_tuning_data.jsonl"
        with open(local_file, 'w', encoding='utf-8') as outfile:
            for (did, iid), item_data in input_map.items():
                item = {
                    'product_type': item_data['product_type'],
                    'item_title': item_data['item_title'],
                    'short_description': item_data['short_description'],
                    'long_description': item_data['long_description']
                }

                # generate prompts for generation tasks
                prompts = self.prompt_manager.generate_prompts(item, family_name=self.family_name, task_type="generation")

                for (d_id, i_id, tname), model_resp in response_map.items():
                    if d_id == did and i_id == iid:
                        prompt_text = None
                        for p in prompts:
                            if p['task'] == tname:
                                prompt_text = p['prompt']
                                break

                        if not prompt_text:
                            logging.warning(f"No prompt found for task '{tname}' on (dataset_id={did}, item_id={iid}).")
                            continue

                        record = self.instruction_formatter.format_record(prompt_text, model_resp)
                        outfile.write(json.dumps(record, ensure_ascii=False) + "\n")

        self._upload_to_gcs(local_file)
        logging.info("Instruction tuning dataset created and uploaded successfully.")

    def _upload_to_gcs(self, local_file_path: str):
        storage_client = storage.Client()
        bucket = storage_client.bucket(self.gcs_bucket)
        blob = bucket.blob(self.gcs_output_path)
        blob.upload_from_filename(local_file_path)
        logging.info(f"File {local_file_path} uploaded to gs://{self.gcs_bucket}/{self.gcs_output_path}")
