import sqlite3
import json
import pandas as pd

class DatabaseHandler:
    def __init__(self, db_path="model_responses.db"):
        self.db_path = db_path

    def create_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evaluation_results (
                item_id TEXT,
                item_product_type TEXT,
                task TEXT,
                model_name TEXT,
                model_version TEXT,
                evaluator_type TEXT,
                quality_score INTEGER,
                relevance INTEGER,
                clarity INTEGER,
                compliance INTEGER,
                accuracy INTEGER,
                reasoning TEXT,
                suggestions TEXT,
                is_winner BOOLEAN,
                comments TEXT,
                PRIMARY KEY (item_id, task, model_name, model_version, evaluator_type)
            )
        ''')
        conn.commit()
        conn.close()

    def save_evaluation(self, item_id, product_type, task, model_name, model_version,
                        evaluator_type, quality_score=None, relevance=None, clarity=None,
                        compliance=None, accuracy=None, reasoning=None, suggestions=None,
                        is_winner=False, comments=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO evaluation_results (
                item_id, item_product_type, task, model_name, model_version,
                evaluator_type, quality_score, relevance, clarity, compliance, accuracy,
                reasoning, suggestions, is_winner, comments
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item_id, product_type, task, model_name, model_version, evaluator_type,
            quality_score, relevance, clarity, compliance, accuracy,
            reasoning, suggestions, is_winner, comments
        ))
        conn.commit()
        conn.close()

    def get_evaluations(self, evaluator_type=None, task=None, item_id=None,
                        product_type=None, model_name=None):
        query = '''
            SELECT * FROM evaluation_results WHERE 1=1
        '''
        params = []

        if evaluator_type:
            query += ' AND evaluator_type = ?'
            params.append(evaluator_type)
        if task:
            query += ' AND task = ?'
            params.append(task)
        if item_id:
            query += ' AND item_id = ?'
            params.append(item_id)
        if product_type:
            query += ' AND item_product_type = ?'
            params.append(product_type)
        if model_name:
            query += ' AND model_name = ?'
            params.append(model_name)

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
