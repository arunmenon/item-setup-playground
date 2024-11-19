import sqlite3
import argparse

def list_tables(db_path):
    """
    List all tables in the SQLite database.

    Args:
        db_path (str): Path to the SQLite database.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            if tables:
                print("Tables in the database:")
                for table in tables:
                    print(table[0])
            else:
                print("No tables found in the database.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List tables in the SQLite database.")
    parser.add_argument("--db_path", type=str, required=True, help="Path to the SQLite database.")
    args = parser.parse_args()
    list_tables(args.db_path)
