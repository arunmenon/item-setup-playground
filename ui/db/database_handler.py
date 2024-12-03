import sqlite3
import json
import pandas as pd

class DatabaseHandler:
    def __init__(self, db_path="external_database.db"):
        self.db_path = db_path

    def create_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create evaluation_results table
        # Create evaluation_results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evaluation_results (
                item_id TEXT,
                item_product_type TEXT,
                generation_task TEXT,
                evaluation_task TEXT,
                model_name TEXT,
                model_version TEXT,
                evaluator_type TEXT,
                evaluator_id TEXT,
                evaluation_data TEXT,  -- Stores the JSON output
                is_winner BOOLEAN,
                comments TEXT,
                PRIMARY KEY (
                    item_id,
                    generation_task,
                    evaluation_task,
                    model_name,
                    model_version,
                    evaluator_type,
                    evaluator_id
                )
            )
        ''')

        # Create aggregated_evaluations table (Optional)
        # Adjusted to accommodate dynamic metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aggregated_evaluations (
                item_id TEXT,
                item_product_type TEXT,
                generation_task TEXT,
                evaluation_task TEXT,
                model_name TEXT,
                model_version TEXT,
                evaluator_type TEXT,
                evaluator_id TEXT,
                metric_name TEXT,
                metric_mean REAL,
                metric_variance REAL,
                metric_confidence TEXT,
                PRIMARY KEY (
                    item_id,
                    generation_task,
                    evaluation_task,
                    model_name,
                    model_version,
                    evaluator_type,
                    evaluator_id,
                    metric_name
                )
            )
        ''')

        conn.commit()
        conn.close()


    def save_evaluation(self, evaluation_result):
        """
        Save an evaluation result to the evaluation_results table.

        Args:
            evaluation_result (dict): The evaluation result data.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO evaluation_results (
                item_id, item_product_type, generation_task, evaluation_task, model_name,
                model_version, evaluator_type, evaluator_id, evaluation_data, is_winner, comments
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            evaluation_result['item_id'],
            evaluation_result['item_product_type'],
            evaluation_result['generation_task'],
            evaluation_result['evaluation_task'],
            evaluation_result['model_name'],
            evaluation_result['model_version'],
            evaluation_result['evaluator_type'],
            evaluation_result['evaluator_id'],
            json.dumps(evaluation_result['evaluation_data']),  # Serialize JSON data
            evaluation_result.get('is_winner', False),
            evaluation_result.get('comments')
        ))
        conn.commit()
        conn.close()


    def get_evaluations(self, **filters):
        """
        Retrieve evaluations from the evaluation_results table.

        Args:
            filters: Keyword arguments for filtering (e.g., evaluator_type='LLM')
        """
        query = '''
            SELECT * FROM evaluation_results WHERE 1=1
        '''
        params = []

        for key, value in filters.items():
            query += f' AND {key} = ?'
            params.append(value)

        with sqlite3.connect(self.db_path) as conn:
            evaluations_df = pd.read_sql_query(query, conn, params=params)

        return evaluations_df

    def get_leaderboard(self, task=None, product_type=None, evaluator_type=None):
        query = '''
            SELECT
                task,
                item_product_type AS product_type,
                model_name,
                model_version,
                evaluator_type,
                COUNT(is_winner) AS preference_count,
                AVG(quality_score) AS avg_quality_score,
                AVG(relevance) AS avg_relevance,
                AVG(clarity) AS avg_clarity,
                AVG(compliance) AS avg_compliance,
                AVG(accuracy) AS avg_accuracy
            FROM evaluation_results
            WHERE is_winner = 1
        '''
        params = []

        if task:
            query += ' AND task = ?'
            params.append(task)
        if product_type:
            query += ' AND item_product_type = ?'
            params.append(product_type)
        if evaluator_type:
            query += ' AND evaluator_type = ?'
            params.append(evaluator_type)

        query += '''
            GROUP BY task, item_product_type, model_name, model_version, evaluator_type
            ORDER BY preference_count DESC
        '''

        with sqlite3.connect(self.db_path) as conn:
            leaderboard_df = pd.read_sql_query(query, conn, params=params)

        return leaderboard_df
    
    def get_aggregated_evaluations(self, task=None, product_type=None, model_name=None):
        query = '''
            SELECT
                task,
                item_product_type AS product_type,
                model_name,
                model_version,
                quality_score_mean,
                quality_score_variance,
                quality_score_confidence,
                relevance_mean,
                relevance_variance,
                relevance_confidence,
                clarity_mean,
                clarity_variance,
                clarity_confidence,
                compliance_mean,
                compliance_variance,
                compliance_confidence,
                accuracy_mean,
                accuracy_variance,
                accuracy_confidence
            FROM aggregated_evaluations
            WHERE 1=1
        '''
        params = []

        if task:
            query += ' AND task = ?'
            params.append(task)
        if product_type:
            query += ' AND item_product_type = ?'
            params.append(product_type)
        if model_name:
            query += ' AND model_name = ?'
            params.append(model_name)

        with sqlite3.connect(self.db_path) as conn:
            aggregated_df = pd.read_sql_query(query, conn, params=params)

        return aggregated_df