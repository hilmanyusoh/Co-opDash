from dash import html
import dash_bootstrap_components as dbc

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0, "left": 0, "bottom": 0,
    "width": "285px",
    "padding": "1rem",
    "background-color": "#ffffff",
    "box-shadow": "2px 0 5px rgba(0, 0, 0, 0.1)",
    "overflow-y": "auto",
    "z-index": 1000,
}

def render_single_nav(label, href, icon):
    return html.Div(
        dbc.NavLink(
            [
                html.I(className=f"fas {icon} me-3", style={"width": "20px"}),
                html.Span(label, className="fw-medium"),
            ],
            href=href,
            active="exact",
            className="py-3 px-3 mb-1",
            style={
                "borderRadius": "8px", 
                "fontSize": "1rem",  
                "display": "flex",
                "alignItems": "center",
                "color": "black"  # ตัวหนังสือปกติสีดำ
            }
        ),
        className="nav-main"
    )

def render_sub_nav(label, href, icon):
    return html.Div(
        dbc.NavLink(
            [
                html.I(className=f"fas {icon} me-3", style={"width": "20px", "opacity": "0.7"}),
                html.Span(label),
            ],
            href=href,
            active="exact",
            className="py-2 px-3 mb-1",
            # เมนูย่อยใช้ CSS ควบคุมสีขาวเมื่อ Active (ผ่านไฟล์ style.css)
        ),
        className="nav-sub"
    )

def render_sidebar():
    return html.Div(
        [
            # Header
            html.Div([
                html.H4("I-Corp Dash", className="text-primary fw-bold mb-0"),
            ], className="text-center mb-3 mt-2"),
            html.Hr(className="my-3"),
            
            dbc.Nav(
                [
                    render_single_nav("ข้อมูลภาพรวม", "/overview", "fa-gauge-high"),

                    # Accordion: สมาชิก (ปรับแต่งให้เหมือนเมนูหลัก)
                    dbc.Accordion(
                        [
                            dbc.AccordionItem(
                                children=dbc.Nav(
                                    [ 
                                        render_sub_nav("ข้อมูลสมาชิก", "/member", "fa-user-group"),
                                        render_sub_nav("ข้อมูลสาขา", "/branches", "fa-building-columns"),
                                        render_sub_nav("ข้อมูลเชิงพื้นที่", "/address", "fa-map-location-dot"),
                                        render_sub_nav("ข้อมูลการเงิน", "/amount", "fa-sack-dollar"),
                                    ],
                                    vertical=True, pills=True
                                ),
                                # แก้ไข title ตรงนี้ให้เป็นสีดำ
                                title=html.Span([
                                    html.I(className="fas fa-users me-3", style={"width": "20px", "color": "black"}), 
                                    html.Span("สมาชิก", style={"color": "black"})
                                ], className="fw-medium d-flex align-items-center"),
                                item_id="acc_members",
                            ),
                        ],
                        flush=True, 
                        start_collapsed=True,
                        className="mb-1 border-0",
                        # ล้างค่าสีฟ้ามาตรฐานของ Bootstrap Accordion
                        style={
                            "--bs-accordion-btn-color": "black",
                            "--bs-accordion-active-color": "black",
                            "--bs-accordion-active-bg": "#f8fafc", # พื้นหลังเทาจางๆ เมื่อกางออก
                            "--bs-accordion-btn-focus-box-shadow": "none",
                            "--bs-accordion-border-color": "transparent",
                        }
                    ),

                    render_single_nav("การคำนวณเครดิต", "/credit-score", "fa-calculator"),
                    render_single_nav("การคาดการณ์", "/performance", "fa-chart-line"),
                ],
                vertical=True, 
                pills=True,
                className="w-100"
            ),
        ],
        style=SIDEBAR_STYLE,
        id="sidebar",
    )