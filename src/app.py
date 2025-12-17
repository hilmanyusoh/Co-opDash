# src/app.py

import dash
import dash_bootstrap_components as dbc

# สร้าง Dash Instance
app = dash.Dash(
    __name__, 
    external_stylesheets=[
        dbc.themes.COSMO,  
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
    ], 
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
) 

app.title = "Dashboard Members"

# สำหรับ deployment
server = app.server