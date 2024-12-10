# bigquery_store.py

from google.cloud import bigquery
import logging

class BigQueryEvaluationStore:
    def __init__(self, evaluation_table, aggregated_table):
        self.client = bigquery.Client()
        self.evaluation_table = evaluation_table
        self.aggregated_table = aggregated_table

    def save_evaluations(self, evaluation_results):
        if not evaluation_results:
            return
        errors = self.client.insert_rows_json(self.evaluation_table, evaluation_results)
        if errors:
            logging.error(f"Error inserting evaluation_results: {errors}")
        else:
            logging.info(f"Inserted {len(evaluation_results)} evaluation results into {self.evaluation_table}.")

    def save_aggregated_evaluation_results(self, aggregated_results):
        if not aggregated_results:
            return
        errors = self.client.insert_rows_json(self.aggregated_table, aggregated_results)
        if errors:
            logging.error(f"Error inserting aggregated_evaluations: {errors}")
        else:
            logging.info(f"Inserted {len(aggregated_results)} aggregated results into {self.aggregated_table}.")
