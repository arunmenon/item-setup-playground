import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def generate_leaderboard_plot(leaderboard_df):
    if leaderboard_df.empty:
        return go.Figure()

    fig = px.bar(
        leaderboard_df,
        x="model_name",
        y="preference_count",
        color="evaluator_type",
        barmode="group",
        facet_col="product_type",
        title="Model Preferences by Evaluator Type",
        hover_data={
            "model_name": False,
            "preference_count": False,
            "evaluator_type": False,
        },
        height=400,
        width=800,
    )

    fig.update_layout(
        xaxis_title="Model Name",
        yaxis_title="Preference Count",
        legend_title="Evaluator Type",
        font=dict(
            family="Arial",
            size=12
        ),
        margin=dict(l=20, r=20, t=50, b=50),
        plot_bgcolor='white',
        autosize=False
    )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='lightgray')

    return fig

def generate_correlation_heatmap(detail_results_df):
    # Calculate correlation matrix
    correlation_matrix = detail_results_df[['quality_score', 'relevance', 'clarity', 'compliance', 'accuracy']].corr()

    fig = px.imshow(
        correlation_matrix,
        text_auto=True,
        color_continuous_scale='Viridis',
        title='Correlation Heatmap of Evaluation Metrics'
    )

    fig.update_layout(
        autosize=False,
        width=500,
        height=500,
        margin=dict(l=50, r=50, t=50, b=50)
    )

    return fig

def generate_winner_model_comparison_plot(evaluation_df):
    # Filter data for winner models with both LLM and human evaluations
    human_evals = evaluation_df[
        (evaluation_df['is_winner'] == True) &
        (evaluation_df['evaluator_type'] == 'Human')
    ]

    if human_evals.empty:
        return go.Figure()

    llm_evals = evaluation_df[
        (evaluation_df['evaluator_type'] == 'LLM')
    ]

    merged_df = pd.merge(
        human_evals,
        llm_evals,
        on=['item_id', 'task', 'model_name', 'model_version'],
        suffixes=('_human', '_llm')
    )

    if merged_df.empty:
        return go.Figure()

    # Metrics to compare
    metrics = ['relevance', 'clarity', 'compliance', 'accuracy']

    # Melt the DataFrame for plotting
    plot_data = []
    for metric in metrics:
        if metric + '_human' in merged_df.columns and metric + '_llm' in merged_df.columns:
            temp_df = merged_df[['model_name', metric + '_human', metric + '_llm']]
            temp_df = temp_df.melt(id_vars=['model_name'], var_name='Evaluator', value_name='Score')
            temp_df['Metric'] = metric.capitalize()
            plot_data.append(temp_df)

    if not plot_data:
        return go.Figure()

    plot_df = pd.concat(plot_data)

    # Clean evaluator names
    plot_df['Evaluator'] = plot_df['Evaluator'].map({
        metric + '_human': 'Human',
        metric + '_llm': 'LLM'
    })

    fig = px.bar(
        plot_df,
        x='model_name',
        y='Score',
        color='Evaluator',
        barmode='group',
        facet_col='Metric',
        title='Comparison of Evaluations by Evaluator Type for Winner Models',
        height=600
    )

    fig.update_layout(
        xaxis_title='Model Name',
        yaxis_title='Score',
        legend_title='Evaluator Type'
    )

    return fig
