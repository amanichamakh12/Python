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
    
   

# Création de l'application
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.H1("Tableau de bord des annonces Tayara.tn", 
                   className="text-center my-4"),
            html.P("Analyse des données immobilières", 
                  className="text-muted text-center")
        ], width=12)
    ]),    
    dbc.Row([
       dbc.Col([
    html.Label("Type de bien:"),
    dcc.Dropdown(
        id='type-filter',
        options=[{'label': typ, 'value': typ} 
                for typ in sorted(df['Type de bien'].unique()) 
                if pd.notna(typ) and str(typ).strip() not in [' ', 'N/A']] 
                if not df.empty else [],
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
        min=price_min,
        max=price_max,
        value=[price_25, price_75],
        marks={
            price: f"{price//1000}k" if price < 1000000 else f"{price//1000000}M"
            for price in sorted({
                price_min,
                price_25,
                int(df['Prix'].median()) if not df.empty else (price_min + price_max)//2,
                price_75,
                price_max
            })
        },
        step=max(10000, (price_max - price_min)//100),  # Pas dynamique
        tooltip={"placement": "bottom", "always_visible": True}
    )
], width=4)
    ], style={'marginBottom': '20px'}),

   dbc.Col([
    html.Label("Fourchette de superficie (m²):"),
    dcc.RangeSlider(
        id='superficie-slider',
        min=superficie_min,
        max=superficie_max,
        value=[
            int(df['Superficie'].quantile(0.1)) if not df.empty else 0,
            int(df['Superficie'].quantile(0.9)) if not df.empty else 500
        ],
        marks={
            i: f"{i}m²" 
            for i in range(
                superficie_min, 
                superficie_max + 1, 
                max(10, (superficie_max - superficie_min) // 5)
            )
        },
        tooltip={"placement": "bottom", "always_visible": True}
    )
], width=4),
    
    dbc.Row([
        dbc.Col([
            dbc.Button(
                "Exporter les données",
                id="export-btn",
                color="primary",
                className="d-grid gap-2 col-6 mx-auto"
            ),
            dcc.Download(id="download-data")
        ], width=12)
    
], className="container-fluid"),
dbc.Row([
    dbc.Col(
        dcc.Graph(
            id='map-figure',  # Cet ID doit correspondre à celui dans le callback
            style={'height': '500px'}  # Ajustez la hauteur selon vos besoins
        ),
        width=12
    )
]),
  
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
     Output('price-boxplot', 'figure'),
     Output('map-figure','figure')],
    [Input('price-slider', 'value'),
     Input('type-filter', 'value'),
     Input('location-filter', 'value'),
     Input('superficie-slider','value')]
)
def update_graphs(price_range, selected_types, selected_locations,selected_superficie,):
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
          # Filtrage par superficie
        if selected_superficie:
            filtered_df = filtered_df[
                (filtered_df['Superficie'] >= selected_superficie[0]) & 
                (filtered_df['Superficie'] <= selected_superficie[1])
            ]
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
        x='Localisation',  
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

        try:
            # Ceci est un exemple simplifié - vous devrez adapter selon vos données
            fig_map = px.scatter_map(
                filtered_df,
                lat=[36.8] * len(filtered_df),  
                lon=[10.1] * len(filtered_df), 
                hover_name="Localisation",
                hover_data=["Prix", "Type de bien"],
                color="Type de bien",
                zoom=10,
                height=500,
                title="Localisation des biens"
            )
            fig_map.update_layout(
                mapbox_style="open-street-map",
                margin={"r":0,"t":0,"l":0,"b":0}
            )
        except Exception as e:
            print(f"Erreur création carte: {str(e)}")
            fig_map = px.scatter(title="Carte non disponible - données de localisation manquantes")
        
        return price_hist, type_pie, ville_bar, price_box, fig_map
    
    except Exception as e:
        print(f"Erreur dans le callback: {str(e)}")
        error_fig = px.scatter(title=f"Erreur: {str(e)}")
        return error_fig, error_fig, error_fig, error_fig, error_fig

if __name__ == '__main__':
    app.run(debug=True, port=8060)