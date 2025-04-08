
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import requests
from dash.exceptions import PreventUpdate

# Récupération des données depuis l'API

try:
    url = "http://fastapi:8000/AllAnnonces"
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
    price_min = int(df['Prix'].min()) if not df.empty else 0
    price_max = int(df['Prix'].max()) if not df.empty else 1000000
    price_25 = int(df['Prix'].quantile(0.25)) if not df.empty else price_min
    price_75 = int(df['Prix'].quantile(0.75)) if not df.empty else price_max
    df = df[
    (df['Type de bien'].notna()) & 
    (~df['Type de bien'].isin(['N/A', 'NA', 'NaN', ''])) &
    (df['Type de bien'].str.strip() != '')
]
    df['Type de bien'] = df['Type de bien'].astype(str).str.strip()
    df = df[df['Type de bien'].str.match('^(À Vendre|À Louer)$')]
    df = df[df['Prix'] != ' ']
    df['Superficie'] = (
        df['Superficie']
        .astype(str)
        .str.replace(r'[^\d.]', '', regex=True)  # Garde uniquement les chiffres et points
        .replace(['na', 'n/a', 'N/A', ''], '0')  # Remplace les valeurs manquantes
    )
    
    # Étape 2: Conversion en float
    df['Superficie'] = pd.to_numeric(df['Superficie'], errors='coerce')
    
    # Étape 3: Remplacement des valeurs nulles et filtrage
    df['Superficie'] = df['Superficie'].fillna(0)
    df = df[df['Superficie'] > 0]  # Supprime les superficies nulles ou négatives
    
    # Étape 4: Conversion finale en entiers
    df['Superficie'] = df['Superficie'].round().astype(int)
    superficie_min = int(df['Superficie'].min()) if 'Superficie' in df.columns and not df.empty else 0
    superficie_max = int(df['Superficie'].max()) if 'Superficie' in df.columns and not df.empty else 500

    
    

    df = df.reset_index(drop=True)
    
   

# Création de l'application avec un thème plus moderne
app = Dash(__name__, external_stylesheets=[dbc.themes.LUX])

# ======================================================================
# STYLE PERSONNALISÉ
# ======================================================================
CARD_STYLE = {
    'borderRadius': '10px',
    'boxShadow': '0 4px 6px 0 rgba(0, 0, 0, 0.1)',
    'padding': '20px',
    'backgroundColor': 'white',
    'height': '100%'
}

KPI_STYLE = {
    'fontSize': '28px',
    'fontWeight': 'bold',
    'marginBottom': '5px'
}

DELTA_STYLE = {
    'fontSize': '14px',
    'color': '#2ca02c'  # Vert pour les valeurs positives
}

HEADER_STYLE = {
    'backgroundColor': '#f8f9fa',
    'padding': '2rem 1rem',
    'marginBottom': '2rem'
}

# ======================================================================
# LAYOUT DU DASHBOARD
# ======================================================================
app.layout = dbc.Container(fluid=True, children=[
    
    # En-tête
    dbc.Row(dbc.Col(html.Div([
        html.H1("Dashboard Immobilier", className="display-4"),
        html.P("Analyse des données immobilières en temps réel", className="lead")
    ], style=HEADER_STYLE), width=12)),
    
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
    html.H6("Prix Moyen", className="card-subtitle"),
    html.H3(
        f"{round(df['Prix'].mean(), 0):,.0f} DT" if not df.empty and 'Prix' in df.columns else "N/A",
        style=KPI_STYLE,
        id='kpi-prix-moyen'
    ),
    html.Span(id='kpi-prix-tendance', style=DELTA_STYLE)
        ])]) ),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("Superficie Moyenne", className="card-subtitle"),
               html.H3(f"{round(df['Superficie'].mean(), 0):,.0f}m²", style=KPI_STYLE),
            ])
        ], style=CARD_STYLE), width=3),
        
        dbc.Col(dbc.Card([
            
        dbc.CardBody([
            html.H6("Prix moyen au m² a vendre", className="card-subtitle"),
            html.H3(
                f"{round(df[df['Type de bien'] == 'À Vendre']['Prix'].sum() / df[df['Type de bien'] == 'À Vendre']['Superficie'].sum(), 2):,} DT/m²"
                if not df.empty else "N/A",
                style=KPI_STYLE,
                id='kpi-prix-m2'
            ),
            html.Span(id='kpi-tendance-prix-m2', style=DELTA_STYLE)
        ])
    ], style=CARD_STYLE), width=3),
    
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("Nombre d'annonces", className="card-subtitle"),
                html.H3(len(df), style=KPI_STYLE),
            ])
        ], style=CARD_STYLE), width=3)
    ], className="mb-4"),
    
    # Deuxième rangée : Graphiques principaux
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Distribution des prix", className="card-title"),
                dcc.Graph(
                    id="price-distribution",
                  figure=px.histogram(df, x='Prix', nbins=20, color_discrete_sequence=['#1f77b4'])
    if not df.empty and 'Prix' in df.columns else px.scatter(title="Aucune donnée disponible")
)
            ])
        ], style=CARD_STYLE), width=6),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Répartition par type", className="card-title"),
                dcc.Graph(
                id="type-distribution",
                figure=px.pie(df, names='Type de bien', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                if not df.empty and 'Type de bien' in df.columns else px.scatter(title="Aucune donnée disponible")
            )
            ])
        ], style=CARD_STYLE), width=6)
    ], className="mb-4"),
    
    # Troisième rangée : Graphiques secondaires
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Prix par localisation", className="card-title"),
                dcc.Graph(
                id="ville-distribution",
                figure=px.box(df, x='Localisation', y='Prix', color_discrete_sequence=['#ff7f0e'])
                if not df.empty and 'Localisation' in df.columns else px.scatter(title="Aucune donnée disponible")
            )
            ])
        ], style=CARD_STYLE), width=6),
        
    
    ]),

    
    # Filtres (optionnel - peut être placé dans une sidebar)
dbc.Row(
    dbc.Col(
        dbc.Card([
            dbc.CardBody([
                html.H5("Filtres", className="card-title"),
                dbc.Row([
                    dbc.Col([
                                html.Label("Type de bien:"),
                                dcc.Dropdown(
                                    id='type-filter',
                                    options=[{'label': typ, 'value': typ} for typ in df['Type de bien'].dropna().unique()],
                                    multi=True,
                                    placeholder="Tous types"
                                )
                            ], width=4),
                    dbc.Col([
                        html.Label("Localisation:"),
                    dcc.Dropdown(
                        id='location-filter',
                        options=[{'label': loc, 'value': loc} for loc in df['Localisation'].unique()],
                        multi=True,
                        placeholder="Toutes villes"
                    )
                    ], width=4),
                    
                    dbc.Col([
                        html.Label("Fourchette de prix:"),
                        dcc.RangeSlider(
                        id='price-slider',
                        min=df['Prix'].min() if 'Prix' in df.columns else 0,
                        max=df['Prix'].max() if 'Prix' in df.columns else 1000000,
                        value=[df['Prix'].quantile(0.25), df['Prix'].quantile(0.75)] if 'Prix' in df.columns else [0, 1000000],
                        marks={int(x): f"{x:,}" for x in [df['Prix'].min(), df['Prix'].median(), df['Prix'].max()]},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                    ], width=4)
                ])
            ])
        ], style={**CARD_STYLE, 'marginTop': '20px'}), 
        width=12
    )
)
])

@app.callback(
    [Output('price-distribution', 'figure'),
     Output('type-distribution', 'figure'),
     Output('ville-distribution', 'figure')],
    [Input('price-slider', 'value'),
     Input('type-filter', 'value'),
     Input('location-filter', 'value')]
)

def update_graphs(price_range, selected_types, selected_locations):
    if df.empty:
        empty_fig = px.scatter(title="Aucune donnée disponible")
        return empty_fig, empty_fig, empty_fig

    try:
        filtered_df = df.copy()

        filtered_df = filtered_df[
            (filtered_df['Prix'] >= price_range[0]) & 
            (filtered_df['Prix'] <= price_range[1])
        ]

        if selected_types:
            filtered_df = filtered_df[filtered_df['Type de bien'].isin(selected_types)]
        
        if selected_locations:
            filtered_df = filtered_df[filtered_df['Localisation'].isin(selected_locations)]

        if filtered_df.empty:
            empty_fig = px.scatter(title="Aucune donnée correspondante")
            return empty_fig, empty_fig, empty_fig

        price_hist = px.histogram(
            filtered_df, x='Prix', nbins=15, color='Type de bien',
            title="Distribution des prix", hover_data=['Localisation']
        )

        type_pie = px.pie(
            filtered_df, names='Type de bien', title="Répartition par type de bien", hole=0.3
        )

        ville_bar = px.bar(
            filtered_df['Localisation'].value_counts().reset_index(name='count'),
            x='Localisation', y='count',
            title="Nombre d'annonces par ville",
            labels={'index': 'Ville', 'count': "Nombre d'annonces"}
        )

        return price_hist, type_pie, ville_bar

    except Exception as e:
        print(f"Erreur dans le callback: {str(e)}")
        empty_fig = px.scatter(title="Erreur lors de l'affichage")
        return empty_fig, empty_fig, empty_fig

    


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=8060)
