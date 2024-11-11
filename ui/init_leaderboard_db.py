import sqlite3

def init_db():
    conn = sqlite3.connect("model_responses.db")
    cursor = conn.cursor()
    
    # Table to store individual responses and user preferences
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

    # Table to store leaderboard counts for each model
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaderboard (
            task_type TEXT,
            product_type TEXT,
            model_name TEXT,
            preference_count INTEGER DEFAULT 0,
            PRIMARY KEY (task_type, product_type, model_name)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized with responses and leaderboard tables.")

if __name__ == "__main__":
    init_db()
