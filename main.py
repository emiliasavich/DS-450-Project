from dash import Dash, dcc, html, Input, Output, State, ctx, ALL
import plotly.express as px
import pandas as pd

from emilia.emilia_App import get_emilia_visualization
from jose.jose_App import get_jose_visualization
from nimra.nimra_App import get_nimra_visualization
from sebastian.sebastian_App import get_sebastian_visualization

# Preprocess
# df = pd.read_csv("data/nyc_restaurants.csv")
df = pd.read_csv("https://github.com/emiliasavich/DS-450-Project/releases/download/data-v1/nyc_restaurants.csv")
df["INSPECTION DATE"] = pd.to_datetime(df["INSPECTION DATE"], errors="coerce")
df = df[df["BORO"] != "0"]

df = df.dropna(subset=["CUISINE DESCRIPTION"])
df = df[df["CUISINE DESCRIPTION"].str.strip() != ""]
TOP_10_CUISINES = list(df["CUISINE DESCRIPTION"].value_counts().head(10).index)

BOROUGHS = sorted(df["BORO"].dropna().unique())

app = Dash(__name__)
# server = app.server 

# Pre-render visualizations
nimra_viz = get_nimra_visualization(app, df)
jose_viz = get_jose_visualization(app, df)
emilia_viz = get_emilia_visualization(app, df)
sebastian_viz = get_sebastian_visualization(app, df)

nimra_p = 'Restaurants serving American cuisine have the most violations.'
jose_p = 'Most cuisines have trended to have worse inspection scores.'
emilia_p = 'Queens has the greatest proportion of restaurants with grade C or B. Manhattan has the greatest proportion of grade A.'
sebastian_p = 'The number of closed restaurants has increased, while the number of re-opened and re-closed has stayed around constant.'

show_viz = {"display": "block"}
show_half_viz = {"display": "block", "width":"50%"}
hide_viz = {"display": "none"}

app.layout = html.Div(
        id="outermost-container",
        children=[
            html.Div(
                id="dashboard-title",
                children=[
                    html.H1("Analyzing NYC Restaurant Inspection Results for 10 Most Common Cuisines")
                ]
            ),
            html.Div(
                id="cuisine-filter-row",
                style={
                    "padding": "12px 25px",
                    "fontFamily": "Times New Roman",
                    "borderBottom": "1px solid #ddd",
                },
                children=[
                    html.Div(
                        className="flex-container",
                        children=[
                            html.Label(
                                "Filter by Cuisine:",
                                style={"fontWeight": "bold", "marginRight": "10px", "whiteSpace": "nowrap"}
                            ),
                            dcc.Checklist(
                                id="global-cuisine-filter",
                                options=[{"label": c, "value": c} for c in TOP_10_CUISINES],
                                value=TOP_10_CUISINES,
                                inline=True,
                                labelStyle={"marginRight": "14px", "cursor": "pointer"}
                            )
                    ]),
                    html.Div(
                        className="flex-container",
                        children=[
                            html.Label(
                                "Filter by Borough:",
                                style={"fontWeight": "bold", "marginRight": "10px", "whiteSpace": "nowrap"}
                            ),
                            dcc.Checklist(
                                id="global-borough-filter",
                                options=[{"label": b, "value": b} for b in BOROUGHS],
                                value=BOROUGHS,
                                inline=True,
                                labelStyle={"marginRight": "14px", "cursor": "pointer"}
                            )
                    ])
                ]
            ),
            dcc.Store(id='active-state', data='1'),
            html.Div(
                id='storyboard-buttons',
                children=[
                    html.Button('Story 1', id={'type': 'story-btn', 'index': '1'}, n_clicks=0, className="active"),
                    html.Button('Story 2', id={'type': 'story-btn', 'index': '2'}, n_clicks=0),
                    html.Button('Story 3', id={'type': 'story-btn', 'index': '3'}, n_clicks=0),
                    html.Button('Story 4', id={'type': 'story-btn', 'index': '4'}, n_clicks=0),
                    html.Button('Dashboard', id={'type': 'story-btn', 'index': '5'}, n_clicks=0),
                ]
            ),
            html.P(
                id='story-description',
                children=nimra_p,
                style={'text-align': 'center', 'font-size': '1.2rem'}
            ),
            html.Div(
                id='storyboard-figure',
                children=[
                    html.Div(id='nimra-viz', children=[nimra_viz], style=show_viz),
                    html.Div(id='jose-viz', children=[jose_viz], style=hide_viz),
                    html.Div(id='emilia-viz', children=[emilia_viz], style=hide_viz),
                    html.Div(id='sebastian-viz', children=[sebastian_viz], style=hide_viz),
                ]
            )
        ])

@app.callback(
    [Output('nimra-viz', 'style'),
     Output('jose-viz', 'style'),
     Output('emilia-viz', 'style'),
     Output('sebastian-viz', 'style'),
     Output('storyboard-figure', 'style'),
     Output({'type': 'story-btn', 'index': ALL}, 'className'),
     Output('story-description', 'children')],
    Input({'type': 'story-btn', 'index': ALL}, 'n_clicks'),
    State('active-state','data')
)
def show_clicked(story_btns, active_state):
    if ctx.triggered_id and isinstance(ctx.triggered_id, dict):
        switch_var = ctx.triggered_id['index']
    else:
        return show_viz, hide_viz, hide_viz, hide_viz, {}, ['active', '', '', '', ''], nimra_p

    match switch_var:
        case '1':
            return show_viz, hide_viz, hide_viz, hide_viz, {}, ['active', '', '', '', ''], nimra_p
        case '2':
            return hide_viz, show_viz, hide_viz, hide_viz, {}, ['', 'active', '', '', ''], jose_p
        case '3':
            return hide_viz, hide_viz, show_viz, hide_viz, {}, ['', '', 'active', '', ''], emilia_p
        case '4':
            return hide_viz, hide_viz, hide_viz, show_viz, {}, ['', '', '', 'active', ''], sebastian_p
        case '5':
            return show_half_viz, show_half_viz, show_half_viz, show_half_viz, {"display": "flex", "flexWrap": "wrap"}, ['', '', '', '', 'active'], ''

if __name__ == "__main__":
    app.run(debug=True)
