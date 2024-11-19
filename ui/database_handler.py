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

        # Create responses table with model_name column
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_gtin TEXT,
                product_type TEXT,
                task_type TEXT,
                model_responses TEXT,
                winner_response TEXT,
                model_name TEXT,
                relevance INTEGER,
                clarity INTEGER,
                compliance INTEGER,
                accuracy INTEGER,
                comments TEXT
            )
        ''')

        # Check if 'model_name' column exists; add if not
        cursor.execute("PRAGMA table_info(responses)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'model_name' not in columns:
            cursor.execute("ALTER TABLE responses ADD COLUMN model_name TEXT")
            print("Added 'model_name' column to 'responses' table.")

        # Leaderboard table remains the same
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

    def save_preference(self, item_gtin, product_type, task_type, model_responses, winner_response,
                        model_name, relevance, clarity, compliance, accuracy, comments):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO responses (
                item_gtin, product_type, task_type, model_responses, winner_response,
                model_name, relevance, clarity, compliance, accuracy, comments
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (item_gtin, product_type, task_type, json.dumps(model_responses), winner_response,
              model_name, relevance, clarity, compliance, accuracy, comments))
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
        leaderboard_df = pd.read_sql_query('''
            SELECT
                l.task_type,
                l.product_type,
                l.model_name,
                l.preference_count,
                AVG(r.relevance) as avg_relevance,
                AVG(r.clarity) as avg_clarity,
                AVG(r.compliance) as avg_compliance,
                AVG(r.accuracy) as avg_accuracy
            FROM leaderboard l
            LEFT JOIN responses r
            ON l.model_name = r.model_name AND l.task_type = r.task_type AND l.product_type = r.product_type
            GROUP BY l.task_type, l.product_type, l.model_name
            ORDER BY l.preference_count DESC
        ''', conn)
        conn.close()
        return leaderboard_df
