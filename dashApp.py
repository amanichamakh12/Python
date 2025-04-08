from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import requests
from dash.exceptions import PreventUpdate

# Récupération des données depuis l'API
try:
    url = "http://localhost:8000/AllAnnonces"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data.get('data', []))
except Exception as e:
    print(f"Erreur lors de la récupération des données: {str(e)}")
    df = pd.DataFrame()

# Vérification et nettoyage des données
if not df.empty:
    df['Prix'] = df['Prix'].replace(r'[^\d.]', '', regex=True)
    df['Prix'] = pd.to_numeric(df['Prix'], errors='coerce').fillna(0)
    df = df.dropna(subset=['Type de bien', 'Localisation', 'Prix'])

# Création de l'application
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    html.H1("Tableau de bord des annonces immobilières", 
            style={'textAlign': 'center', 'marginBottom': '30px'}),
    
    dbc.Row([
        dbc.Col([
            html.Label("Type de transaction:"),
            dcc.Dropdown(
                id='type-filter',
                options=[{'label': typ, 'value': typ} for typ in df['Type de bien'].unique()] if not df.empty else [],
                multi=True,
                placeholder="Tous types"
            )
        ], width=4),
        
        dbc.Col([
            html.Label("Localisation:"),
            dcc.Dropdown(
                id='location-filter',
                options=[{'label': loc, 'value': loc} for loc in df['Localisation'].unique()] if not df.empty else [],
                multi=True,
                placeholder="Toutes villes"
            )
        ], width=4),
        
        dbc.Col([
            html.Label("Fourchette de prix (DT):"),
            dcc.RangeSlider(
                id='price-slider',
                min=int(df['Prix'].min()) if not df.empty else 0,
                max=int(df['Prix'].max()) if not df.empty else 1000000,
                value=[int(df['Prix'].min()) if not df.empty else 0, 
                      int(df['Prix'].max()) if not df.empty else 1000000],
                marks={i: f"{i//1000}k" for i in range(
                    0, 
                    (int(df['Prix'].max()) if not df.empty else 1000000)+1, 
                    100000)},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], width=4)
    ], style={'marginBottom': '20px'}),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='price-distribution'), width=6),
        dbc.Col(dcc.Graph(id='type-distribution'), width=6)
    ]),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='ville-distribution'), width=6),
        dbc.Col(dcc.Graph(id='price-boxplot'), width=6)
    ])
])

@app.callback(
    [Output('price-distribution', 'figure'),
     Output('type-distribution', 'figure'),
     Output('ville-distribution', 'figure'),
     Output('price-boxplot', 'figure')],
    [Input('price-slider', 'value'),
     Input('type-filter', 'value'),
     Input('location-filter', 'value')]
)
def update_graphs(price_range, selected_types, selected_locations):
    if df.empty:
        empty_fig = px.scatter(title="Aucune donnée disponible")
        return empty_fig, empty_fig, empty_fig, empty_fig
    
    try:
        filtered_df = df.copy()
        
        # Filtrage par prix
        filtered_df = filtered_df[
            (filtered_df['Prix'] >= price_range[0]) & 
            (filtered_df['Prix'] <= price_range[1])
        ]
        
        # Filtrage par type
        if selected_types:
            filtered_df = filtered_df[filtered_df['Type de bien'].isin(
                [selected_types] if isinstance(selected_types, str) else selected_types
            )]
        
        # Filtrage par localisation
        if selected_locations:
            filtered_df = filtered_df[filtered_df['Localisation'].isin(
                [selected_locations] if isinstance(selected_locations, str) else selected_locations
            )]
        
        # Vérification si le DataFrame filtré est vide
        if filtered_df.empty:
            empty_fig = px.scatter(title="Aucune donnée correspondante")
            return empty_fig, empty_fig, empty_fig, empty_fig
        
        # Création des graphiques
        price_hist = px.histogram(
            filtered_df,
            x='Prix',
            nbins=15,
            color='Type de bien',
            title="Distribution des prix",
            labels={'Prix': 'Prix (DT)'},
            hover_data=['Localisation']
        )
        
        type_pie = px.pie(
            filtered_df,
            names='Type de bien',
            title="Répartition par type de bien",
            hole=0.3
        ) if not filtered_df.empty else px.scatter(title="Aucune donnée")
        
        ville_bar = px.bar(
        filtered_df['Localisation'].value_counts().reset_index(),
        x='Localisation',  # J'ai changé 'index' par 'Localisation'
        y='count',  # La colonne count est automatiquement créée par value_counts()
        title="Nombre d'annonces par ville",
        labels={'Localisation': 'Ville', 'count': 'Nombre d\'annonces'}
    ) if not filtered_df.empty else px.scatter(title="Aucune donnée")   
        
        price_box = px.box(
            filtered_df,
            x='Type de bien',
            y='Prix',
            title="Distribution des prix par type",
            color='Type de bien'
        ) if not filtered_df.empty else px.scatter(title="Aucune donnée")
        
        return price_hist, type_pie, ville_bar, price_box
    
    except Exception as e:
        print(f"Erreur dans le callback: {str(e)}")
        error_fig = px.scatter(title=f"Erreur: {str(e)}")
        return error_fig, error_fig, error_fig, error_fig

if __name__ == '__main__':
    app.run(debug=True, port=8060)