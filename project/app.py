# app.py

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import datetime

# คำสั่งนี้เป็น Direct Import อยู่แล้ว และทำงานได้ถูกต้อง
from callbacks import register_callbacks 
# ไม่จำเป็นต้อง import layout_home/analysis/review ตรงๆ ที่นี่ เพราะถูก import ใน callbacks.py แล้ว

# --- 1. การกำหนดค่า Dash App และ Template ---
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.COSMO, "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css"], 
                suppress_callback_exceptions=True) 
app.title = "MongoDB Admin Dashboard (Dash)"

# --- 2. Sidebar Layout ---
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

# ตำแหน่งสำหรับเนื้อหาหลัก
CONTENT_STYLE = {
    "margin-left": "18rem", 
    "padding": "2rem 2rem",
}

sidebar = html.Div(
    [
        html.H2("Admin Center", className="display-4 text-primary"),
        html.Hr(),
        html.P(
            "ระบบจัดการและวิเคราะห์ข้อมูลสมาชิก", className="lead"
        ),
        dbc.Nav(
            [
                dbc.NavLink(" Home (บันทึกข้อมูล)", href="/home", id="page-home", active="exact"),
                dbc.NavLink(" Dashboard Analysis", href="/analysis", id="page-analysis", active="exact"),
                dbc.NavLink(" Data Review & Search", href="/review", id="page-review", active="exact"),
            ],
            vertical=True,
            pills=True,
            className="mt-4"
        ),
        html.Div(
            f"อัปเดตข้อมูล ณ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            style={'position': 'absolute', 'bottom': '10px', 'fontSize': '0.75rem', 'color': '#777'}
        )
    ],
    style=SIDEBAR_STYLE,
)

# --- 3. การจัด Layout หลักของแอปพลิเคชัน ---
app.layout = html.Div([
    dcc.Location(id="url", refresh=False), 
    sidebar, 
    html.Div(id="page-content", style=CONTENT_STYLE), 
])

# --- 4. ลงทะเบียน Callbacks ---
register_callbacks(app)

# --- 5. รันแอปพลิเคชัน ---
if __name__ == '__main__':
    # ตั้งค่า debug=True สำหรับการพัฒนา
    app.run(debug=True)