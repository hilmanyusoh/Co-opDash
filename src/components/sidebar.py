from dash import html
import dash_bootstrap_components as dbc
import datetime

# Sidebar Style
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

# ส่วนประกอบเมนูเดี่ยว (Overview / Performance)
def render_single_nav(label, href, icon):
    return dbc.NavLink(
        [
            html.I(className=f"fas {icon} me-3", style={"width": "20px"}),
            html.Span(label, className="fw-medium"),
        ],
        href=href,
        active="exact",
        className="py-3 px-3 mb-1 text-dark",
        style={"borderRadius": "8px", "fontSize": "1rem", "display": "flex", "alignItems": "center"}
    )

# ส่วนประกอบเมนูย่อย (ภายใน Accordion)
def render_sub_nav(label, href, icon):
    return dbc.NavLink(
        [
            html.I(className=f"fas {icon} me-3", style={"width": "20px", "opacity": "0.7"}),
            html.Span(label),
        ],
        href=href,
        active="exact",
        className="py-2 px-3 mb-1",
        style={"borderRadius": "8px", "fontSize": "0.92rem"}
    )

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
            
            # 1. ข้อมูลภาพรวม (ไม่มีเมนูย่อย)
            render_single_nav("ข้อมูลภาพรวม", "/overview", "fa-gauge-high"),

            # 2. สมาชิก (Accordion)
            dbc.Accordion(
                [
                    dbc.AccordionItem(
                        dbc.Nav(
                            [
                                render_sub_nav("ข้อมูลประชากร", "/member", "fa-user-group"),
                                render_sub_nav("ข้อมูลสาขา", "/branches", "fa-building-columns"),
                                render_sub_nav("ข้อมูลเชิงพื้นที่", "/address", "fa-map-location-dot"),

                                # ⭐ เพิ่มเมนูข้อมูลทางการเงิน
                                render_sub_nav("ข้อมูลทางการเงิน","/amount",
                                    "fa-sack-dollar"),
                            ],

                            vertical=True, 
                            pills=True
                        ),
                        title=html.Span([
                            html.I(className="fas fa-users me-3", style={"width": "20px"}), 
                            "สมาชิก"
                        ], className="fw-medium"),
                        item_id="acc_members",
                    ),
                ],
                flush=True, 
                start_collapsed=True, 
                className="mb-1 border-0",
                # ปรับสไตล์ให้ Accordion ดูสะอาด
                style={"--bs-accordion-bg": "transparent", "--bs-accordion-border-color": "transparent"}
            ),

            # 4. Performance (ไม่มีเมนูย่อย)
            render_single_nav("Performance", "/performance", "fa-chart-line"),

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
                        [html.I(className="fas fa-shield-halved me-2"), "v1.2.0"],
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