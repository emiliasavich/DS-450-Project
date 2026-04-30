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

severity_colors = {
    "Critical": "#d62728",
    "Non-Critical": "#1f77b4"
}

df = df[df["severity"] != "Not Applicable"]

cuisine_categories = {
    "North American": [
        "American", "Tex-Mex", "New American", "Southwestern",
        "Californian","Cajun", "Creole/Cajun",
        "Soul Food","Creole",
    ],
    "Latin American & Carribean":[
        "Latin American","Peruvian","Brazilian",
        "Chilean","Mexican","Carribean","Chimichurri",
    ],
    "European":[
        "Scandinavian","German", "Polish", "New French","English",
        "Italian","French", "Irish", "Eastern European","Russian","Czech",
        "Basque","Portuguese","Spanish"
    ],
    "Asian & Pacific Islander": [
        "Chinese", "Japanese", "Asian/Asian Fusion", "Korean", "Thai", "Indian", 
        "Bangladeshi", "Southeast Asian", "Filipino", "Pakistani", "Chinese/Japanese", 
        "Hawaiian", "Australian", "Indonesian", "Polynesian"
    ],
    "Fast Casual & Deli": [
        "Pizza", "Chicken", "Sandwiches", "Hamburgers", "Bagels/Pretzels", "Seafood", 
        "Sandwiches/Salads/Mixed Buffet", "Salads", "Hotdogs/Pretzels", "Hotdogs", 
        "Soups/Salads/Sandwiches", "Soups"
    ],
    "Sweets, Snacks & Beverages": [
        "Coffee/Tea", "Bakery Products/Desserts", "Juice, Smoothies, Fruit Salads", 
        "Donuts", "Frozen Desserts", "Bottled Beverages", "Pancakes/Waffles", 
        "Fruits/Vegetables", "Nuts/Confectionary"
    ],
    "Middle Eastern, African & Mediterranean": [
        "Mediterranean", "Middle Eastern", "Greek", "African", "Turkish", "Ethiopian", 
        "Egyptian", "Afghan", "Moroccan", "Armenian", "Lebanese", "Iranian"
    ],
    "Specialty & Dietary": [
        "Jewish/Kosher", "Vegan", "Vegetarian"
    ],
    "Dining Styles & Concept":[
        "Continental", "Fusion","Haute Cuisine","Tapas",
        "Chinese/Cuban","Other","Steakhouse", "Barbecue"
    ]
}

cuisine_to_region = {
    cuisine: region
    for region, cuisines in cuisine_categories.items()
    for cuisine in cuisines
}

df["REGION"] = df["CUISINE DESCRIPTION"].map(cuisine_to_region)


grouped_df = (
    df.groupby(["REGION", "severity"])
      .size()
      .reset_index(name="count")
)

severity_order = ["Critical", "Non-Critical"]
grouped_df["severity"] = pd.Categorical(
    grouped_df["severity"],
    categories=severity_order,
    ordered=True
)

app = dash.Dash(__name__)

regions = sorted(grouped_df["REGION"].unique())

app.layout = html.Div([
    html.H2("NYC Restaurant Violations by Cuisine Group & Severity"),
    dcc.Dropdown(
        id="cuisine-select",
        options=[{"label": r, "value": r} for r in regions],
        value=regions,
        multi=True
    ),
    dcc.RadioItems(
        id="sort-order",
        options=[
            {"label": "Low → High", "value": "asc"},
            {"label": "High → Low", "value": "desc"}
        ],
        value="desc",
        inline=True
    ),
    html.Div([
    html.Button("Show Individual Cuisines", id="split-button", n_clicks=0, style={"display": "none"}),
    html.Button("Back", id="back-button", n_clicks=0, style={"display": "none"})
    ], id="button-container"),
    dcc.Store(id="mode", data={"mode": "stacked", "region": None}),
    dcc.Graph(id="violation-chart"),
])

@app.callback(
    Output("violation-chart", "figure"),
    Output("mode", "data"),
    Output("split-button", "style"),
    Output("back-button", "style"),
    Input("cuisine-select", "value"),
    Input("sort-order", "value"),
    Input("violation-chart", "clickData"),
    Input("split-button", "n_clicks"),
    Input("back-button", "n_clicks"),
    State("mode", "data")
)
def update_chart(selected_regions, sort_order, clickData, split_clicks, back_clicks, mode):

    filtered = grouped_df[grouped_df["REGION"].isin(selected_regions)].copy()

    totals = (
        filtered.groupby("REGION")["count"]
        .sum()
        .sort_values(ascending=(sort_order == "asc"))
    )

    filtered["REGION"] = pd.Categorical(
        filtered["REGION"],
        categories=totals.index,
        ordered=True
    )
    filtered = filtered.sort_values("REGION")


    if back_clicks > 0:
        fig = px.bar(
            filtered,
            x="REGION",
            y="count",
            color="severity",
            color_discrete_map=severity_colors,
            barmode="stack",
            title="Violations by Cuisine Group",
            height=650
        )
        fig.update_traces(texttemplate='%{y}', textposition='inside')
        fig.update_layout(
            xaxis_title="Region",
            yaxis_title="Number of Violations"
        )
        return fig, {"mode": "stacked", "region": None}, {"display": "none"}, {"display": "none"}

    if mode["mode"] == "drilldown" and split_clicks > 0:
        region = mode["region"]

        sub = df[df["REGION"] == region]

        cuisine_grouped = (
            sub.groupby(["CUISINE DESCRIPTION", "severity"])
            .size()
            .reset_index(name="count")
        )

        cuisine_totals = (
            cuisine_grouped.groupby("CUISINE DESCRIPTION")["count"]
            .sum()
            .sort_values(ascending=False)
        )

        cuisine_grouped["CUISINE DESCRIPTION"] = pd.Categorical(
            cuisine_grouped["CUISINE DESCRIPTION"],
            categories=cuisine_totals.index,
            ordered=True
        )

        cuisine_grouped = cuisine_grouped.sort_values("CUISINE DESCRIPTION")

        fig = px.bar(
            cuisine_grouped,
            x="CUISINE DESCRIPTION",
            y="count",
            color="severity",
            color_discrete_map=severity_colors,
            barmode="stack",
            title=f"{region}: Violations by Individual Cuisine",
            height=700
        )

        fig.update_layout(xaxis_tickangle=-45)

        return fig, {"mode": "split", "region": region}, {"display": "none"}, {"display": "inline-block"}


    if clickData is not None and mode["mode"] == "stacked":
        clicked_region = clickData["points"][0]["x"]

        sub = filtered[filtered["REGION"] == clicked_region]

        cuisines = cuisine_categories.get(clicked_region, [])
        cuisine_list_str = ", ".join(cuisines)

        fig = px.bar(
            sub,
            x="severity",
            y="count",
            color="severity",
            color_discrete_map=severity_colors,
            barmode="group",
            title=f"Violation Breakdown for {clicked_region}<br><sup>Cuisines: {cuisine_list_str}</sup>",
            height=650
        )
        fig.update_traces(texttemplate='%{y}', textposition='inside')
        fig.update_layout(
            xaxis_title="Severity",
            yaxis_title="Number of Violations"
        )
        return fig, {"mode": "drilldown", "region": clicked_region}, {"display": "inline-block"}, {"display": "inline-block"}

    fig = px.bar(
        filtered,
        x="REGION",
        y="count",
        color="severity",
        color_discrete_map=severity_colors,
        barmode="stack",
        title="Violations by Cuisine Group",
        height=650
    )
    fig.update_traces(texttemplate='%{y}', textposition='inside')
    fig.update_layout(
            xaxis_title="Region",
            yaxis_title="Number of Violations"
        )
    return fig, {"mode": "stacked", "region": None}, {"display": "none"}, {"display": "none"}


if __name__ == "__main__":
    app.run(debug=True)
