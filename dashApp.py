from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import requests

# Récupération des données depuis l'API
url = "http://localhost:8000/AllAnnonces"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    df = pd.DataFrame(data['data'])  # Assurez-vous que les données sont dans 'data'
else:
    print("Erreur lors de la récupération des données.")
    df = pd.DataFrame()

# Vérification des données
print(df.head())

# Nettoyer la colonne 'Prix' (enlever tout sauf les chiffres et points décimaux)
df['Prix'] = df['Prix'].replace(r'[^\d.]', '', regex=True)
df['Prix'] = pd.to_numeric(df['Prix'], errors='coerce')  # Convertir en float, avec NaN si erreur

# Calcul du prix moyen
prix_moyen = df['Prix'].mean() if not df['Prix'].isnull().all() else 0
prix_moyen_str = f"Prix moyen des biens : {prix_moyen:.2f} TND"

# Comptage des biens par localisation et type
biens_par_ville = df['Localisation'].value_counts()
biens_par_Type = df['Type de bien'].value_counts()

# Création des graphiques
fig = px.box(df, x='Type de bien', y='Prix', title="Répartition des prix par type de bien")
fig_villes = px.bar(biens_par_ville, title="Répartition géographique des biens (par ville)")
fig_types = px.bar(biens_par_Type, title="Nombre de biens par type")

# Création de l'application Dash
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div(children=[
    html.H1("Tableau de bord des annonces immobilières", style={'textAlign': 'center'}),

    html.Div([
        html.Div([dcc.Graph(figure=fig)], style={'width': '48%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(figure=fig_villes)], style={'width': '48%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(figure=fig_types)], style={'width': '48%', 'display': 'inline-block'})
    ]),

    html.Div([  # Ajoutez des informations supplémentaires si nécessaire
        html.P(prix_moyen_str, style={'textAlign': 'center'})
    ])
])

if __name__ == '__main__':
    app.run(debug=True, port=8060)
