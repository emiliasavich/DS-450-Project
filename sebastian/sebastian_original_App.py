import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd

# Most of this I just ripped from my ipynb, explanation for everything is there
# Read the dataframe
df = pd.read_csv("DOHMH_New_York_City_Restaurant_Inspection_Results_20260430.csv")

# Filter out columns I want. Don't really need 'CAMIS' though but just to be sure
df_filtered = df[['CAMIS', 'INSPECTION DATE', 'ACTION']].copy() # Copy because it complains if you don't
df_filtered['INSPECTION DATE'] = pd.to_datetime(df_filtered['INSPECTION DATE'])
df_filtered['INSPECTION YEAR'] = df_filtered['INSPECTION DATE'].dt.year

# Drop all null values for the ACTION column, assuming no action basically
df_filtered.dropna(subset=['ACTION'], inplace=True)

# Map string to an integer category, just remember to convert those in the dash application
mapping = {
    "Establishment Closed by DOHMH. Violations were cited in the following area(s) and those requiring immediate action were addressed.": 0,
    "Establishment re-closed by DOHMH.": 1,
    "Establishment re-opened by DOHMH.": 2,
    "Violations were cited in the following area(s).": 3,
    "No violations were recorded at the time of this inspection.": 3
}
df_filtered['ACTION CLASS'] = df_filtered['ACTION'].map(mapping)

# Create the table mapping inspection year to each type of action we are focusing on
table = (
    df_filtered
    .groupby(['INSPECTION YEAR', 'ACTION CLASS'])
    .size()
    .unstack(fill_value=0)
)

# Build the table for plotting
table_plot = table.drop(columns=3, errors='ignore').reset_index()
table_plot = table_plot.rename(columns={
    0: 'Closed',
    1: 'Re-closed',
    2: 'Re-opened'
})

# Convert to long format
table_long = table_plot.melt(
    id_vars='INSPECTION YEAR',
    var_name='Action',
    value_name='Count'
)

# ---------------------------------------------------
# DASH APPLICATION SEGMENT STARTS HERE
# ---------------------------------------------------
app = dash.Dash(__name__)

fig = px.bar(
    table_long,
    x='INSPECTION YEAR',
    y='Count',
    color='Action',
    title='Inspection Actions by Year',
    labels={
        'INSPECTION YEAR': 'Year',
        'Count': 'Number of Inspections',
        'Action': 'Action Type'
    }
)
app.layout = html.Div([
    html.H1("NYC Restaurant Inspection Actions"),
    dcc.Graph(id='stacked-bar', figure=fig)
])

if __name__ == '__main__':
    app.run(debug=True)
