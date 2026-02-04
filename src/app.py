import os
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from dotenv import load_dotenv

# Import หน้าที่จำเป็น
from .components.sidebar import render_sidebar
from .pages import overview, creditscore, member, branches, address, performance, amount

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

CONTENT_STYLE = {
    "margin-left": "285px", 
    "padding": "1.5rem",
}

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False, pathname="/overview"),
        render_sidebar(),
        html.Div(id="page-content", style=CONTENT_STYLE),
    ]
)

# ==================================================
# 🔄 Callback หลัก: จัดการ Routing และย้ายขีดสีฟ้าใน Sidebar
# ==================================================
@app.callback(
    [Output("page-content", "children"),
     Output("nav-overview", "active"),
     Output("nav-credit", "active"),
     Output("nav-performance", "active")],
    [Input("url", "pathname")]
)
def render_and_update_sidebar(pathname):
    # 1. เลือก Layout ที่จะแสดงผลตาม URL
    if pathname == "/" or pathname == "/overview":
        content = overview.layout
    elif pathname == "/credit-score":
        content = creditscore.layout
    elif pathname == "/member":
        content = member.layout
    elif pathname == "/branches":
        content = branches.layout
    elif pathname == "/address":
        content = address.layout
    elif pathname == "/amount":   
        content = amount.layout
    elif pathname == "/performance":
        content = performance.layout
    else:
        content = html.Div([
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"เส้นทาง {pathname} ไม่ถูกต้อง"),
        ], className="p-3 bg-light rounded-3")

    # 2. ตรวจสอบสถานะเมนูใน Sidebar (Active Link)
    is_overview = pathname in ["/", "/overview"]
    is_credit = pathname == "/credit-score"
    is_performance = pathname == "/performance"

    # คืนค่าทีเดียว 4 อย่าง: (เนื้อหาหน้าเว็บ, ขีดสีฟ้าเมนู 1, เมนู 2, เมนู 3)
    return content, is_overview, is_credit, is_performance


# Callbacks ของแต่ละ Page
if hasattr(overview, 'register_callbacks'):
    overview.register_callbacks(app)

if hasattr(creditscore, 'register_callbacks'):
    creditscore.register_callbacks(app)    
    
if hasattr(member, 'register_callbacks'):
    member.register_callbacks(app)

if __name__ == "__main__":
    app.run(
        debug=os.getenv("DEBUG") == "True",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8050)),
    )