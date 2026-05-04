import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd

def get_nimra_visualization(app, df):
    df = df.copy()

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

    top_10_cuisines = df["CUISINE DESCRIPTION"].value_counts().head(10).index
    df = df[df["CUISINE DESCRIPTION"].isin(top_10_cuisines)]
    df["REGION"] = df["CUISINE DESCRIPTION"]


    grouped_df = (
        df.groupby(["REGION", "severity", "BORO"])
        .size()
        .reset_index(name="count")
    )

    severity_order = ["Critical", "Non-Critical"]
    grouped_df["severity"] = pd.Categorical(
        grouped_df["severity"],
        categories=severity_order,
        ordered=True
    )

    to_return = html.Div(
        style={"flex": "1", "minWidth": "0"},
        children=[
        html.Div([
        html.Button("Show Individual Cuisines", id="nimra-split-button", n_clicks=0, style={"display": "none"}),
        html.Button("Back", id="nimra-back-button", n_clicks=0, style={"display": "none"})
        ], id="nimra-button-container"),
        dcc.Store(id="nimra-mode", data={"mode": "stacked", "region": None}),
        dcc.Graph(id="nimra-violation-chart"),
    ])

    @app.callback(
        [Output("nimra-violation-chart", "figure"),
        Output("nimra-mode", "data"),
        Output("nimra-split-button", "style"),
        Output("nimra-back-button", "style")],
        [Input("global-cuisine-filter", "value"),
        Input("global-borough-filter", "value"),
        Input("nimra-violation-chart", "clickData"),
        Input("nimra-split-button", "n_clicks"),
        Input("nimra-back-button", "n_clicks")],
        State("nimra-mode", "data")
    )
    def update_chart(selected_cuisines, selected_boroughs, clickData, split_clicks, back_clicks, mode):
        selected_regions = selected_cuisines# if selected_cuisines else list(grouped_df["REGION"].unique())
        filtered = grouped_df[grouped_df["REGION"].isin(selected_regions)].copy()
        filtered = filtered[filtered['BORO'].isin(selected_boroughs)]

        filtered = (
            filtered.groupby(["REGION", "severity"])["count"]
            .sum()
            .reset_index()
        )

        totals = (
            filtered.groupby("REGION")["count"]
            .sum()
            # .sort_values(ascending=(sort_order == "asc"))
            .sort_values(ascending=False)
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
                template="simple_white",
                barmode="stack",
                title="Violations by Cuisine Group",
                # height=650
            )
            fig.update_traces(texttemplate='%{y}', textposition='inside')
            fig.update_layout(
                xaxis_title="Region",
                yaxis_title="Number of Violations",
                template="simple_white",
                legend=dict(
                    x=1,
                    y=1,
                    xanchor="right",
                    yanchor="top"
                )
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
                template="simple_white",
                barmode="stack",
                title=f"{region}: Violations by Individual Cuisine",
                # height=700
            )

            fig.update_layout(
                xaxis_tickangle=-45, 
                template="simple_white",
                legend=dict(
                    x=1,
                    y=1,
                    xanchor="right",
                    yanchor="top"
                )
            )

            return fig, {"mode": "split", "region": region}, {"display": "none"}, {"display": "inline-block"}


        if clickData is not None and mode["mode"] == "stacked":
            clicked_region = clickData["points"][0]["x"]

            sub = filtered[filtered["REGION"] == clicked_region]

            fig = px.bar(
                sub,
                x="severity",
                y="count",
                color="severity",
                color_discrete_map=severity_colors,
                template="simple_white",
                barmode="group",
                title=f"Violation Breakdown for {clicked_region}",
                # height=650
            )
            fig.update_traces(texttemplate='%{y}', textposition='inside')
            fig.update_layout(
                xaxis_title="Severity",
                yaxis_title="Number of Violations",
                template="simple_white",
                legend=dict(
                    x=1,
                    y=1,
                    xanchor="right",
                    yanchor="top"
                )
            )
            return fig, {"mode": "drilldown", "region": clicked_region}, {"display": "inline-block"}, {"display": "inline-block"}

        fig = px.bar(
            filtered,
            x="REGION",
            y="count",
            color="severity",
            color_discrete_map=severity_colors,
            template="simple_white",
            barmode="stack",
            title="Violations by Cuisine Group",
            # height=650
        )
        fig.update_traces(texttemplate='%{y}', textposition='inside')
        fig.update_layout(
                xaxis_title="Region",
                yaxis_title="Number of Violations",
                template="simple_white",
                legend=dict(
                    x=1,
                    y=1,
                    xanchor="right",
                    yanchor="top"
                )
            )
        return fig, {"mode": "stacked", "region": None}, {"display": "none"}, {"display": "none"}
    
    return to_return
