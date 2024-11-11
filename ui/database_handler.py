import sqlite3
import json
import pandas as pd

class DatabaseHandler:
    def __init__(self, db_path="model_responses.db"):
        self.db_path = db_path
        self.create_tables_if_not_exists()

    def create_tables_if_not_exists(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_gtin TEXT,
                product_type TEXT,
                task_type TEXT,
                model_responses TEXT,
                winner_response TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaderboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT,
                product_type TEXT,
                model_name TEXT,
                preference_count INTEGER DEFAULT 0
            )
        ''')

        conn.commit()
        conn.close()

    def save_preference(self, item_gtin, product_type, task_type, model_responses, winner_response):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO responses (item_gtin, product_type, task_type, model_responses, winner_response)
            VALUES (?, ?, ?, ?, ?)
        ''', (item_gtin, product_type, task_type, json.dumps(model_responses), winner_response))
        conn.commit()
        conn.close()

    def increment_model_preference(self, task_type, product_type, model_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT preference_count FROM leaderboard
            WHERE task_type = ? AND product_type = ? AND model_name = ?
        ''', (task_type, product_type, model_name))
        result = cursor.fetchone()

        if result:
            cursor.execute('''
                UPDATE leaderboard
                SET preference_count = preference_count + 1
                WHERE task_type = ? AND product_type = ? AND model_name = ?
            ''', (task_type, product_type, model_name))
        else:
            cursor.execute('''
                INSERT INTO leaderboard (task_type, product_type, model_name, preference_count)
                VALUES (?, ?, ?, 1)
            ''', (task_type, product_type, model_name))

        conn.commit()
        conn.close()

    def get_leaderboard(self):
        conn = sqlite3.connect(self.db_path)
        leaderboard_df = pd.read_sql_query("SELECT task_type, product_type, model_name, preference_count FROM leaderboard ORDER BY preference_count DESC", conn)
        conn.close()
        return leaderboard_df
