import sqlite3
import json

def migrate_detail_results_to_evaluation_results(db_path):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch all records from detail_results
    cursor.execute("SELECT * FROM detail_results")
    rows = cursor.fetchall()

    # Get column names from detail_results
    cursor.execute("PRAGMA table_info(detail_results)")
    columns_info = cursor.fetchall()
    column_names = [col[1] for col in columns_info]

    # Prepare insertion into evaluation_results
    for row in rows:
        row_dict = dict(zip(column_names, row))

        # Map fields to evaluation_results schema
        evaluation_result = {
            "item_id": row_dict.get("item_id"),
            "item_product_type": row_dict.get("item_product_type"),
            "task": row_dict.get("task"),
            "model_name": row_dict.get("model_name"),
            "model_version": row_dict.get("model_version"),
            "evaluator_type": "LLM",  # Since these are LLM evaluations
            "quality_score": row_dict.get("quality_score"),
            "relevance": None,  # Not available in old data
            "clarity": None,    # Not available in old data
            "compliance": None, # Not available in old data
            "accuracy": None,   # Not available in old data
            "reasoning": row_dict.get("reasoning"),
            "suggestions": row_dict.get("suggestions"),
            "is_winner": row_dict.get("is_winner"),
            "comments": None    # No comments in old data
        }

        # Insert into evaluation_results
        cursor.execute('''
            INSERT OR REPLACE INTO evaluation_results (
                item_id, item_product_type, task, model_name, model_version,
                evaluator_type, quality_score, relevance, clarity, compliance, accuracy,
                reasoning, suggestions, is_winner, comments
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            evaluation_result["item_id"],
            evaluation_result["item_product_type"],
            evaluation_result["task"],
            evaluation_result["model_name"],
            evaluation_result["model_version"],
            evaluation_result["evaluator_type"],
            evaluation_result["quality_score"],
            evaluation_result["relevance"],
            evaluation_result["clarity"],
            evaluation_result["compliance"],
            evaluation_result["accuracy"],
            evaluation_result["reasoning"],
            evaluation_result["suggestions"],
            evaluation_result["is_winner"],
            evaluation_result["comments"]
        ))

    # Commit changes and close connection
    conn.commit()
    conn.close()

    print("Migration completed successfully.")

# Usage
if __name__ == "__main__":
    migrate_detail_results_to_evaluation_results(db_path="results.db")
