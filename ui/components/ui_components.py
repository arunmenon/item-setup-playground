import plotly.graph_objects as go

def generate_variance_distribution_plot(aggregated_df):
    import plotly.express as px
    import numpy as np
    import pandas as pd

    if aggregated_df.empty:
        return go.Figure()

    metrics = ['quality_score', 'relevance', 'clarity', 'compliance', 'accuracy']
    plot_data = []

    for metric in metrics:
        variance_col = f'{metric}_variance'
        temp_df = aggregated_df[['model_name', variance_col]]
        temp_df = temp_df.rename(columns={variance_col: 'variance'})
        temp_df['Metric'] = metric.capitalize()
        plot_data.append(temp_df)

    plot_df = pd.concat(plot_data, ignore_index=True)

    # Remove rows with NaN variance
    plot_df = plot_df.dropna(subset=['variance'])

    # Create box plot to show variance distribution
    fig = px.box(
        plot_df,
        x='Metric',
        y='variance',
        points='all',
        color='Metric',
        title='Variance Distribution Across Metrics',
        labels={'variance': 'Variance', 'Metric': 'Metric'}
    )

    fig.update_layout(
        xaxis_title='Metric',
        yaxis_title='Variance',
        showlegend=False
    )

    return fig

def generate_confidence_level_breakdown(aggregated_df):
    import plotly.express as px
    import pandas as pd

    if aggregated_df.empty:
        return go.Figure()

    metrics = ['quality_score', 'relevance', 'clarity', 'compliance', 'accuracy']
    plot_data = []

    for metric in metrics:
        confidence_col = f'{metric}_confidence'
        temp_df = aggregated_df[[confidence_col]]
        temp_df = temp_df.rename(columns={confidence_col: 'confidence_level'})
        temp_df['Metric'] = metric.capitalize()
        plot_data.append(temp_df)

    plot_df = pd.concat(plot_data, ignore_index=True)

    # Count of confidence levels per metric
    count_df = plot_df.groupby(['Metric', 'confidence_level']).size().reset_index(name='Count')

    # Create bar plot
    fig = px.bar(
        count_df,
        x='Metric',
        y='Count',
        color='confidence_level',
        barmode='group',
        title='Confidence Level Breakdown by Metric',
        labels={'Count': 'Number of Models', 'Metric': 'Metric', 'confidence_level': 'Confidence Level'}
    )

    fig.update_layout(
        xaxis_title='Metric',
        yaxis_title='Number of Models',
        legend_title='Confidence Level'
    )

    return fig

