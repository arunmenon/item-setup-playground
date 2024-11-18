import sqlite3
import json
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


def count_rows(db_path, table_name, filters=None):
    """
    Count rows in a table with optional filters.

    Args:
        db_path (str): Path to the SQLite database.
        table_name (str): Name of the table to query.
        filters (dict, optional): Filters to apply to the count query. Example: {"task": "title"}.

    Returns:
        int: Row count.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Build the count query
            query = f"SELECT COUNT(*) FROM {table_name}"
            query_params = []

            if filters:
                filter_clauses = []
                for key, value in filters.items():
                    filter_clauses.append(f"{key} = ?")
                    query_params.append(value)
                query += " WHERE " + " AND ".join(filter_clauses)

            # Execute the query
            cursor.execute(query, query_params)
            row_count = cursor.fetchone()[0]
            return row_count
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return 0


def query_results(db_path, table_name, filters=None):
    """
    Query results from the SQLite database.

    Args:
        db_path (str): Path to the SQLite database.
        table_name (str): Name of the table to query.
        filters (dict, optional): Filters to apply to the query.

    Returns:
        list[dict]: Query results.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Build the query
            query = f"SELECT * FROM {table_name}"
            query_params = []

            if filters:
                filter_clauses = []
                for key, value in filters.items():
                    filter_clauses.append(f"{key} = ?")
                    query_params.append(value)
                query += " WHERE " + " AND ".join(filter_clauses)

            # Execute the query
            cursor.execute(query, query_params)
            rows = cursor.fetchall()

            # Fetch column names for creating a result dictionary
            column_names = [description[0] for description in cursor.description]
            results = [dict(zip(column_names, row)) for row in rows]

            # Deserialize JSON fields (reasoning and suggestions)
            for result in results:
                if "reasoning" in result and isinstance(result["reasoning"], str):
                    try:
                        result["reasoning"] = json.loads(result["reasoning"])
                    except json.JSONDecodeError:
                        pass
                if "suggestions" in result and isinstance(result["suggestions"], str):
                    try:
                        result["suggestions"] = json.loads(result["suggestions"])
                    except json.JSONDecodeError:
                        pass

            return results
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="SQLite Database Utility Script.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # Subparser for listing tables
    list_tables_parser = subparsers.add_parser("list_tables", help="List all tables in the database")
    list_tables_parser.add_argument("--db_path", type=str, required=True, help="Path to the SQLite database.")

    # Subparser for querying results
    query_parser = subparsers.add_parser("query", help="Query data from a table")
    query_parser.add_argument("--db_path", type=str, required=True, help="Path to the SQLite database.")
    query_parser.add_argument("--table_name", type=str, required=True, help="Name of the table to query.")
    query_parser.add_argument("--filters", type=str, nargs="*", help="Filters in the form key=value (e.g., task=title).")

    # Subparser for counting rows
    count_parser = subparsers.add_parser("count", help="Count rows in a table")
    count_parser.add_argument("--db_path", type=str, required=True, help="Path to the SQLite database.")
    count_parser.add_argument("--table_name", type=str, required=True, help="Name of the table to query.")
    count_parser.add_argument("--filters", type=str, nargs="*", help="Filters in the form key=value (e.g., task=title).")

    args = parser.parse_args()

    if args.command == "list_tables":
        # List all tables in the database
        list_tables(args.db_path)
    elif args.command == "query":
        # Parse filters for querying results
        filters = {}
        if args.filters:
            for filter_pair in args.filters:
                key, value = filter_pair.split("=", 1)
                filters[key] = value

        # Query the database
        results = query_results(args.db_path, args.table_name, filters)

        # Print the results
        if results:
            print(f"Queried {len(results)} rows from {args.table_name}:")
            for result in results:
                print(json.dumps(result, indent=2))
        else:
            print(f"No results found in {args.table_name} with the given filters.")
    elif args.command == "count":
        # Parse filters for counting rows
        filters = {}
        if args.filters:
            for filter_pair in args.filters:
                key, value = filter_pair.split("=", 1)
                filters[key] = value

        # Count rows in the database
        row_count = count_rows(args.db_path, args.table_name, filters)
        print(f"Row count in {args.table_name}: {row_count}")
