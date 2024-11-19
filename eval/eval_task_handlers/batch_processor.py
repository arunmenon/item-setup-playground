import json
import sqlite3
from datetime import datetime
import logging
import asyncio  # Required for managing async tasks
from eval.config.constants import TASK_MAPPING
from collections import defaultdict
import numpy as np


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

        # Initialize the database and create tables if they don't exist
        self._initialize_database()

    def _initialize_database(self):
        """
        Create necessary tables in the SQLite database if they do not exist.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create detail_results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evaluation_results (
                    item_id TEXT,
                    item_product_type TEXT,
                    task TEXT,
                    model_name TEXT,
                    model_version TEXT,
                    evaluator_type TEXT,         -- 'LLM' or 'Human'
                    quality_score INTEGER,       -- For LLM evaluations (0-100)
                    relevance INTEGER,           
                    clarity INTEGER,             
                    compliance INTEGER,          
                    accuracy INTEGER,            
                    reasoning TEXT,
                    suggestions TEXT,
                    is_winner BOOLEAN,
                    comments TEXT,               -- Additional comments from human evaluators
                    PRIMARY KEY (item_id, task, model_name, model_version, evaluator_type)
                )
            """)

            

            conn.commit()

    def process_batches(self, df, api_handler, evaluators, prepare_item):
        """
        Process data in batches and save results to the database after each batch.

        Args:
            df (pd.DataFrame): Input DataFrame.
            api_handler (APIHandler): API handler instance.
            evaluator (Evaluator): Evaluator instance.
            prepare_item (callable): Function to prepare item data for API.
        """
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
                # Aggregate evaluations
                aggregated_results = self._aggregate_evaluations(evaluation_results)
                if aggregated_results:
                    self._save_aggregated_results(aggregated_results)    

    
    async def _evaluate_item(self, item_data, enrichment_results, evaluators):
        evaluation_results = []
        product_type = item_data["item_product_type"]

        tasks = []
        task_context = []  # To track which task/model/evaluator each async task corresponds to

        for evaluator in evaluators:
            evaluator_id = evaluator.id  # Get evaluator_id
            for task, task_name in TASK_MAPPING.items():
                model_responses = enrichment_results.get(task_name, {})
                if not model_responses:
                    continue

                for model_name, model_data in model_responses.items():
                    enriched_content = model_data.get("response", {}).get(f"enhanced_{task}")
                    if not enriched_content:
                        continue

                    # Create async tasks for evaluation
                    tasks.append(
                        evaluator.evaluate_task(
                            item_data, product_type, task, model_name, enriched_content, evaluator_id
                        )
                    )
                    task_context.append((task, model_name, model_data.get('model_version', '1.0'), evaluator_id))

        # Await and process results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for idx, result in enumerate(results):
            if isinstance(result, dict):
                # Extract context
                task, model_name, model_version, evaluator_id = task_context[idx]

                # Prepare evaluation result
                evaluation_result = {
                    "item_id": item_data["item_id"],
                    "item_product_type": product_type,
                    "task": task,
                    "model_name": model_name,
                    "model_version": model_version,
                    "evaluator_type": 'LLM',
                    "evaluator_id": evaluator_id,
                    "quality_score": result.get("quality_score"),
                    "relevance": result.get("relevance"),
                    "clarity": result.get("clarity"),
                    "compliance": result.get("compliance"),
                    "accuracy": result.get("accuracy"),
                    "reasoning": json.dumps(result.get("reasoning", {})),
                    "suggestions": json.dumps(result.get("suggestions", "None")),
                    "is_winner": False,
                    "comments": None
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

            # Prepare the data for insertion with serialization
           # Prepare the data for insertion
            data_to_insert = [
                (
                    result["item_id"],
                    result["item_product_type"],
                    result["task"],
                    result["model_name"],
                    result["model_version"],
                    result["evaluator_type"],
                    result.get("quality_score"),
                    result.get("relevance"),
                    result.get("clarity"),
                    result.get("compliance"),
                    result.get("accuracy"),
                    result.get("reasoning"),
                    result.get("suggestions"),
                    result.get("is_winner", False),
                    result.get("comments")
                )
                for result in results
            ]

            # Insert or replace into the appropriate table
            # Insert or replace into the evaluation_results table
            cursor.executemany("""
                INSERT INTO evaluation_results (
                    item_id, item_product_type, task, model_name, model_version,
                    evaluator_type, quality_score, relevance, clarity, compliance, accuracy,
                    reasoning, suggestions, is_winner, comments
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(item_id, task, model_name, model_version, evaluator_type)
                DO UPDATE SET
                    quality_score=excluded.quality_score,
                    relevance=excluded.relevance,
                    clarity=excluded.clarity,
                    compliance=excluded.compliance,
                    accuracy=excluded.accuracy,
                    reasoning=excluded.reasoning,
                    suggestions=excluded.suggestions,
                    is_winner=excluded.is_winner,
                    comments=excluded.comments
            """, data_to_insert)

            conn.commit()
            logging.info(f"{len(results)} rows upserted into evaluation_results.")

    def _aggregate_evaluations(self, evaluation_results):
        # Group evaluations by item_id, task, model_name, model_version
        grouped_evaluations = defaultdict(list)
        for eval_result in evaluation_results:
            key = (eval_result['item_id'], eval_result['task'], eval_result['model_name'], eval_result['model_version'])
            grouped_evaluations[key].append(eval_result)

        aggregated_results = []
        for key, evals in grouped_evaluations.items():
            item_id, task, model_name, model_version = key
            aggregated_metrics = self._calculate_aggregated_metrics(evals)

            # Prepare aggregated result
            aggregated_result = {
                'item_id': item_id,
                'item_product_type': evals[0]['item_product_type'],
                'task': task,
                'model_name': model_name,
                'model_version': model_version,
                **aggregated_metrics
            }
            aggregated_results.append(aggregated_result)

        return aggregated_results
    
    def _calculate_aggregated_metrics(self, evaluations):
        metrics = ['quality_score', 'relevance', 'clarity', 'compliance', 'accuracy']
        aggregated = {}
        for metric in metrics:
            scores = [e.get(metric) for e in evaluations if e.get(metric) is not None]
            if scores:
                mean_score = np.mean(scores)
                variance = np.var(scores, ddof=1)  # Sample variance
                confidence = self._determine_confidence_level(variance)
                aggregated[f'{metric}_mean'] = mean_score
                aggregated[f'{metric}_variance'] = variance
                aggregated[f'{metric}_confidence'] = confidence
            else:
                aggregated[f'{metric}_mean'] = None
                aggregated[f'{metric}_variance'] = None
                aggregated[f'{metric}_confidence'] = 'Unknown'
        return aggregated
    
    def _determine_confidence_level(self, variance):
        if variance is None:
            return 'Unknown'
        elif variance <= 0.5:
            return 'High'
        elif variance <= 1.5:
            return 'Medium'
        else:
            return 'Low'
        
    def _save_aggregated_results(self, aggregated_results):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Create table if it doesn't exist
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
    


        

