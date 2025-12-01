# src/app.py

import dash
import dash_bootstrap_components as dbc

# Dash Instance
app = dash.Dash(
    __name__, 
    external_stylesheets=[
        dbc.themes.COSMO, 
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css"
    ], 
    suppress_callback_exceptions=True
) 
app.title = "Dashboard members"