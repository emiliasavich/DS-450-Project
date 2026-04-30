import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

app = dash.Dash(__name__)
df = pd.read_csv("DOHMH_New_York_City_Restaurant_Inspection_Results_20260430.csv")
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
boroughs = sorted(df["BORO"].dropna().unique())
cuisines = sorted(df["CUISINE DESCRIPTION"].dropna().unique())
app.layout = html.Div(
    style={
        "fontFamily": "Times New Roman",
        "padding": "25px"
    },
    children=[
        html.H2("NYC Restaurant Inspection Score Trends"),
        html.P(
            "Chart focuses on Restaurants with Lower Scores. "
            "Lower scores are Good. Higher scores means more violations with respect to Time"
        ),
        html.P(
            "Limit to 10 Selections Per View!"
        ),
        html.Div([
            html.Label("Select Borough:"),
            dcc.Dropdown(
                id="borough-select",
                options=[{"label": b, "value": b} for b in boroughs],
                value=boroughs,
                multi=True
            ),
        ]),
        html.Br(),
        html.Div([
            html.Label("Select Cuisine:"),
            dcc.Dropdown(
                id="cuisine-select",
                options=[{"label": c, "value": c} for c in cuisines],
                value=[],
                multi=True,
                placeholder="Default: No Selection for all cuisine"
            ),
        ]),
        html.Br(),
        html.Div([
            html.Label("Chart View:"),
            dcc.RadioItems(
                id="chart-view",
                options=[
                    {
                        "label": "Individual Restaurants",
                        "value": "individual"
                    },
                    {
                        "label": "Average by Cuisine",
                        "value": "average"
                    }
                ],
                value="average",
                inline=True
            )
        ]),
        dcc.Graph(id="line-chart")
    ]
)
@app.callback(
    Output("line-chart", "figure"),
    Input("borough-select", "value"),
    Input("cuisine-select", "value"),
    Input("chart-view", "value")
)
def update_chart(selected_boroughs, selected_cuisines, chart_view):
    filtered = df.copy()
    if selected_boroughs:
        filtered = filtered[filtered["BORO"].isin(selected_boroughs)]
    if selected_cuisines:
        filtered = filtered[
            filtered["CUISINE DESCRIPTION"].isin(selected_cuisines)
        ]
    if filtered.empty:
        return px.line(title="No data available for the selected filters.")
    # Averages:
    if chart_view == "average":
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
            title="Average Inspection Score Over Time by Cuisine"
        )
        fig.update_layout(
            xaxis_title="Inspection Month",
            yaxis_title="Average Inspection Score",
            legend_title="Cuisine"
        )
    # Indivudual
    else:
        summary = (
            filtered.sort_values("INSPECTION DATE")
            .groupby("CAMIS")
            .agg(
                restaurant_label=("restaurant_label", "first"),
                first_score=("SCORE", "first"),
                last_score=("SCORE", "last"),
                num_inspections=("SCORE", "count")
            )
            .reset_index()
        )
        summary["score_change"] = (
            summary["last_score"] - summary["first_score"]
        )
        top_ids = (
            summary.sort_values("score_change", ascending=False)
            .head(10)["CAMIS"]
        )
        plot_df = filtered[filtered["CAMIS"].isin(top_ids)]
        fig = px.line(
            plot_df,
            x="INSPECTION DATE",
            y="SCORE",
            color="restaurant_label",
            markers=True,
            hover_data=[
                "DBA",
                "BORO",
                "CUISINE DESCRIPTION",
                "GRADE"
            ],
            title="Individual Restaurant Inspection Score Trends"
        )
        fig.update_layout(
            xaxis_title="Inspection Date",
            yaxis_title="Inspection Score",
            legend_title="Restaurant"
        )
    # A Grade Line
    fig.add_hline(
        y=13,
        line_dash="dash",
        annotation_text="A-grade Maximum Score: 13"
    )
    fig.update_layout(
        template="simple_white",
        height=650
    )
    return fig
if __name__ == "__main__":
    app.run(debug=True)