import sqlite3
import json
import pandas as pd

class DatabaseHandler:
    def __init__(self, db_path="model_responses.db"):
        self.db_path = db_path

    def create_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create evaluation_results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evaluation_results (
                item_id TEXT,
                item_product_type TEXT,
                task TEXT,
                model_name TEXT,
                model_version TEXT,
                evaluator_type TEXT,
                evaluator_id TEXT,
                quality_score INTEGER,
                relevance INTEGER,
                clarity INTEGER,
                compliance INTEGER,
                accuracy INTEGER,
                reasoning TEXT,
                suggestions TEXT,
                is_winner BOOLEAN,
                comments TEXT,
                PRIMARY KEY (item_id, task, model_name, model_version, evaluator_type, evaluator_id)
            )
        ''')

        # Create aggregated_evaluations table
        cursor.execute('''
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
                model_name,
                model_version,
                evaluator_type,
                COUNT(CASE WHEN is_winner = TRUE THEN 1 END) AS preference_count,
                ROUND(AVG(quality_score), 2) AS avg_quality_score,
                ROUND(AVG(relevance), 2) AS avg_relevance,
                ROUND(AVG(clarity), 2) AS avg_clarity,
                ROUND(AVG(compliance), 2) AS avg_compliance,
                ROUND(AVG(accuracy), 2) AS avg_accuracy
            FROM evaluation_results
            WHERE 1=1
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
            GROUP BY model_name, model_version, evaluator_type
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
