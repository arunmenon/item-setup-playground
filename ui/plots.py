import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def generate_leaderboard_plot(leaderboard_df):
    if leaderboard_df.empty:
        return go.Figure()

    # Ensure necessary columns are present
    required_columns = ['model_name', 'preference_count', 'evaluator_type', 'product_type']
    for col in required_columns:
        if col not in leaderboard_df.columns:
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
            "model_name": True,
            "preference_count": True,
            "evaluator_type": True,
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

def generate_correlation_heatmap(evaluation_df):
    if evaluation_df.empty:
        return go.Figure()

    # Parse 'evaluation_data' column
    evaluation_df['evaluation_data_parsed'] = evaluation_df['evaluation_data'].apply(lambda x: json.loads(x) if pd.notnull(x) else {})

    # Extract numeric metrics
    metrics = set()
    for data in evaluation_df['evaluation_data_parsed']:
        metrics.update([k for k, v in data.items() if isinstance(v, (int, float))])

    if not metrics:
        return go.Figure()

    # Create columns for each metric
    for metric in metrics:
        evaluation_df[metric] = evaluation_df['evaluation_data_parsed'].apply(lambda x: x.get(metric))

    # Drop rows where all metrics are NaN
    evaluation_df.dropna(subset=metrics, how='all', inplace=True)

    if evaluation_df.empty:
        return go.Figure()

    # Calculate correlation matrix
    correlation_matrix = evaluation_df[list(metrics)].corr()

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
    if evaluation_df.empty:
        return go.Figure()

    # Parse 'evaluation_data' column
    evaluation_df['evaluation_data_parsed'] = evaluation_df['evaluation_data'].apply(lambda x: json.loads(x) if pd.notnull(x) else {})

    # Extract evaluator_type and is_winner
    evaluation_df['evaluator_type'] = evaluation_df['evaluator_type'].fillna('Unknown')
    evaluation_df['is_winner'] = evaluation_df['is_winner'].fillna(False)

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

    # Merge on relevant keys
    merge_keys = ['item_id', 'generation_task', 'evaluation_task', 'model_name', 'model_version']
    merged_df = pd.merge(
        human_evals,
        llm_evals,
        on=merge_keys,
        suffixes=('_human', '_llm')
    )

    if merged_df.empty:
        return go.Figure()

    # Extract metrics from evaluation_data
    metrics = set()
    for data in merged_df['evaluation_data_parsed_human']:
        metrics.update([k for k, v in data.items() if isinstance(v, (int, float))])
    for data in merged_df['evaluation_data_parsed_llm']:
        metrics.update([k for k, v in data.items() if isinstance(v, (int, float))])

    if not metrics:
        return go.Figure()

    # Prepare data for plotting
    plot_data = []
    for metric in metrics:
        # Extract metric values
        merged_df[f'{metric}_human'] = merged_df['evaluation_data_parsed_human'].apply(lambda x: x.get(metric))
        merged_df[f'{metric}_llm'] = merged_df['evaluation_data_parsed_llm'].apply(lambda x: x.get(metric))

        if merged_df[[f'{metric}_human', f'{metric}_llm']].dropna(how='all').empty:
            continue

        temp_df = merged_df[['model_name', f'{metric}_human', f'{metric}_llm']]
        temp_df = temp_df.melt(id_vars=['model_name'], var_name='Evaluator', value_name='Score')
        temp_df['Metric'] = metric.capitalize()
        plot_data.append(temp_df)

    if not plot_data:
        return go.Figure()

    plot_df = pd.concat(plot_data, ignore_index=True)

    # Clean evaluator names
    plot_df['Evaluator'] = plot_df['Evaluator'].apply(lambda x: 'Human' if x.endswith('_human') else ('LLM' if x.endswith('_llm') else x))

    # Remove NaN scores
    plot_df.dropna(subset=['Score'], inplace=True)

    if plot_df.empty:
        return go.Figure()

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

def generate_aggregated_plot(aggregated_df):
    if aggregated_df.empty:
        return go.Figure()

    # Prepare data
    plot_df = aggregated_df.copy()
    plot_df['Metric'] = plot_df['metric_name'].str.capitalize()
    plot_df['mean_score'] = plot_df['metric_mean']
    plot_df['variance'] = plot_df['metric_variance']
    plot_df['confidence_level'] = plot_df['metric_confidence']

    # Calculate standard deviation for error bars
    plot_df['std_dev'] = plot_df['variance'].apply(lambda x: np.sqrt(x) if pd.notnull(x) else None)

    # Remove entries with NaN mean_score
    plot_df.dropna(subset=['mean_score'], inplace=True)

    if plot_df.empty:
        return go.Figure()

    # Create bar plot with error bars
    fig = px.bar(
        plot_df,
        x='model_name',
        y='mean_score',
        color='confidence_level',
        error_y='std_dev',
        barmode='group',
        facet_col='Metric',
        title='Aggregated Evaluation Metrics with Confidence Levels',
        height=600
    )

    fig.update_layout(
        xaxis_title='Model Name',
        yaxis_title='Mean Score',
        legend_title='Confidence Level'
    )

    return fig

def generate_variance_distribution_plot(aggregated_df):
    if aggregated_df.empty:
        return go.Figure()

    plot_df = aggregated_df.copy()
    plot_df['Metric'] = plot_df['metric_name'].str.capitalize()
    plot_df['variance'] = aggregated_df['metric_variance']

    # Remove entries with NaN variance
    plot_df.dropna(subset=['variance'], inplace=True)

    if plot_df.empty:
        return go.Figure()

    # Create box plot to show variance distribution
    fig = px.box(
        plot_df,
        x='Metric',
        y='variance',
        points='all',
        color='Metric',
        title='Variance Distribution Across Metrics'
    )

    fig.update_layout(
        xaxis_title='Metric',
        yaxis_title='Variance',
        showlegend=False
    )

    return fig

def generate_confidence_level_breakdown(aggregated_df):
    if aggregated_df.empty:
        return go.Figure()

    plot_df = aggregated_df.copy()
    plot_df['Metric'] = plot_df['metric_name'].str.capitalize()
    plot_df['confidence_level'] = plot_df['metric_confidence']

    # Remove entries with NaN confidence levels
    plot_df.dropna(subset=['confidence_level'], inplace=True)

    if plot_df.empty:
        return go.Figure()

    # Count of confidence levels per metric
    count_df = plot_df.groupby(['Metric', 'confidence_level']).size().reset_index(name='Count')

    # Create bar plot
    fig = px.bar(
        count_df,
        x='Metric',
        y='Count',
        color='confidence_level',
        barmode='group',
        title='Confidence Level Breakdown by Metric'
    )

    fig.update_layout(
        xaxis_title='Metric',
        yaxis_title='Number of Evaluations',
        legend_title='Confidence Level'
    )

    return fig



