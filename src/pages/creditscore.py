import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd
from ..data_manager import get_member_profile 

# ==================================================
# 1. Helper Functions (คงเดิม)
# ==================================================
def format_value(val, key):
    if val == "-" or val is None or val == "": return "-"
    if key == "account_number": return str(val)
    
    if any(x in key for x in ["count", "overdue", "installments", "accounts", "months", "inquiries"]):
        try: return f"{int(float(val))} งวด/ครั้ง"
        except: return val

    if any(x in key for x in ["pct", "rate"]):
        try: return f"{float(val):,.2f} %"
        except: return val

    if any(x in key for x in ["amount", "income", "balance", "limit", "payment", "approved", "value"]):
        try: return f"{float(val):,.2f} บาท"
        except: return val
        
    if "days" in key:
        try: return f"{int(float(val))} วัน"
        except: return val
        
    return val

def create_info_section(title, fields, data):
    rows = [
        html.Tr([
            html.Td(html.H6(title, className="text-primary fw-bold mt-3 mb-2 border-bottom pb-1", 
                            style={"fontFamily": "Sarabun", "fontSize": "15px"}), 
                    colSpan=2, className="border-0")
        ])
    ]
    for label, key in fields:
        val = format_value(data.get(key, "-"), key)
        rows.append(html.Tr([
            html.Td(label, className="text-muted border-0 ps-3 py-1", 
                    style={"width": "45%", "fontSize": "13px", "fontFamily": "Sarabun"}),
            html.Td(html.B(val, className="text-dark"), className="border-0 py-1", 
                    style={"fontSize": "14px", "fontFamily": "Sarabun"})
        ]))
    return rows

# ==================================================
# 2. UI Components
# ==================================================

def create_member_detail_table(data):
    # --- ส่วนที่ 1: Logic การพิจารณา ---
    score = data.get('credit_score', 0)
    income = data.get('monthly_income', 0)
    
    if score >= 753: # AA
        status, color, multiplier = "แนะนำให้อนุมัติ", "success", 5.0
        advice = "ลูกค้ามีวินัยการเงินสูงมาก แนะนำเสนอวงเงินสูงสุดพร้อมอัตรากำไร"
    elif score >= 681: # BB, CC, DD
        status, color, multiplier = "พิจารณาอนุมัติ (ปานกลาง)", "primary", 3.0
        advice = "ลูกค้ามีความเสี่ยงยอมรับได้ ควรตรวจสอบภาระหนี้ปัจจุบันประกอบการตัดสินใจ"
    elif score >= 616: # EE, FF, GG
        status, color, multiplier = "พิจารณาด้วยความระมัดระวัง", "warning", 1.5
        advice = "ลูกค้ามีความเสี่ยงค่อนข้างสูง แนะนำให้ขอเอกสารค้ำประกันหรือปรับลดวงเงิน"
    else: # HH
        status, color, multiplier = "ไม่แนะนำให้อนุมัติ", "danger", 0
        advice = "ลูกค้ามีประวัติค้างชำระหรือคะแนนต่ำเกินเกณฑ์มาตรฐาน ไม่แนะนำให้สร้างหนี้เพิ่ม"

    estimated_limit = income * multiplier

    # --- ส่วนที่ 2: ผลการประเมินเครดิต (Score Card) ---
    score_fields = [
        ("คะแนนเครดิต", "credit_score"), 
        ("เรตติ้ง", "credit_rating"),
        ("ระดับความเสี่ยง", "risk_category"),
        ("ช่วงคะแนน", "score_range")
    ]
    
    score_card = dbc.Card([
        dbc.CardBody([
            html.H5("ผลการประเมินเครดิต", className="text-primary mb-4 fw-bold ", 
                    style={"fontFamily": "Sarabun", "fontSize": "16px"}),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Small(label, className="text-muted d-block mb-1", style={"fontSize": "12px"}),
                        html.H3(format_value(data.get(key, "-"), key), 
                                className="text-dark fw-bold mb-0", 
                                style={"fontFamily": "Sarabun", "fontSize": "24px"})
                    ], className=f"text-center {'border-end' if i < len(score_fields)-1 else ''}")
                ], width=3) for i, (label, key) in enumerate(score_fields)
            ])
        ], className="p-4")
    ], className="mb-4 shadow-sm border-0", style={"backgroundColor": "white", "borderRadius": "15px"})

    # --- ส่วนที่ 3: กล่องพิจารณาสินเชื่อ (Recommendation Card) ---
    recommendation_card = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                # ฝั่งซ้าย: สถานะ
                dbc.Col([
                    html.Small("สถานะการพิจารณา", className="text-muted d-block", style={"fontSize": "11px", "fontFamily": "Sarabun"}),
                    html.Span(status, className=f"text-{color} fw-bold", style={"fontSize": "14px", "fontFamily": "Sarabun"})
                ], width=4, className="border-end"),
                
                # ฝั่งขวา: วงเงิน
                dbc.Col([
                    html.Small("วงเงินกู้สูงสุดที่แนะนำ", className="text-muted d-block", style={"fontSize": "11px", "fontFamily": "Sarabun"}),
                    html.Span(f"{estimated_limit:,.2f} บาท", className="text-dark fw-bold", style={"fontSize": "15px", "fontFamily": "Sarabun"})
                ], width=8),
            ], className="align-items-center mb-2"),
            
            # หมายเหตุ
            html.Div([
                html.Small(f"หมายเหตุ: {advice}", className="text-muted", style={"fontSize": "11px", "fontStyle": "italic", "fontFamily": "Sarabun"})
            ], className="pt-2 border-top")
        ], className="p-3")
    ], className="mb-4 shadow-sm border-0", style={"borderRadius": "12px", "backgroundColor": "#f8f9fa"})

    # --- ส่วนที่ 4: Tabs (คงเดิม) ---
    all_tabs = []
    all_tabs.append(dbc.Tab(
        dbc.Card([
            dbc.CardBody([
                dbc.Table(html.Tbody(create_info_section("ข้อมูลส่วนบุคคล", [
                    ("รหัสลูกค้า", "customer_id"), ("เลขบัตรประชาชน", "national_id"),
                    ("ชื่อผู้กู้", "borrower_name"), ("อายุ", "age"), ("เพศ", "gender"),
                    ("ระดับการศึกษา", "education"), ("อาชีพ", "occupation"), 
                    ("รายได้ต่อเดือน", "monthly_income"), ("เบอร์โทรศัพท์", "phone_number")
                ], data)), borderless=True, size="sm")
            ], className="p-3")
        ], className="border-0 shadow-sm", style={"borderRadius": "0 0 15px 15px"}),
        label="ประวัติส่วนตัว", tab_id="tab-personal", label_style={"fontFamily": "Sarabun", "fontSize": "14px", "fontWeight": "600"}
    ))

    loan_accounts = data.get('accounts', [])
    for i, account in enumerate(loan_accounts):
        loan_num = i + 1
        all_tabs.append(dbc.Tab(
            dbc.Card([
                dbc.CardBody([
                    dbc.Table(html.Tbody(
                        create_info_section("รายละเอียดสินเชื่อ", [
                            ("เลขที่บัญชี", "account_number"), ("ประเภทสินเชื่อ", "product_type"),
                            ("วงเงินอนุมัติ", "credit_limit"), ("ยอดหนี้คงเหลือ", "outstanding_balance"),
                            ("ยอดผ่อนต่อเดือน", "monthly_payment"), ("สถานะบัญชี", "account_status")
                        ], account) + 
                        create_info_section("ประวัติการชำระและพฤติกรรม", [
                            ("ชำระตรงเวลา (%)", "payment_performance_pct"), ("จำนวนงวดที่ค้าง", "installments_overdue"),
                            ("จำนวนวันที่ค้างชำระ (DPD)", "days_past_due"), ("ยอดเงินค้างชำระ", "overdue_amount"),
                            ("ค้างชำระในรอบ 12 เดือน", "late_payment_count_12m"), ("ค้างชำระในรอบ 24 เดือน", "late_payment_count_24m"),
                            ("อัตราใช้วงเงิน (%)", "credit_utilization_rate")
                        ], account)
                    ), borderless=True, size="sm")
                ], className="p-3")
            ], className="border-0 shadow-sm", style={"borderRadius": "0 0 15px 15px"}),
            label=f"สินเชื่อ {loan_num}", tab_id=f"tab-loan-{loan_num}", label_style={"fontFamily": "Sarabun", "fontSize": "14px", "fontWeight": "600"}
        ))
        if loan_num >= 3: break

    return html.Div([
        score_card,          # 1. แสดงคะแนนก่อน
        recommendation_card, # 2. แสดงสถานะการพิจารณาต่อท้าย (ด่านล่าง score)
        dbc.Tabs(all_tabs, id="member-detail-tabs", active_tab=None),
        html.Div(id="tab-placeholder", className="mt-3")
    ])

# ==================================================
# 3. Main Layout & 4. Callbacks (คงเดิม)
# ==================================================

layout = dbc.Container([
    html.Div([
        dbc.Row([
            dbc.Col([
                html.H2("ตรวจสอบข้อมูลสมาชิก", className="fw-bold mb-5", 
                        style={"fontFamily": "Sarabun", "fontSize": "32px","marginTop": "80px", "color": "#1e293b"}),
            ], width=12, className="text-center")
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.InputGroup([
                        dbc.Input(
                            id="national-id-input", 
                            placeholder="ระบุเลขบัตรประชาชน 13 หลัก", 
                            type="text",
                            style={
                                "fontFamily": "Sarabun", 
                                "fontSize": "18px", 
                                "height": "65px",
                                "border": "1px solid #e2e8f0",
                                "borderRadius": "35px 0 0 35px",
                                "paddingLeft": "30px",
                                "backgroundColor": "#ffffff"
                            }
                        ),
                        dbc.Button(
                            "ค้นหา", 
                            id="search-btn", 
                            color="dark", 
                            style={
                                "fontFamily": "Sarabun", 
                                "width": "160px", 
                                "fontSize": "18px",
                                "borderRadius": "0 35px 35px 0",
                                "backgroundColor": "#000000"
                            }
                        ),
                    ], className="shadow-sm", style={"borderRadius": "35px"}),
                    html.Div(id="member-name-display", className="mt-4")
                ], style={"backgroundColor": "transparent"})
            ], width=12, lg=10, xl=9, className="mx-auto px-4 px-md-5")
        ], justify="center"),
    ], id="search-page", style={"minHeight": "100vh", "paddingBottom": "100px"}),

    html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("รายงานข้อมูลเครดิตเชิงลึก", className="fw-bold mb-4 text-primary", style={"fontFamily": "Sarabun"}),
                html.Div(id="detail-content")
            ], width=12)
        ]),
    ], id="detail-page", style={"display": "none", "padding": "40px 20px"})

], fluid=True, style={"minHeight": "100vh", "fontFamily": "Noto Sans Thai", "padding": "0"})

def register_callbacks(app):
    @app.callback(
        [Output("member-name-display", "children"),
         Output("search-page", "style"),
         Output("detail-page", "style")],
        [Input("search-btn", "n_clicks")],
        [State("national-id-input", "value")],
        prevent_initial_call=True
    )
    def handle_search(n, nid):
        if not nid:
            return dash.no_update, {"display": "block", "minHeight": "100vh", "paddingBottom": "100px"}, {"display": "none"}
            
        data = get_member_profile(nid)
        search_page_style = {"display": "block", "minHeight": "100vh", "paddingBottom": "100px"}
        detail_page_style = {"display": "none"}
        
        if data and data.get('borrower_name'):
            content = html.Div([
                html.Div([
                    html.Div([
                        html.Span("ชื่อ: ", style={"fontFamily": "Sarabun", "fontSize": "20px", "color": "#64748b"}),
                        html.Span(data.get('borrower_name'), style={"fontFamily": "Sarabun", "fontSize": "20px"})
                    ]),
                    dbc.Button(
                        "ดูประวัติและคะแนนเครดิต", 
                        id="view-detail-btn", 
                        color="dark", 
                        style={
                            "fontFamily": "Sarabun", 
                            "borderRadius": "25px", 
                            "padding": "8px 25px",
                            "fontSize": "15px",
                            "backgroundColor": "#000000"
                        }
                    )
                ], className="d-flex justify-content-between align-items-center p-3 border shadow-sm", 
                   style={"backgroundColor": "#ffffff", "marginTop": "20px", "borderRadius": "30px", "border": "1px solid #e2e8f0"})
            ])
            return content, search_page_style, detail_page_style
            
        return dbc.Alert("ไม่พบข้อมูลสมาชิก", color="danger", className="mt-4 text-center", 
                        style={"borderRadius": "30px", "fontFamily": "Sarabun"}), search_page_style, detail_page_style

    @app.callback(
        [Output("search-page", "style", allow_duplicate=True), 
         Output("detail-page", "style", allow_duplicate=True), 
         Output("detail-content", "children")],
        Input("view-detail-btn", "n_clicks"),
        State("national-id-input", "value"),
        prevent_initial_call=True
    )
    def toggle_report_page(n, nid):
        if n and nid:
            data = get_member_profile(nid)
            if data:
                return {"display": "none"}, {"display": "block", "padding": "40px 20px"}, create_member_detail_table(data)
        return dash.no_update, dash.no_update, dash.no_update

    @app.callback(
        Output("tab-placeholder", "children"),
        Input("member-detail-tabs", "active_tab")
    )
    def update_tab_placeholder(active_tab):
        if active_tab is None:
            return html.Div([
                html.Div("กรุณาคลิกเลือกหัวข้อด้านบน (ประวัติส่วนตัว หรือ สินเชื่อ) เพื่อแสดงข้อมูล", 
                        className="text-center p-5 text-muted border rounded-3 bg-white shadow-sm",
                        style={"fontFamily": "Sarabun"})
            ])
        return ""