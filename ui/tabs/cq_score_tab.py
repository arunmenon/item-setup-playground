# File: cq_score_tab.py

import gradio as gr
import pandas as pd
import plotly.express as px
import logging
from google.cloud import bigquery

class CQScoreAggregator:
    """
    Minimal aggregator that runs your union-based query in BigQuery 
    to get model_name + cq_score for both 'catalog' (original) 
    and actual model_name (enriched).
    """

    def __init__(self, project_id: str, dataset: str = "item_setup_playground"):
        self.client = bigquery.Client(project=project_id)
        self.dataset = dataset

    def get_cq_scores(self, task: str = "short_description_enhancement") -> pd.DataFrame:
        """
        Runs the union query to get:
          model_name, round(cq_score*100,2) as cq_score
        from (select 'catalog' ... union all select model_name ...)
        and sorts by cq_score desc.
        """
        # Adjust table name if needed
        table = f"`{self.client.project}.{self.dataset}.cq_evaluation_results`"

        query = f"""
        SELECT 
          model_name,
          ROUND(cq_score * 100, 2) AS cq_score
        FROM (
          SELECT 
            'catalog' AS model_name,
            AVG(original_score) AS cq_score
          FROM {table}
          WHERE task = @task
          GROUP BY model_name
          
          UNION ALL
          
          SELECT 
            model_name,
            AVG(enriched_score) AS cq_score
          FROM {table}
          WHERE task = @task
          GROUP BY model_name
        )
        ORDER BY cq_score DESC
        """

        logging.debug("CQ Score query:\n%s", query)

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("task", "STRING", task)
            ]
        )
        df = self.client.query(query, job_config=job_config).to_dataframe()
        return df

def create_cq_score_tab(project_id: str, default_dataset: str = "item_setup_playground"):
    """
    Creates a new Gradio tab: "CQ Score Tab"
    which runs the aggregator query for a chosen 'task' 
    (default 'short_description_enhancement') 
    and shows a bar chart + data table of model_name vs. CQ score.
    """
    aggregator = CQScoreAggregator(project_id=project_id, dataset=default_dataset)

    with gr.TabItem("CQ Score"):
        gr.Markdown("## Enriched Short Description CQ Scores")

        # Let user pick a task if desired
        task_selector = gr.Dropdown(
            label="Select Task",
            choices=["short_description_enhancement", "long_description_enhancement", "title_enhancement"],
            value="short_description_enhancement"
        )

        output_df = gr.Dataframe(label="CQ Score Table")
        output_plot = gr.Plot(label="CQ Score Chart")

        def refresh_cq_scores(task):
            df = aggregator.get_cq_scores(task=task)
            if df.empty:
                return df, None
            # Build a bar chart
            fig = px.bar(
                df,
                x="model_name",
                y="cq_score",
                title=f"Enriched {task} CQ Scores",
                labels={"cq_score":"CQ Score (%)"},
                text="cq_score"
            )
            # Sort bars descending by y
            fig.update_layout(xaxis={'categoryorder':'total descending'})
            fig.update_traces(textposition="outside")
            return df, fig

        task_selector.change(
            fn=refresh_cq_scores,
            inputs=[task_selector],
            outputs=[output_df, output_plot]
        )
