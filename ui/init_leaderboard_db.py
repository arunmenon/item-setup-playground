import sqlite3

def init_db():
    conn = sqlite3.connect("model_responses.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_gtin TEXT,
            product_type TEXT,
            task_type TEXT,
            model_responses TEXT,    -- JSON-encoded model responses
            winner_response TEXT      -- The selected preferred response
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized and table created with generic schema for model responses.")

if __name__ == "__main__":
    init_db()
