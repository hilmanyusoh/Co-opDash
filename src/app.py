import os
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from dotenv import load_dotenv

# Import หน้าที่จำเป็น
from .components.sidebar import render_sidebar
from .pages import dashboard  # เปลี่ยนจาก dashboard เป็น analysis ให้ตรงกับชื่อไฟล์
from .pages import addressdash # เพิ่มการ Import หน้าที่อยู่

load_dotenv()  

app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.COSMO,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
        "https://fonts.googleapis.com",
        "https://fonts.gstatic.com",
        "https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@100..900&display=swap",
    ],
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

app.title = "I-Corp Dash"

# Layout Styles
CONTENT_STYLE = {
    "margin-left": "285px", # ปรับให้เท่ากับความกว้าง sidebar ใน sidebar.py
    "padding": "1.5rem",
}

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        render_sidebar(),
        html.Div(id="page-content", style=CONTENT_STYLE),
    ]
)

# Callback หลัก: การจัดการ Routing
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    # 1. หน้า Dashboard / Analysis หลัก
    if pathname == "/" or pathname == "/dashboard":
        return dashboard.layout
    
    # 2. หน้า วิเคราะห์ที่อยู่ (เพิ่มส่วนนี้)
    elif pathname == "/addressdash":
        return addressdash.layout

    # 3. หน้า 404 (เปลี่ยนจาก Jumbotron เป็น Div)
    return html.Div(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"เส้นทาง {pathname} ไม่ถูกต้อง"),
        ],
        className="p-3 bg-light rounded-3",
    )

# Callbacks ของแต่ละ Page
if hasattr(dashboard, 'register_callbacks'):
    dashboard.register_callbacks(app)
if hasattr(addressdash, 'register_callbacks'):
    addressdash.register_callbacks(app)

if __name__ == "__main__":
    app.run(
        debug=os.getenv("DEBUG") == "True",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8050)),
    )