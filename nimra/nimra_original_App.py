import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd

df = pd.read_csv("DOHMH_New_York_City_Restaurant_Inspection_Results_20260420.csv")

df = df.dropna(subset=["CUISINE DESCRIPTION"])
df = df[df["CUISINE DESCRIPTION"].str.strip() != ""]
df = df[df["ACTION"] != "No violations"]

df["CRITICAL FLAG"] = df["CRITICAL FLAG"].astype(str).str.strip()

df["severity"] = df["CRITICAL FLAG"].replace({
    "Critical": "Critical",
    "Not Critical": "Non-Critical",
    "Not Applicable": "Not Applicable"
})

df = df[df["severity"] != "Not Applicable"]

severity_colors = {
    "Critical": "#d62728",
    "Non-Critical": "#1f77b4"
}

cuisine_totals = (
    df.groupby("CUISINE DESCRIPTION")["severity"]
      .count()
      .sort_values(ascending=False)
      .head(10)
)

top10_cuisines = cuisine_totals.index.tolist()
filtered_df = df[df["CUISINE DESCRIPTION"].isin(top10_cuisines)]

grouped_df = (
    filtered_df.groupby(["CUISINE DESCRIPTION", "severity"])
               .size()
               .reset_index(name="count")
)

grouped_df["CUISINE DESCRIPTION"] = pd.Categorical(
    grouped_df["CUISINE DESCRIPTION"],
    categories=cuisine_totals.index,
    ordered=True
)

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H2("NYC Restaurant Violations for Top 10 Cuisines"),
    dcc.RadioItems(
        id="sort-order",
        options=[
            {"label": "High → Low", "value": "desc"},
            {"label": "Low → High", "value": "asc"}
        ],
        value="desc",
        inline=True
    ),
    dcc.Graph(id="violation-chart")
])

@app.callback(
    Output("violation-chart", "figure"),
    Output("violation-chart", "clickData"),
    Input("sort-order", "value"),
    Input("violation-chart", "clickData")
)
def update_chart(sort_order, clickData):

    totals_sorted = cuisine_totals.sort_values(
        ascending=(sort_order == "asc")
    )

    clicked_cuisine = None
    if clickData and "points" in clickData:
        clicked_cuisine = clickData["points"][0]["x"]

    if clicked_cuisine in top10_cuisines:
        temp = grouped_df[grouped_df["CUISINE DESCRIPTION"] == clicked_cuisine]

        fig = px.bar(
            temp,
            x="severity",
            y="count",
            color="severity",
            color_discrete_map=severity_colors,
            barmode="group",
            title=f"{clicked_cuisine}: Critical vs Non‑Critical",
            height=650
        )

        fig.update_traces(texttemplate='%{y}', textposition='inside')
        fig.update_layout(
            xaxis_title="Severity",
            yaxis_title="Number of Violations",
        )
        return fig, clickData

    temp = grouped_df.copy()
    temp["CUISINE DESCRIPTION"] = pd.Categorical(
        temp["CUISINE DESCRIPTION"],
        categories=totals_sorted.index,
        ordered=True
    )
    temp = temp.sort_values("CUISINE DESCRIPTION")

    fig = px.bar(
        temp,
        x="CUISINE DESCRIPTION",
        y="count",
        color="severity",
        color_discrete_map=severity_colors,
        barmode="stack",
        title="Top 10 Cuisines by Violations",
        height=650
    )
    fig.update_traces(texttemplate='%{y}', textposition='inside')
    fig.update_layout(
        xaxis_title="Cuisine",
        yaxis_title="Number of Violations",
    )
    return fig, None

if __name__ == "__main__":
    app.run(debug=True)
