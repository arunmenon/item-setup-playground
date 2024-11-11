import sqlite3
import json

class DatabaseHandler:
    def __init__(self, db_path="model_responses.db"):
        self.db_path = db_path

    def create_tables_if_not_exists(self):
        """
        Creates the required tables if they do not already exist.
        """
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
        conn.commit()
        conn.close()
        print("Tables created successfully if they did not exist.")

    def save_preference(self, item_gtin, product_type, task_type, model_responses, winner_response):
        """
        Saves the user preference (selected model response) into the database.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO responses (item_gtin, product_type, task_type, model_responses, winner_response)
            VALUES (?, ?, ?, ?, ?)
        ''', (item_gtin, product_type, task_type, json.dumps(model_responses), winner_response))
        conn.commit()
        conn.close()
