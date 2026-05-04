import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

def get_jose_visualization(app, df):
    df = df.copy()
    df["INSPECTION DATE"] = pd.to_datetime(df["INSPECTION DATE"])
    df["SCORE"] = pd.to_numeric(df["SCORE"])
    df = df[df["BORO"].astype(str)!="0"]
    df = df.dropna(subset=[
        "CAMIS",
        "DBA",
        "BORO",
        "CUISINE DESCRIPTION",
        "INSPECTION DATE",
        "SCORE"])
    df = df[df["INSPECTION DATE"] != pd.Timestamp("1900-01-01")]
    df = (df.sort_values("INSPECTION DATE").drop_duplicates(subset=["CAMIS", "INSPECTION DATE", "SCORE"]))
    df["inspection_month"] = (df["INSPECTION DATE"].dt.to_period("M").dt.to_timestamp())
    df["restaurant_label"] = (df["DBA"].astype(str)+" --> in "+df["BORO"].astype(str))
    restaurant_summary = (
        df.sort_values("INSPECTION DATE")
        .groupby("CAMIS")
        .agg(
            restaurant=("DBA", "first"),
            borough=("BORO", "first"),
            cuisine=("CUISINE DESCRIPTION", "first"),
            first_score=("SCORE", "first"),
            last_score=("SCORE", "last"),
            num_inspections=("SCORE", "count")
        )
        .reset_index()
    )
    restaurant_summary["score_change"] = (
        restaurant_summary["last_score"] - restaurant_summary["first_score"]
    )
    # Check: Restaurants had 3 inspections and had a A Grade at least
    eligible_restaurants = restaurant_summary[
        (restaurant_summary["first_score"] <= 13) &
        (restaurant_summary["num_inspections"] >= 3)
    ]
    eligible_ids = eligible_restaurants["CAMIS"]
    df = df[df["CAMIS"].isin(eligible_ids)]
    # boroughs = sorted(df["BORO"].dropna().unique())
    to_return = html.Div(
        style={
            "fontFamily": "Times New Roman",
            # "padding": "25px",
            "flex": "1",
            "minWidth": "0"
        },
        children=[
            dcc.Graph(id="line-chart"),
        ]
    )
    @app.callback(
        Output("line-chart", "figure"),
        Input("global-borough-filter", "value"),
        Input("global-cuisine-filter", "value")
    )
    def update_chart(selected_boroughs, selected_cuisines):
        filtered = df.copy()
        filtered = filtered[filtered["BORO"].isin(selected_boroughs)]
        filtered = filtered[filtered["CUISINE DESCRIPTION"].isin(selected_cuisines)]
        avg_df = (
            filtered
            .groupby(["CUISINE DESCRIPTION", "inspection_month"], as_index=False)
            .agg(
                avg_score=("SCORE", "mean"),
                inspection_count=("SCORE", "count")
            )
        )
        # 10 Limit
        top_cuisines = (
            filtered["CUISINE DESCRIPTION"]
            .value_counts()
            .head(10)
            .index
        )
        avg_df = avg_df[
            avg_df["CUISINE DESCRIPTION"].isin(top_cuisines)
        ]
        fig = px.line(
            avg_df,
            x="inspection_month",
            y="avg_score",
            color="CUISINE DESCRIPTION",
            markers=True,
            hover_data=["inspection_count"],
            title="Average Inspection Score Over Time by Cuisine<br><sub>Lower scores are Good. Higher scores means more violations with respect to Time.</sub>"
        )
        fig.update_layout(
            template="simple_white",
            xaxis_title="Inspection Month",
            yaxis_title="Average Inspection Score",
            legend_title="Cuisine"
        )
        # A Grade Line
        fig.add_hline(
            y=13,
            line_dash="dash",
            line_width=2,
            line_color="green",
            annotation_text="A-grade Maximum Score: 13",
            annotation_position="bottom left",
        )
        return fig
    return to_return

