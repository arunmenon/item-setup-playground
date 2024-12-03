import sqlite3
import pandas as pd
import os
import sys


def export_tables_to_csv(db_path, output_dir):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Loop through the tables and export each to a CSV file
    for table_name in tables:
        table_name = table_name[0]
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        csv_path = os.path.join(output_dir, f"{table_name}.csv")
        df.to_csv(csv_path, index=False)
        # df.to_parquet(csv_path, index=False)
        print(f"Table {table_name} exported to {csv_path}")

    # Close the database connection
    conn.close()


if __name__=="__main__":
    if len(sys.argv)!=3:
        print("Usage: python script.py <source_db_path> <output_dir>")
        sys.exit(1)

    source_db_path = sys.argv[1]
    output_dir = sys.argv[2]

    export_tables_to_csv(source_db_path, output_dir)