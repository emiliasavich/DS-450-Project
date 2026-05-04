import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Output, Input, State, callback, ctx, ALL

def get_emilia_visualization(app, df):
    df = df.copy()

    grades = ["C", "B", "A"]
    colors = {"C": "red", "B": "orange", "A": "green"}

    # Keep only the most recent inspection per restaurant
    graded = df[df['GRADE'].notna() & df['GRADE'].isin(grades)]
    most_recent = (
        graded.sort_values('INSPECTION DATE')
            .drop_duplicates(subset='CAMIS', keep='last')
    )

    # Get a fig_bar object
    def get_fig_bar(curr_grade, filtered_most_recent):
        # Done to fix bug with no data
        if filtered_most_recent.empty:
            new_fig = px.bar(
                template="simple_white",
                title=f"Percent of Restaurants with <span style='color:{colors[curr_grade]}'>Grade {curr_grade}</span> by Borough",
            )
            new_fig.update_layout(
                xaxis_title="Boro",
                yaxis_title=f"Percent with Grade {curr_grade}",
            )
            return new_fig
        
        grouped = filtered_most_recent.groupby(["BORO", "GRADE"]).size().reset_index(name="Count")
        total_by_boro = filtered_most_recent.groupby("BORO").size()
        grouped["Total By Boro"] = grouped["BORO"].map(total_by_boro)
        grouped["Percent By Grade"] = grouped["Count"] / grouped["Total By Boro"] * 100
        grade_rows = grouped[grouped['GRADE'] == curr_grade].sort_values("Percent By Grade", ascending=False)
        new_fig = px.bar(
            x=grade_rows["BORO"],
            y=grade_rows["Percent By Grade"].round(2),
            text=grade_rows["Percent By Grade"].round(2),
            template="simple_white",
            title=f"Percent of Restaurants with <span style='color:{colors[curr_grade]}'>Grade {curr_grade}</span> by Borough",
            labels={"x": "Boro", "y": f"Percent with Grade {curr_grade}"},
        )
        new_fig.update_traces(marker_color=colors[curr_grade])
        return new_fig

    to_return = html.Div(
        id="overall-container",
        style={"flex": "1", "minWidth": "0"},
        children=[
            dcc.Store(id="emilia-current-grade", data="C"),
            html.Div(
                style={"position": "relative"},
                children=[
                    dcc.Graph(id='bar-comp'),
                    html.Div(
                        style={
                            "position": "absolute",
                            "top": "50px",
                            "right": "85px",
                            "display": "flex",
                            "gap": "5px",
                            "zIndex": 10,
                        },
                        children=[
                            html.Button('Grade A', id={'type': 'grade-btn', 'index': 'A'}, n_clicks=0),
                            html.Button('Grade B', id={'type': 'grade-btn', 'index': 'B'}, n_clicks=0),
                            html.Button('Grade C', id={'type': 'grade-btn', 'index': 'C'}, n_clicks=0),
                        ],
                    ),
                ],
            ),
        ]
    )

    @callback(
        [Output('bar-comp', 'figure'),
        Output('emilia-current-grade', 'data')],
        [Input({'type': 'grade-btn', 'index': ALL}, 'n_clicks'),
        Input('global-cuisine-filter', 'value'),
        Input('global-borough-filter', 'value')],
        State('emilia-current-grade', 'data'),
    )
    def show_clicked(n_clicks_list, selected_cuisines, selected_boroughs, current_grade):
        filtered = most_recent[most_recent['CUISINE DESCRIPTION'].isin(selected_cuisines)]
        filtered = filtered[filtered['BORO'].isin(selected_boroughs)]

        if ctx.triggered_id and isinstance(ctx.triggered_id, dict):
            curr_grade = ctx.triggered_id['index']
        else:
            curr_grade = current_grade

        return get_fig_bar(curr_grade, filtered), curr_grade

    return to_return
