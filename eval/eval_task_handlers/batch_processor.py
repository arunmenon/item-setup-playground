import json
import logging
import asyncio
from collections import defaultdict
import numpy as np


class BatchProcessor:
    def __init__(self, batch_size, db_handler):
        self.batch_size = batch_size
        self.db_handler = db_handler
        self.db_handler.create_tables()

    def process_batches(self, df, api_handler, evaluators, prepare_item):
        for start in range(0, len(df), self.batch_size):
            batch = df.iloc[start:start + self.batch_size]
            logging.info(f"Processing batch {start // self.batch_size + 1}")

            evaluation_results = []

            for _, row in batch.iterrows():
                item_id = row['catlg_item_id']

                # Process a single item
                item_data = prepare_item(row)
                enrichment_results = api_handler.call_api(item_data)
                if enrichment_results:
                    evaluations = asyncio.run(
                        self._evaluate_item(item_data, enrichment_results, evaluators)
                    )
                    evaluation_results.extend(evaluations)
                else:
                    logging.warning(f"No enrichment results for item: {item_id}")

            if evaluation_results:
                self._save_to_db(evaluation_results)
                # Optionally, aggregate evaluations
                aggregated_results = self._aggregate_evaluations(evaluation_results)
                if aggregated_results:
                    self.db_handler.save_aggregated_evaluations(aggregated_results)

    async def _evaluate_item(self, item_data, enrichment_results, evaluators):
        evaluation_results = []
        product_type = item_data["item_product_type"]

        tasks = []
        task_context = []

        for evaluator in evaluators:
            evaluator_id = evaluator.id
            for generation_task_name, model_responses in enrichment_results.items():
                if not model_responses:
                    continue

                for model_name, model_data in model_responses.items():
                    enriched_content = model_data.get("response", {}).get("content")
                    if not enriched_content:
                        continue

                    # Create async tasks for evaluation
                    tasks.append(
                        evaluator.evaluate_task(
                            item_data, product_type, generation_task_name, model_name, enriched_content, evaluator_id=evaluator_id
                        )
                    )
                    task_context.append((
                    generation_task_name, model_name, model_data.get('model_version', '1.0'), evaluator_id))

        # Await and process results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for idx, result_list in enumerate(results):
            if isinstance(result_list, list):
                for eval_result in result_list:
                    evaluation_results.append(eval_result)
            else:
                logging.error(f"Error in evaluating model response: {results[idx]}")

        return evaluation_results

    def _save_to_db(self, results):
        if not results:
            logging.info("No results to save.")
            return

        for result in results:
            self.db_handler.save_evaluation(result)

    def _aggregate_evaluations(self, evaluation_results):
        # Group evaluations by relevant keys
        grouped_evaluations = defaultdict(list)
        for eval_result in evaluation_results:
            key = (
                eval_result['item_id'],
                eval_result['item_product_type'],
                eval_result['generation_task'],
                eval_result['evaluation_task'],
                eval_result['model_name'],
                eval_result['model_version'],
                eval_result['evaluator_type'],
                eval_result['evaluator_id']
            )
            grouped_evaluations[key].append(eval_result['evaluation_data'])

        aggregated_results = []
        for key, eval_data_list in grouped_evaluations.items():
            metrics = defaultdict(list)
            for eval_data in eval_data_list:
                for metric_name, metric_value in eval_data.items():
                    if isinstance(metric_value, (int, float)):
                        metrics[metric_name].append(metric_value)

            for metric_name, values in metrics.items():
                if values:
                    mean = np.mean(values)
                    variance = np.var(values, ddof=1)
                    confidence = self._determine_confidence_level(variance)
                    aggregated_result = {
                        'item_id'          : key[0],
                        'item_product_type': key[1],
                        'generation_task'  : key[2],
                        'evaluation_task'  : key[3],
                        'model_name'       : key[4],
                        'model_version'    : key[5],
                        'evaluator_type'   : key[6],
                        'evaluator_id'     : key[7],
                        'metric_name'      : metric_name,
                        'metric_mean'      : mean,
                        'metric_variance'  : variance,
                        'metric_confidence': confidence
                    }
                    aggregated_results.append(aggregated_result)

        return aggregated_results

    def _determine_confidence_level(self, variance):
        if variance <= 0.5:
            return 'High'
        elif variance <= 1.5:
            return 'Medium'
        else:
            return 'Low'