# batch_processor.py

import logging
import asyncio
from collections import defaultdict
import numpy as np
from eval.config.constants import TASK_MAPPING

class BatchProcessor:
    def __init__(self, batch_size, store):
        self.batch_size = batch_size
        self.store = store

    async def process_batches(self, df, api_handler, evaluators, prepare_item, include_evaluation):
        for start in range(0, len(df), self.batch_size):
            batch = df.iloc[start:start+self.batch_size]
            logging.info(f"Processing batch {start // self.batch_size + 1}")

            evaluation_results = []
            for _, row in batch.iterrows():
                item_data = prepare_item(row)
                enrichment_results = api_handler.call_api(item_data)

                if include_evaluation and enrichment_results:
                    evaluations = await self._evaluate_item(item_data, enrichment_results, evaluators)
                    evaluation_results.extend(evaluations)

            if evaluation_results:
                self.store.save_evaluations(evaluation_results)
                aggregated_results = self._aggregate_evaluations(evaluation_results)
                if aggregated_results:
                    self.store.save_aggregated_evaluation_results(aggregated_results)

    async def _evaluate_item(self, item_data, enrichment_results, evaluators):
        evaluation_results = []
        product_type = item_data.get("item_product_type", "unknown")

        tasks = []
        for evaluator in evaluators:
            evaluator_id = evaluator.id
            for generation_task_name, model_responses in enrichment_results.items():
                if not model_responses:
                    continue
                for task, task_name in TASK_MAPPING.items():
                    model_responses_task = enrichment_results.get(task_name, {})
                    if not model_responses_task:
                        continue
                    for model_name, model_data in model_responses_task.items():
                        enriched_content = model_data.get("response", {}).get(f"enhanced_{task}")
                        if not enriched_content:
                            continue

                        tasks.append(
                            evaluator.evaluate_task(
                                item_data, product_type, generation_task_name, model_name, enriched_content, evaluator_id=evaluator_id
                            )
                        )

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result_list in results:
            if isinstance(result_list, list):
                evaluation_results.extend(result_list)
            else:
                logging.error(f"Error evaluating model response: {result_list}")
        return evaluation_results

    def _aggregate_evaluations(self, evaluation_results):
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
                    # Assuming dataset_id is part of item_data or passed along evaluation_results if needed
                    # If needed, ensure evaluation_results store dataset_id in eval_result
                    dataset_id = eval_data_list[0].get('dataset_id', None)
                    aggregated_results.append({
                        'item_id': key[0],
                        'item_product_type': key[1],
                        'generation_task': key[2],
                        'evaluation_task': key[3],
                        'model_name': key[4],
                        'model_version': key[5],
                        'evaluator_type': key[6],
                        'evaluator_id': key[7],
                        'metric_name': metric_name,
                        'metric_mean': mean,
                        'metric_variance': variance,
                        'metric_confidence': confidence,
                        'dataset_id': dataset_id
                    })
        return aggregated_results

    def _determine_confidence_level(self, variance):
        if variance <= 0.5:
            return 'High'
        elif variance <= 1.5:
            return 'Medium'
        else:
            return 'Low'
