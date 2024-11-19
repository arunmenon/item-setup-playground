import plotly.express as px
import plotly.graph_objects as go

def generate_leaderboard_plot(leaderboard_df):
    if leaderboard_df.empty:
        return None

    # Prepare custom data array including 'product_type' and average ratings
    custom_data = leaderboard_df[[
        "product_type",
        "avg_relevance",
        "avg_clarity",
        "avg_compliance",
        "avg_accuracy"
    ]].values

    fig = px.bar(
        leaderboard_df,
        x="model_name",
        y="preference_count",
        color="product_type",
        barmode="group",
        title="Model Preferences by Product Type",
        hover_data={
            "model_name": False,        # Exclude 'model_name' from automatic hover
            "preference_count": False,  # Exclude 'preference_count' from automatic hover
            "product_type": False,      # Exclude 'product_type' from automatic hover
            "avg_relevance": False,
            "avg_clarity": False,
            "avg_compliance": False,
            "avg_accuracy": False
        },
        height=400,
        width=600,
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig.update_traces(
        customdata=custom_data,  # Include custom data for hover template
        marker_line_width=1.0,
        opacity=0.8,
        hovertemplate=(
            "<b>Model Name:</b> %{x}<br>"
            "<b>Preference Count:</b> %{y}<br>"
            "<b>Product Type:</b> %{customdata[0]}<br>"
            "<b>Avg Relevance:</b> %{customdata[1]:.2f}<br>"
            "<b>Avg Clarity:</b> %{customdata[2]:.2f}<br>"
            "<b>Avg Compliance:</b> %{customdata[3]:.2f}<br>"
            "<b>Avg Accuracy:</b> %{customdata[4]:.2f}<br>"
        )
    )

    fig.update_layout(
        xaxis_title="Model Name",
        yaxis_title="Preference Count",
        legend_title="Product Type",
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
