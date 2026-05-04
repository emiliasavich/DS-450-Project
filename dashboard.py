from dash import Dash, dcc, html, Input, Output, State, ctx, ALL
import plotly.express as px
import pandas as pd

from emilia.emilia_App import get_emilia_visualization
from jose.jose_App import get_jose_visualization
from nimra.nimra_App import get_nimra_visualization
from sebastian.sebastian_App import get_sebastian_visualization


def get_dashboard(app, df):

    to_return = html.Div([
        html.Div(
            id="upper-row",
            className="flex-container",
            children=[
                get_nimra_visualization(app, df),
                get_jose_visualization(app, df)
            ]
        ),
        html.Div(
            id="bottom-row",
            className="flex-container",
            children=[
                get_emilia_visualization(app, df),
                get_sebastian_visualization(app, df)
            ]
        )
    ])

    return to_return
