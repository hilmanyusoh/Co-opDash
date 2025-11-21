# src/components/sidebar.py

from dash import html
import dash_bootstrap_components as dbc
import datetime

# --- 1. Layout Styles ---
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "18rem", 
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa", 
    "box-shadow": "2px 0 5px rgba(0, 0, 0, 0.1)",
}

def render_sidebar():
    """สร้าง Layout ของแถบด้านข้าง (Sidebar)"""
    return html.Div(
        [
            html.H2("Admin Center", className="display-4 text-primary"),
            html.Hr(),
            html.P("ระบบจัดการและวิเคราะห์ข้อมูลสมาชิก", className="lead"),
            dbc.Nav(
                [
                    dbc.NavLink("Home", 
                                href="/home", 
                                id="page-home", 
                                active="exact"),
                    dbc.NavLink("Dashboard Analysis", 
                                href="/analysis", 
                                id="page-analysis", 
                                active="exact"),
                    dbc.NavLink("Data Review & Search", 
                                href="/review", 
                                id="page-review", 
                                active="exact"),
                ],
                vertical=True,
                pills=True,
                className="mt-4"
            ),
            html.Div(
                f"อัปเดต ณ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
                style={'position': 'absolute', 
                       'bottom': '10px', 
                       'fontSize': '0.75rem', 
                       'color': '#777'}
            )
        ],
        style=SIDEBAR_STYLE,
    )