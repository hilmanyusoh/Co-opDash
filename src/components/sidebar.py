# src/components/sidebar.py

from dash import html
import dash_bootstrap_components as dbc
import datetime

# Sidebar Style (คงเดิมไว้)
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "285px",
    "padding": "1rem",
    "background-color": "#ffffff",
    "box-shadow": "2px 0 5px rgba(0, 0, 0, 0.1)",
    "overflow-y": "auto",
    "z-index": 1000,
}

# ==================================================
# Navigation Items (แก้ไขจุดนี้)
# ==================================================
NAV_ITEMS = [
    {
        "label": "ภาพรวมระบบ",
        "href": "/dashboard",
        "icon": "fa-solid fa-gauge",
    },
    {
        "label": "วิเคราะห์ข้อมูลที่อยู่",
        "href": "/addressdash",  # ต้องตรงกับ Path ที่ตั้งไว้ใน app.py
        "icon": "fa-solid fa-map-location-dot", # เปลี่ยนไอคอนให้สื่อถึงแผนที่
    },
]

# Sidebar Layout
def render_sidebar():
    current_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

    return html.Div(
        [
            # Header
            html.Div(
                [
                    html.H4("I-Corp Dash", className="text-primary fw-bold mb-0"),
                ],
                className="text-center mb-3",
            ),
            html.Hr(className="my-3"),
            
            # Navigation Menu
            dbc.Nav(
                [
                    dbc.NavLink(
                        [
                            html.I(className=f"fas {item['icon']} me-3"), # เพิ่มระยะห่าง icon นิดหน่อย
                            html.Span(item["label"]),
                        ],
                        href=item["href"],
                        active="exact",
                        className="mb-2 py-2 px-3", # เพิ่ม Padding ให้กดง่ายขึ้น
                        style={
                            "borderRadius": "8px",
                            "transition": "all 0.2s ease",
                        },
                    )
                    for item in NAV_ITEMS
                ],
                vertical=True,
                pills=True,
                className="flex-column",
            ),

            # Footer
            html.Div(
                [
                    html.Hr(className="my-3"),
                    html.Small(
                        [
                            html.I(className="fas fa-clock me-2"),
                            f"อัปเดต: {current_time}"
                        ],
                        className="text-muted text-center d-block mb-1",
                    ),
                    html.Small(
                        [html.I(className="fas fa-info-circle me-2"), "v1.0.1"],
                        className="text-muted text-center d-block",
                    ),
                ],
                style={
                    "position": "absolute",
                    "bottom": "15px",
                    "left": "1rem",
                    "right": "1rem",
                },
            ),
        ],
        style=SIDEBAR_STYLE,
        id="sidebar",
    )