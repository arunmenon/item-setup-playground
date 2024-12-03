import sqlite3

def initialize_database(schema_path, db_path="external_database.db"):
    with sqlite3.connect(db_path) as conn:
        with open(schema_path, 'r') as f:
            schema = f.read()
        conn.executescript(schema)
        print("Database initialized with the schema.")

# Initialize the database
initialize_database('schema.sql')
