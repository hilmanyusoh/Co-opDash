# src/components/sidebar.py

from dash import html
import dash_bootstrap_components as dbc
import datetime

# =========================
# Sidebar Style
# =========================
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
    "box-shadow": "2px 0 5px rgba(0, 0, 0, 0.1)",
    "overflow-y": "auto",
    "z-index": 1000,
}

# =========================
# Navigation Items
# =========================
NAV_ITEMS = [
    {
        "label": "เพิ่มสมาชิก",
        "href": "/home",
        "icon": "fa-user-plus",
    },
    {
        "label": "วิเคราะห์ข้อมูล",
        "href": "/analysis",
        "icon": "fa-chart-bar",
    },
    {
        "label": "ค้นหาข้อมูล",
        "href": "/review",
        "icon": "fa-search",
    },
]

# =========================
# Sidebar Layout
# =========================
def render_sidebar():
    """สร้าง Sidebar พร้อมเมนูนำทาง"""
    
    current_time = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
    
    return html.Div([
        # Header
        html.Div([
            html.I(className="fas fa-users-cog fa-2x text-primary mb-2"),
            html.H4("Admin Center", className="text-primary fw-bold mb-0"),
        ], className="text-center mb-3"),
        
        html.Hr(className="my-3"),
        
        # Description
        html.P(
            "ระบบจัดการข้อมูลสมาชิก",
            className="text-muted text-center mb-4 small"
        ),
        
        # Navigation Menu
        dbc.Nav([
            dbc.NavLink([
                html.I(className=f"fas {item['icon']} me-2"),
                html.Span(item['label']),
            ],
            href=item['href'],
            active="exact",
            className="mb-2",
            style={
                "borderRadius": "8px",
                "transition": "all 0.2s ease",
            })
            for item in NAV_ITEMS
        ],
        vertical=True,
        pills=True,
        className="flex-column"),
        
        # System Info
        html.Hr(className="my-4"),
        
        html.Div([
            html.Small([
                html.I(className="fas fa-circle text-success me-2", 
                       style={"fontSize": "0.5rem"}),
                "ระบบพร้อมใช้งาน"
            ], className="text-muted d-block mb-2"),
            html.Small([
                html.I(className="fas fa-clock me-2 text-muted"),
                current_time
            ], className="text-muted d-block"),
        ], className="px-2"),
        
        # Footer
        html.Div([
            html.Hr(className="my-3"),
            html.Small([
                html.I(className="fas fa-info-circle me-2"),
                "Dashboard v1.0"
            ], className="text-muted text-center d-block"),
        ],
        style={
            "position": "absolute",
            "bottom": "10px",
            "left": "1rem",
            "right": "1rem",
        }),
    ],
    style=SIDEBAR_STYLE,
    id="sidebar")