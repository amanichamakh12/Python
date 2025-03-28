import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
import requests


url = "http://localhost:8000/AllAnnonces"
response = requests.get(url)
data = response.json()

df = pd.DataFrame(data)
fig = px.bar(df, x='Localisation', y='Prix', title="Répartition des prix par localisation")

app = dash.Dash(__name__)

# Layout de l'application
app.layout = html.Div([
    html.H1("Répartition des prix des biens", style={'textAlign': 'center'}),
    dcc.Graph(
        id='bar-chart',
        figure=px.bar(df, x='Localisation', y='Prix', title="Répartition des prix")
    )
])

# Lancer l'application
if __name__ == '__main__':
    app.run(debug=True)
