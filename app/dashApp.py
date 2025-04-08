from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import requests
from dash.exceptions import PreventUpdate
 

try:
    url = "http://fastapi:8000/AllAnnonces"
    #url = "http://127.0.0.1:8000/AllAnnonces"#pour tester en locale 

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    df = pd.DataFrame(data.get('data', []))
except Exception as e:
    print(f"Erreur lors de la récupération des données: {str(e)}")
    df = pd.DataFrame()
 

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
     .str.replace(r'[^\d.]', '', regex=True)  
     .replace(['na', 'n/a', 'N/A', ''], '0')  
    )
     
df['Superficie'] = pd.to_numeric(df['Superficie'], errors='coerce')
     
df['Superficie'] = df['Superficie'].fillna(0)
df = df[df['Superficie'] > 0]  
     
df['Superficie'] = df['Superficie'].round().astype(int)
superficie_min = int(df['Superficie'].min()) if 'Superficie' in df.columns and not df.empty else 0
superficie_max = int(df['Superficie'].max()) if 'Superficie' in df.columns and not df.empty else 500
 
     
df = df.reset_index(drop=True)

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
    'color': '#2ca02c'  
}

HEADER_STYLE = {
    'backgroundColor': '#f8f9fa',
    'padding': '2rem 1rem',
    'marginBottom': '2rem'
}

# ======================================================================
# LAYOUT DU DASHBOARD
# ======================================================================
 
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([
    dbc.Row(dbc.Col(html.Div([
        html.H1("Dashboard Immobilier", className="display-4"),
        html.P("Analyse des données immobilières en temps réel", className="lead")
    ], style=HEADER_STYLE), width=12)),

    dbc.Row([

        dbc.Col([
            html.Div([
                html.Label("Type de bien:"),
                dcc.Dropdown(
                    id='type-filter',
                    options=[{'label': typ, 'value': typ} for typ in df['Type de bien'].unique()] if not df.empty else [],
                    multi=True,
                    placeholder="Tous types"
                ),
                html.Br(),

                html.Label("Localisation:"),
                dcc.Dropdown(
                    id='location-filter',
                    options=[{'label': loc, 'value': loc} for loc in df['Localisation'].unique()] if not df.empty else [],
                    multi=True,
                    placeholder="Toutes villes"
                ),
                html.Br(),

                html.Label("Fourchette de prix (DT):"),
                dcc.RangeSlider(
                    id='price-slider',
                    min=int(df['Prix'].min()) if not df.empty else 0,
                    max=int(df['Prix'].max()) if not df.empty else 1000000,
                    value=[int(df['Prix'].min()) if not df.empty else 0, int(df['Prix'].max()) if not df.empty else 1000000],
                    marks={i: f"{i//1000}k" for i in range(0, (int(df['Prix'].max()) if not df.empty else 1000000)+1, 100000)},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ], style=CARD_STYLE)
        ], width=3),

        dbc.Col([
            dbc.Row([
                dbc.Col(html.Div(dcc.Graph(id='price-distribution'), style=CARD_STYLE), width=6),
                dbc.Col(html.Div(dcc.Graph(id='type-distribution'), style=CARD_STYLE), width=6)
            ]),
            html.Br(),
            dbc.Row([
                dbc.Col(html.Div(dcc.Graph(id='ville-distribution'), style=CARD_STYLE), width=6),
                dbc.Col(html.Div(dcc.Graph(id='price-boxplot'), style=CARD_STYLE), width=6)
            ])
        ], width=9)

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
        
        filtered_df = filtered_df[
            (filtered_df['Prix'] >= price_range[0]) & 
            (filtered_df['Prix'] <= price_range[1])
        ]
        
        if selected_types:
            filtered_df = filtered_df[filtered_df['Type de bien'].isin(
                [selected_types] if isinstance(selected_types, str) else selected_types
            )]
        
        if selected_locations:
            filtered_df = filtered_df[filtered_df['Localisation'].isin(
                [selected_locations] if isinstance(selected_locations, str) else selected_locations
            )]
        
        if filtered_df.empty:
            empty_fig = px.scatter(title="Aucune donnée correspondante")
            return empty_fig, empty_fig, empty_fig, empty_fig
        
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
        x='Localisation',  
        y='count',  
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
        app.run(host="0.0.0.0",debug=True, port=8060)

