import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Output, Input, callback, ctx, ALL

app = Dash(__name__)

df = pd.read_csv("data/nyc_restaurants.csv")

# Preprocess
df["INSPECTION DATE"] = pd.to_datetime(df["INSPECTION DATE"], errors="coerce")
df = df[df["BORO"] != "0"]

grades = ["C", "B", "A"]
colors = {"C": "red", "B": "orange", "A": "green"}

# Keep only the most recent inspection per restaurant
graded = df[df['GRADE'].notna() & df['GRADE'].isin(grades)]
most_recent = (
    graded.sort_values('INSPECTION DATE')
          .drop_duplicates(subset='CAMIS', keep='last')
)

# Get dataframe where row is boro, grade, and number of restaurants
grouped = most_recent.groupby(["BORO", "GRADE"]).size().reset_index(name="Count")
total_by_boro = most_recent.groupby("BORO").size()
grouped["Total By Boro"] = grouped["BORO"].map(total_by_boro)
grouped["Percent By Grade"] = grouped["Count"] / grouped["Total By Boro"] * 100

# Get a fig_bar object
def get_fig_bar(curr_grade):
    filtered_df = grouped[grouped['GRADE'] == curr_grade]
    filtered_df = filtered_df.sort_values("Percent By Grade", ascending=False)
    new_fig_bar = px.bar(
        x=filtered_df["BORO"],
        y=filtered_df["Percent By Grade"].round(2),
        template="simple_white",
        title=f"Percent of Restaurants with <span style='color:{colors[curr_grade]}'>Grade {curr_grade}</span> by Borough",
        labels={"x": "Boro", "y": f"Percent with Grade {curr_grade}"}, 
    )
    new_fig_bar.update_traces(marker_color=colors[curr_grade])
    new_fig_bar.update_layout(title_x=0.5)
    return new_fig_bar

# Make visualization
curr_grade = "C"
original_fig_bar = get_fig_bar(curr_grade)

app.layout = html.Div(
    id="overall-container",
    children=[
        dcc.Graph(id='bar-comp', figure=original_fig_bar),
        html.Button('Grade A', id={'type': 'grade-btn', 'index': 'A'}, n_clicks=0),
        html.Button('Grade B', id={'type': 'grade-btn', 'index': 'B'}, n_clicks=0),
        html.Button('Grade C', id={'type': 'grade-btn', 'index': 'C'}, n_clicks=0),
    ]
)

# Update based on button clicks
@callback(
    Output('bar-comp', 'figure'),
    Input({'type': 'grade-btn', 'index': ALL}, 'n_clicks'),
)
def show_clicked(n_clicks_list):
    if not ctx.triggered_id:
        return original_fig_bar  # nothing clicked yet
    curr_grade = ctx.triggered_id['index'] 
    fig_bar = get_fig_bar(curr_grade)
    return fig_bar

if __name__ == '__main__':
    app.run(debug=True)
