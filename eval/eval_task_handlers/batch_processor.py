import json
import sqlite3
from datetime import datetime
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from eval.config.constants import TASK_MAPPING


class BatchProcessor:
    def __init__(self, batch_size, db_path=None):
        """
        Initialize the BatchProcessor.

        Args:
            batch_size (int): Number of records to process in each batch.
            db_path (str): Path to the SQLite database file.
        """
        self.batch_size = batch_size
        self.db_path = db_path or "results.db"
        self.executor = ThreadPoolExecutor(max_workers=batch_size)

        # Initialize the database and create tables if they do not exist
        self._initialize_database()

    def _initialize_database(self):
        """
        Create necessary tables in the SQLite database if they do not exist.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create detail_results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detail_results (
                    item_id TEXT,
                    item_product_type TEXT,
                    task TEXT,
                    model_name TEXT,
                    model_version TEXT,
                    quality_score TEXT,
                    reasoning TEXT,
                    suggestions TEXT,
                    is_winner BOOLEAN,
                    enriched_content TEXT,
                    prompt_version TEXT,
                    eval_prompt_version TEXT,
                    PRIMARY KEY (item_id, task, model_name, model_version)
                )
            """)

            # Create winner_results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS winner_results (
                    item_id TEXT,
                    item_product_type TEXT,
                    task TEXT,
                    model_name TEXT,
                    model_version TEXT,
                    quality_score TEXT,
                    reasoning TEXT,
                    suggestions TEXT,
                    is_winner BOOLEAN,
                    enriched_content TEXT,
                    prompt_version TEXT,
                    eval_prompt_version TEXT,
                    PRIMARY KEY (item_id, task, model_name, model_version)
                )
            """)

            conn.commit()

    async def process_batches(self, df, api_handler, evaluator, prepare_item):
        """
        Process the data in batches concurrently.

        Args:
            df (pd.DataFrame): Input DataFrame.
            api_handler (APIHandler): API handler instance.
            evaluator (Evaluator): Evaluator instance.
            prepare_item (callable): Function to prepare item data for API.
        """
        tasks = [asyncio.create_task(self._process_single_batch(
            df.iloc[start:start + self.batch_size], api_handler, evaluator, prepare_item))
            for start in range(0, len(df), self.batch_size)]
        await asyncio.gather(*tasks)

    async def _process_single_batch(self, batch, api_handler, evaluator, prepare_item):
        """
        Process data in batches and save results to the database after each batch.

        Args:
            batch (pd.DataFrame): Input batch DataFrame.
            api_handler (APIHandler): API handler instance.
            evaluator (Evaluator): Evaluator instance.
            prepare_item (callable): Function to prepare item data for API.
        """
        logging.info(f"Processing batch of size {len(batch)}")

        detail_results = []
        winner_results = []

        loop = asyncio.get_event_loop()
        tasks = []

        for _, row in batch.iterrows():
            item_data = prepare_item(row)

            # Run the blocking call in a thread pool
            task = loop.run_in_executor(self.executor,
                partial(self._process_item, item_data, api_handler, evaluator))
            tasks.append(task)

        # Await all item processing tasks
        results = await asyncio.gather(*tasks)

        for detail, winner in results:
            detail_results.extend(detail)
            winner_results.extend(winner)

        # Persist results after processing each batch
        if detail_results:
            self._save_to_db(detail_results, "detail_results")
        if winner_results:
            self._save_to_db(winner_results, "winner_results")

    def _process_item(self, item_data, api_handler, evaluator):
        """
        Process a single item.

        Args:
            item_data (dict): The data of the item to be processed.
            api_handler (APIHandler): API handler instance.
            evaluator (Evaluator): Evaluator instance.

        Returns:
            tuple: A tuple containing detail results and winner results.
        """
        item_id = item_data["item_id"]
        enrichment_results = api_handler.call_api(item_data)

        if enrichment_results:
            detail, winner = asyncio.run(self._evaluate_item(item_data, enrichment_results, evaluator))
            return detail, winner
        else:
            logging.warning(f"No enrichment results for item: {item_id}")
            return [], []

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
        evaluation_tasks = []
        for task, task_name in TASK_MAPPING.items():
            model_responses = enrichment_results.get(task_name, {})
            if not model_responses:
                logging.info(f"No responses for task '{task_name}' in item '{item_data['item_id']}'. Skipping.")
                continue

            for model_name, model_data in model_responses.items():
                enriched_content = model_data.get("response", {}).get(f"enhanced_{task}")
                if not enriched_content:
                    logging.warning(f"No enriched content for task '{task_name}' by provider '{model_name}'.")

                    # Directly construct the result with '-NA-' values
                    ordered_result = {
                        "item_id"            : item_data["item_id"],
                        "item_product_type"  : product_type,
                        "task"               : task,
                        "model_name"         : model_name,
                        "model_version"      : "1",  # Default version
                        "quality_score"      : 0,
                        "reasoning"          : "-NA-",
                        "suggestions"        : "-NA-",
                        "is_winner"          : False,  # Default to False
                        "enriched_content"   : "-NA-",
                        "prompt_version"     : "1",
                        "eval_prompt_version": "1",
                    }
                    detail_results.append(ordered_result)

                    # Group result for winner selection
                    task_detail_results[task].append(ordered_result)
                else:
                    # Create async tasks for evaluation
                    evaluation_task = evaluator.evaluate_task(item_data, product_type, task, model_name, enriched_content)
                    evaluation_tasks.append(evaluation_task)
                    task_context.append((task, model_name, enriched_content))  # Track the task and model name

        # Await and process results
        results = await asyncio.gather(*evaluation_tasks, return_exceptions=True)

        for idx, result in enumerate(results):
            if isinstance(result, dict):
                task, model_name, enriched_content = task_context[idx]

                # Ensure necessary fields are added
                ordered_result = {
                    "item_id"            : item_data["item_id"],
                    "item_product_type"  : product_type,
                    "task"               : task,
                    "model_name"         : model_name,
                    "model_version"      : "1",  # Default version
                    "quality_score"      : result.get("quality_score", 0),
                    "reasoning"          : result.get("reasoning", "-NA-"),
                    "suggestions"        : result.get("suggestions", "-NA-"),
                    "is_winner"          : False,  # Default to False
                    "enriched_content"   : enriched_content,
                    "prompt_version"     : "1",
                    "eval_prompt_version": "1",
                }
                detail_results.append(ordered_result)

                # Group results by task for winner selection
                task_detail_results[task].append(ordered_result)

        # # Commented out as we do not need it right now.
        # # Determine winners for tasks with multiple models
        # for task, evaluations in task_detail_results.items():
        #     if not evaluations:  # Handle empty evaluations gracefully
        #         logging.warning(f"No valid results for task '{task}' in item '{item_data['item_id']}'. Skipping winner selection.")
        #         continue
        #
        #     if len(evaluations) > 1:  # Multiple responses for the task
        #         best_result = max(
        #             evaluations,
        #             key=lambda x: (x["quality_score"] or 0, -len(x["reasoning"]))
        #         )
        #     else:  # Single response for the task
        #         best_result = evaluations[0]
        #
        #     best_result["is_winner"] = True  # Mark as winner
        #     winner_results.append(best_result)

        return detail_results, winner_results

    def _save_to_db(self, results, table_name):
        """
        Save results to a SQLite database with an upsert operation.

        Args:
            results (list[dict]): Results to save.
            table_name (str): Name of the table to insert the data.
        """
        if not results:
            logging.info(f"No results to save for {table_name}.")
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Prepare the data for insertion with serialization
            data_to_insert = [
                (
                    result["item_id"],
                    result["item_product_type"],
                    result["task"],
                    result["model_name"],
                    result["model_version"],
                    result["quality_score"],
                    json.dumps(result.get("reasoning", {})),  # Serialize reasoning as JSON string
                    json.dumps(result.get("suggestions", "None")),  # Serialize suggestions as JSON string
                    result["is_winner"],
                    result["enriched_content"],
                    result["prompt_version"],
                    result["eval_prompt_version"]
                )
                for result in results
            ]

            # Insert or replace into the appropriate table
            cursor.executemany(f"""
                INSERT INTO {table_name} (
                    item_id, item_product_type, task, model_name, model_version,
                    quality_score, reasoning, suggestions, is_winner,
                    enriched_content, prompt_version, eval_prompt_version
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(item_id, task, model_name, model_version)
                DO UPDATE SET
                    quality_score=excluded.quality_score,
                    reasoning=excluded.reasoning,
                    suggestions=excluded.suggestions,
                    is_winner=excluded.is_winner,
                    enriched_content=excluded.enriched_content,
                    prompt_version=excluded.prompt_version,
                    eval_prompt_version=excluded.eval_prompt_version
            """, data_to_insert)

            conn.commit()
            logging.info(f"{len(results)} rows upserted into {table_name}.")