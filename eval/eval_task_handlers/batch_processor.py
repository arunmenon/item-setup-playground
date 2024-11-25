import json
import sqlite3
from datetime import datetime
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from eval.config.constants import TASK_MAPPING
from collections import defaultdict
import numpy as np
from tqdm.asyncio import tqdm


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
        self.metrics = ['quality_score', 'relevance', 'clarity', 'compliance', 'accuracy']
        self.metric_ranges = {
            'quality_score': 100,
            'relevance'    : 5,
            'clarity'      : 5,
            'compliance'   : 5,
            'accuracy'     : 5
        }

    def _initialize_database(self):
        """
        Create necessary tables in the SQLite database if they do not exist.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Update table schema to include missing columns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evaluation_results (
                    item_id TEXT,
                    item_product_type TEXT,
                    task TEXT,
                    model_name TEXT,
                    model_version TEXT,
                    evaluator_type TEXT,         -- 'LLM' or 'Human'
                    evaluator_id TEXT,
                    quality_score INTEGER,       -- For LLM evaluations (0-100)
                    relevance INTEGER,           
                    clarity INTEGER,             
                    compliance INTEGER,          
                    accuracy INTEGER,            
                    reasoning TEXT,
                    suggestions TEXT,
                    is_winner BOOLEAN,
                    comments TEXT,               -- Additional comments from human evaluators
                    enriched_content TEXT,
                    prompt_version TEXT,
                    eval_prompt_version TEXT,
                    PRIMARY KEY (item_id, task, model_name, model_version, evaluator_type, evaluator_id)
                )
            """)

            # Create aggregated_results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aggregated_evaluations (
                    item_id TEXT,
                    item_product_type TEXT,
                    task TEXT,
                    model_name TEXT,
                    model_version TEXT,
                    quality_score_mean REAL,
                    quality_score_variance REAL,
                    quality_score_confidence TEXT,
                    relevance_mean REAL,
                    relevance_variance REAL,
                    relevance_confidence TEXT,
                    clarity_mean REAL,
                    clarity_variance REAL,
                    clarity_confidence TEXT,
                    compliance_mean REAL,
                    compliance_variance REAL,
                    compliance_confidence TEXT,
                    accuracy_mean REAL,
                    accuracy_variance REAL,
                    accuracy_confidence TEXT,
                    PRIMARY KEY (item_id, task, model_name, model_version)
                )
            """)

            conn.commit()

    async def process_batches(self, df, api_handler, evaluators, prepare_item):
        """
        Process the data in batches concurrently.

        Args:
            df (pd.DataFrame): Input DataFrame.
            api_handler (APIHandler): API handler instance.
            evaluators (list[Evaluator]): List of evaluator instances.
            prepare_item (callable): Function to prepare item data for API.
        """
        semaphore = asyncio.Semaphore(1)
        tasks = [
            asyncio.create_task(self._process_single_batch(
                df.iloc[start:start + self.batch_size], api_handler, evaluators, prepare_item, semaphore))
            for start in range(0, len(df), self.batch_size)
        ]

        for f in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Processing Batches"):
            await f

    async def _process_single_batch(self, batch, api_handler, evaluators, prepare_item, semaphore):
        """
        Process data in batches and save results to the database after each batch.

        Args:
            batch (pd.DataFrame): Input batch DataFrame.
            api_handler (APIHandler): API handler instance.
            evaluators (list[Evaluator]): List of evaluator instances.
            prepare_item (callable): Function to prepare item data for API.
        """
        async with semaphore:
            logging.debug(f"Processing batch of size {len(batch)}")

            loop = asyncio.get_event_loop()
            tasks = []

            for _, row in batch.iterrows():
                item_data = prepare_item(row)
                task = loop.run_in_executor(self.executor, partial(self._process_item, item_data, api_handler, evaluators))
                tasks.append(task)

            # Await all item processing tasks
            results = await asyncio.gather(*tasks)

            evaluation_results = [item for sublist in results for item in sublist if item]

            if evaluation_results:
                self._save_to_db(evaluation_results)
                # Aggregate evaluations
                aggregated_results = self._aggregate_evaluations(evaluation_results)
                if aggregated_results:
                    self._save_aggregated_results(aggregated_results)

    def _process_item(self, item_data, api_handler, evaluators):
        """
        Process a single item.

        Args:
            item_data (dict): The data of the item to be processed.
            api_handler (APIHandler): API handler instance.
            evaluators (list[Evaluator]): List of evaluator instances.

        Returns:
            list: A list containing evaluation results.
        """
        item_id = item_data["item_id"]
        enrichment_results = api_handler.call_api(item_data)

        if enrichment_results:
            evaluations = asyncio.run(self._evaluate_item(item_data, enrichment_results, evaluators))
            return evaluations
        else:
            logging.warning(f"No enrichment results for item: {item_id}")
            return []

    async def _evaluate_item(self, item_data, enrichment_results, evaluators):
        evaluation_results = []
        product_type = item_data["item_product_type"]

        tasks = []
        task_context = []

        for evaluator in evaluators:
            evaluator_id = evaluator.id  # Get evaluator_id
            for task, task_name in TASK_MAPPING.items():
                model_responses = enrichment_results.get(task_name, {})
                if not model_responses:
                    continue

                for model_name, model_data in model_responses.items():
                    enriched_content = model_data.get("response", {}).get(f"enhanced_{task}")
                    if not enriched_content:
                        # Directly construct the result with '-NA-' values
                        ordered_result = {
                            "item_id"            : item_data["item_id"],
                            "item_product_type"  : product_type,
                            "task"               : task_name,
                            "model_name"         : model_name,
                            "model_version"      : model_data.get('model_version', '1.0'),
                            "evaluator_type"     : 'LLM',
                            "evaluator_id"       : evaluator_id,
                            "quality_score"      : 0,
                            "relevance"          : 0,
                            "clarity"            : 0,
                            "compliance"         : 0,
                            "accuracy"           : 0,
                            "reasoning"          : "-NA-",
                            "suggestions"        : "-NA-",
                            "is_winner"          : False,
                            "comments"           : None,
                            "enriched_content"   : "-NA-",
                            "prompt_version"     : "1",
                            "eval_prompt_version": "1"
                        }
                        evaluation_results.append(ordered_result)

                    else:
                        # Create async tasks for evaluation
                        evaluation_task = evaluator.evaluate_task(item_data, product_type, task, model_name, enriched_content, evaluator_id)
                        tasks.append(evaluation_task)
                        task_context.append((task_name, model_name, model_data.get('model_version', '1.0'), evaluator_id,
                                         enriched_content))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for idx, result in enumerate(results):
            if isinstance(result, dict):
                task_name, model_name, model_version, evaluator_id, enriched_content = task_context[idx]

                evaluation_result = {
                    "item_id"            : item_data["item_id"],
                    "item_product_type"  : product_type,
                    "task"               : task_name,
                    "model_name"         : model_name,
                    "model_version"      : model_version,
                    "evaluator_type"     : 'LLM',
                    "evaluator_id"       : evaluator_id,
                    "quality_score"      : result.get("quality_score"),
                    "relevance"          : result.get("relevance"),
                    "clarity"            : result.get("clarity"),
                    "compliance"         : result.get("compliance"),
                    "accuracy"           : result.get("accuracy"),
                    "reasoning"          : json.dumps(result.get("reasoning", {})),
                    "suggestions"        : json.dumps(result.get("suggestions", "None")),
                    "is_winner"          : False,
                    "comments"           : None,
                    "enriched_content"   : enriched_content,
                    "prompt_version"     : "1",
                    "eval_prompt_version": "1"
                }
                evaluation_results.append(evaluation_result)
            else:
                logging.error(f"Error in evaluating model response: {result}")

        return evaluation_results

    def _save_to_db(self, results):
        """
        Save results to the evaluation_results table in the SQLite database with an upsert operation.

        Args:
            results (list[dict]): Results to save.
        """
        if not results:
            logging.info(f"No results to save.")
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Prepare the data for insertion
            data_to_insert = [
                (
                    result["item_id"],
                    result["item_product_type"],
                    result["task"],
                    result["model_name"],
                    result["model_version"],
                    result["evaluator_type"],
                    result["evaluator_id"],
                    result.get("quality_score"),
                    result.get("relevance"),
                    result.get("clarity"),
                    result.get("compliance"),
                    result.get("accuracy"),
                    result.get("reasoning"),
                    result.get("suggestions"),
                    result.get("is_winner", False),
                    result.get("comments"),
                    result.get("enriched_content"),
                    result.get("prompt_version"),
                    result.get("eval_prompt_version")
                )
                for result in results
            ]

            # Insert or replace into the evaluation_results table
            cursor.executemany("""
                INSERT INTO evaluation_results (
                    item_id, item_product_type, task, model_name, model_version,
                    evaluator_type, evaluator_id, quality_score, relevance, clarity, compliance, accuracy,
                    reasoning, suggestions, is_winner, comments,
                    enriched_content, prompt_version, eval_prompt_version
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(item_id, task, model_name, model_version, evaluator_type, evaluator_id)
                DO UPDATE SET
                    quality_score=excluded.quality_score,
                    relevance=excluded.relevance,
                    clarity=excluded.clarity,
                    compliance=excluded.compliance,
                    accuracy=excluded.accuracy,
                    reasoning=excluded.reasoning,
                    suggestions=excluded.suggestions,
                    is_winner=excluded.is_winner,
                    comments=excluded.comments,
                    enriched_content=excluded.enriched_content,
                    prompt_version=excluded.prompt_version,
                    eval_prompt_version=excluded.eval_prompt_version
            """, data_to_insert)

            conn.commit()
            logging.info(f"{len(results)} rows upserted into evaluation_results.")

    def _aggregate_evaluations(self, evaluation_results):
        # Group evaluations by item_id, product_type, and task
        grouped_evaluations = defaultdict(list)
        for eval_result in evaluation_results:
            key = (eval_result['item_id'], eval_result['item_product_type'], eval_result['task'])
            grouped_evaluations[key].append(eval_result)

        aggregated_results = []

        for key, evals in grouped_evaluations.items():
            item_id, product_type, task = key
            all_scores = defaultdict(list)

            # Collect scores for variance calculation
            for eval in evals:
                for metric in self.metrics:
                    if eval.get(metric) is not None:
                        all_scores[metric].append(eval.get(metric))

            # Calculate overall variance for each metric
            overall_variance = {}
            for metric, scores in all_scores.items():
                if scores:
                    normalized_scores = [score / self.metric_ranges[metric] for score in scores]
                    overall_variance[metric] = np.var(normalized_scores, ddof=1) if len(normalized_scores) > 1 else 0.0
                else:
                    overall_variance[metric] = None

            # Aggregate metrics for each model within the group
            model_aggregated_metrics = []
            unique_models = {(eval['model_name'], eval['model_version']) for eval in evals}

            for model_name, model_version in unique_models:
                model_evals = [e for e in evals if e['model_name']==model_name and e['model_version']==model_version]
                model_metrics = self._calculate_aggregated_metrics(model_evals, overall_variance)

                model_aggregated_metrics.append({
                    'model_name'   : model_name,
                    'model_version': model_version,
                    **model_metrics
                })

            # Prepare aggregated result
            for model_metrics in model_aggregated_metrics:
                aggregated_result = {
                    'item_id'           : item_id,
                    'item_product_type' : product_type,
                    'task'              : task,
                    **model_metrics
                }
                aggregated_results.append(aggregated_result)

        return aggregated_results

    def _calculate_aggregated_metrics(self, evaluations, overall_variance):
        aggregated = {}
        for metric in self.metrics:
            scores = [e.get(metric) for e in evaluations if e.get(metric) is not None]
            if scores:
                # Normalize scores to 0-1 range
                normalized_scores = [round(score / self.metric_ranges[metric], 3) for score in scores]

                mean_score = np.mean(normalized_scores)
                # variance = np.var(normalized_scores, ddof=1) if len(normalized_scores) > 1 else 0.0

                confidence = self._determine_confidence_level(overall_variance[metric])
                aggregated[f'{metric}'] = evaluations[0][f"{metric}"]
                aggregated[f'{metric}_mean'] = round(mean_score, 2)
                aggregated[f'{metric}_variance'] = round(overall_variance[metric], 2)
                aggregated[f'{metric}_confidence'] = confidence
            else:
                aggregated[f'{metric}_mean'] = None
                aggregated[f'{metric}_variance'] = None
                aggregated[f'{metric}_confidence'] = 'Unknown'
        return aggregated

    def _determine_confidence_level(self, variance):
        if variance is None:
            return 'Unknown'
        elif variance <= 0.05:
            return 'High'
        elif variance <= 0.1:
            return 'Medium'
        else:
            return 'Low'


    # def _calculate_aggregated_metrics(self, evaluations):
    #     metrics = ['quality_score', 'relevance', 'clarity', 'compliance', 'accuracy']
    #     aggregated = {}
    #     for metric in metrics:
    #         scores = [e.get(metric) for e in evaluations if e.get(metric) is not None]
    #         if scores:
    #             mean_score = np.mean(scores)
    #             variance = np.var(scores, ddof=1)  # Sample variance
    #             confidence = self._determine_confidence_level(variance)
    #             aggregated[f'{metric}_mean'] = mean_score
    #             aggregated[f'{metric}_variance'] = variance
    #             aggregated[f'{metric}_confidence'] = confidence
    #         else:
    #             aggregated[f'{metric}_mean'] = None
    #             aggregated[f'{metric}_variance'] = None
    #             aggregated[f'{metric}_confidence'] = 'Unknown'
    #     return aggregated
    #
    # def _determine_confidence_level(self, variance):
    #     if variance is None:
    #         return 'Unknown'
    #     elif variance <= 0.5:
    #         return 'High'
    #     elif variance <= 1.5:
    #         return 'Medium'
    #     else:
    #         return 'Low'

    def _save_aggregated_results(self, aggregated_results):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Prepare data for insertion
            data_to_insert = [
                (
                    result['item_id'],
                    result['item_product_type'],
                    result['task'],
                    result['model_name'],
                    result['model_version'],
                    result.get('quality_score_mean'),
                    result.get('quality_score_variance'),
                    result.get('quality_score_confidence'),
                    result.get('relevance_mean'),
                    result.get('relevance_variance'),
                    result.get('relevance_confidence'),
                    result.get('clarity_mean'),
                    result.get('clarity_variance'),
                    result.get('clarity_confidence'),
                    result.get('compliance_mean'),
                    result.get('compliance_variance'),
                    result.get('compliance_confidence'),
                    result.get('accuracy_mean'),
                    result.get('accuracy_variance'),
                    result.get('accuracy_confidence'),
                )
                for result in aggregated_results
            ]
            cursor.executemany("""
                INSERT OR REPLACE INTO aggregated_evaluations (
                    item_id, item_product_type, task, model_name, model_version,
                    quality_score_mean, quality_score_variance, quality_score_confidence,
                    relevance_mean, relevance_variance, relevance_confidence,
                    clarity_mean, clarity_variance, clarity_confidence,
                    compliance_mean, compliance_variance, compliance_confidence,
                    accuracy_mean, accuracy_variance, accuracy_confidence
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data_to_insert)
            conn.commit()