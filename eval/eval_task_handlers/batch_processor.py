from datetime import datetime
import pandas as pd
import logging
import os
from eval.config.constants import TASK_MAPPING
import asyncio  # Required for managing async tasks


class BatchProcessor:
    def __init__(self, batch_size, detail_file=None, winner_file=None):
        """
        Initialize the BatchProcessor.

        Args:
            batch_size (int): Number of records to process in each batch.
            detail_file (str, optional): Path to the detailed results file. Defaults to timestamp-based name.
            winner_file (str, optional): Path to the winner results file. Defaults to timestamp-based name.
        """
        self.batch_size = batch_size

        # Generate default file names with timestamp if not provided
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.detail_file = detail_file or f"detail_results_{timestamp}.csv"
        self.winner_file = winner_file or f"winner_results_{timestamp}.csv"

        logging.info(f"BatchProcessor initialized with:")
        logging.info(f"  Detail file: {self.detail_file}")
        logging.info(f"  Winner file: {self.winner_file}")

    def process_batches(self, df, api_handler, evaluator, prepare_item):
        detail_results = []
        winner_results = []

        for start in range(0, len(df), self.batch_size):
            batch = df.iloc[start:start + self.batch_size]
            logging.info(f"Processing batch {start // self.batch_size + 1}")

            for _, row in batch.iterrows():
                item_id = row['catlg_item_id']

                # Process a single item
                item_data = prepare_item(row)
                enrichment_results = api_handler.call_api(item_data)
                if enrichment_results:
                    detail, winner = asyncio.run(
                        self._evaluate_item(item_data, enrichment_results, evaluator)
                    )
                    detail_results.extend(detail)
                    if winner:
                        winner_results.extend(winner)
                else:
                    logging.warning(f"No enrichment results for item: {item_id}")

            # Save results for detail and winner views
            if detail_results:
                self._save_results(detail_results, self.detail_file)
                detail_results.clear()  # Clear after saving
            if winner_results:
                self._save_results(winner_results, self.winner_file)
                winner_results.clear()  # Clear after saving

    async def _evaluate_item(self, item_data, enrichment_results, evaluator):
        """
        Evaluate an item asynchronously across multiple tasks and providers.

        Args:
            item_data (dict): Data for the item being evaluated.
            enrichment_results (dict): Enrichment results for the item.
            evaluator (Evaluator): Evaluator instance to use for evaluation.

        Returns:
            tuple: A tuple containing detail results and winner results.
        """
        detail_results = []
        winner_results = []
        product_type = item_data["item_product_type"]

        # Dictionary to group results by task for winner selection
        task_detail_results = {task: [] for task in TASK_MAPPING.keys()}
        task_context = []  # To track which task/model each async task corresponds to

        # Create async tasks for evaluation
        tasks = []
        for task, task_name in TASK_MAPPING.items():
            model_responses = enrichment_results.get(task_name, {})
            if not model_responses:
                logging.info(f"No responses for task '{task_name}' in item '{item_data['item_id']}'. Skipping.")
                continue

            for model_name, model_data in model_responses.items():
                enriched_content = model_data.get("response", {}).get(f"enhanced_{task}")
                if not enriched_content:
                    logging.warning(f"No enriched content for task '{task_name}' by provider '{model_name}'.")
                    continue

                # Create async tasks for evaluation
                tasks.append(
                    evaluator.evaluate_task(
                        item_data, product_type, task, model_name, enriched_content
                    )
                )
                task_context.append((task, model_name))  # Track the task and model name


        # Await and process results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for idx,result  in enumerate(results):
            if isinstance(result, dict):
                # Ensure necessary fields are added
                task, model_name = task_context[idx]

                ordered_result = {
                "item_id": item_data["item_id"],
                "item_product_type": product_type,
                "task": task,
                "model_name": model_name,
                "quality_score": result.get("quality_score"),
                "reasoning": result.get("reasoning"),
                "suggestions": result.get("suggestions"),
                "is_winner": False,  # Default to False
                }
                detail_results.append(ordered_result)

                # Group results by task for winner selection
                task_name = task
                if task_name not in task_detail_results:
                    task_detail_results[task_name] = []
                task_detail_results[task_name].append(ordered_result)

        # Determine winners for tasks with multiple models
        for task, evaluations in task_detail_results.items():
            if not evaluations:  # Handle empty evaluations gracefully
                logging.warning(f"No valid results for task '{task}' in item '{item_data['item_id']}'. Skipping winner selection.")
                continue

            if len(evaluations) > 1:  # Multiple responses for the task
                best_result = max(
                    evaluations,
                    key=lambda x: (x["quality_score"] or 0, -len(x["reasoning"]))
                )
            else:  # Single response for the task
                best_result = evaluations[0]

            best_result["is_winner"] = True  # Mark as winner
            winner_results.append(best_result)

        return detail_results, winner_results


    def _save_results(self, results, file_path):
        """
        Save results to a CSV file.

        Args:
            results (list[dict]): Results to save.
            file_path (str): Path to the output file.
        """
        field_order = [
        "item_id", "item_product_type", "task", "model_name",
        "quality_score", "reasoning", "suggestions", "is_winner"
        ]
        df = pd.DataFrame(results)
        df = df[field_order]
        write_mode = 'a' if os.path.exists(file_path) else 'w'
        header = not os.path.exists(file_path)  # Write header only if file doesn't exist
        df.to_csv(file_path, mode=write_mode, header=header, index=False)
        logging.info(f"Results saved to '{file_path}' with {len(df)} rows.")
