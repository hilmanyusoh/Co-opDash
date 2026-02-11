import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd
from ..data_manager import get_member_profile 
# ==================================================
# 1. Helper Functions - Enhanced
# ==================================================
def format_value(val, key):
    """ฟังก์ชันจัดรูปแบบค่าตามประเภทข้อมูล"""
    if val == "-" or val is None or val == "": 
        return "-"
    if key == "account_number": 
        return str(val)
    
    if any(x in key for x in ["count", "overdue", "installments", "accounts", "months", "inquiries"]):
        try: 
            return f"{int(float(val)):,} งวด/ครั้ง"
        except: 
            return val
    if any(x in key for x in ["pct", "rate"]):
        try: 
            return f"{float(val):,.2f}%"
        except: 
            return val
    if any(x in key for x in ["amount", "income", "balance", "limit", "payment", "approved", "value"]):
        try: 
            return f"฿{float(val):,.2f}"
        except: 
            return val
        
    if "days" in key:
        try: 
            return f"{int(float(val)):,} วัน"
        except: 
            return val
        
    return val
def get_risk_badge(score):
    """สร้าง badge แสดงระดับความเสี่ยง"""
    if score >= 753:
        return dbc.Badge("ความเสี่ยงต่ำมาก", color="success", className="px-3 py-2", 
                        style={"fontSize": "12px", "fontWeight": "500"})
    elif score >= 681:
        return dbc.Badge("ความเสี่ยงปานกลาง", color="primary", className="px-3 py-2",
                        style={"fontSize": "12px", "fontWeight": "500"})
    elif score >= 616:
        return dbc.Badge("ความเสี่ยงสูง", color="warning", className="px-3 py-2",
                        style={"fontSize": "12px", "fontWeight": "500"})
    else:
        return dbc.Badge("ความเสี่ยงสูงมาก", color="danger", className="px-3 py-2",
                        style={"fontSize": "12px", "fontWeight": "500"})
def create_info_row(label, value, icon=None):
    """สร้างแถวข้อมูลแบบสวยงาม"""
    return dbc.Row([
        dbc.Col([
            html.Div([
                html.I(className=f"bi bi-{icon} me-2 text-primary") if icon else None,
                html.Span(label, className="text-muted", 
                         style={"fontSize": "13px", "fontFamily": "Sarabun"})
            ])
        ], width=5),
        dbc.Col([
            html.Div(value, className="fw-bold text-dark", 
                    style={"fontSize": "14px", "fontFamily": "Sarabun"})
        ], width=7)
    ], className="mb-2 py-2 border-bottom border-light")
# ==================================================
# 2. UI Components - Modern Design
# ==================================================
def create_credit_score_hero(data):
    """สร้างส่วนแสดงคะแนนเครดิตแบบ Hero Section"""
    score = data.get('credit_score', 0)
    rating = data.get('credit_rating', '-')
    
    # กำหนดสีตามคะแนน (จางลง)
    if score >= 753:
        score_color = "#22c55e"
        bg_gradient = "linear-gradient(135deg, #22c55e 0%, #15803d 100%)"
    elif score >= 681:
        score_color = "#2563eb"
        bg_gradient = "linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)"
    elif score >= 616:
        score_color = "#f59e0b"
        bg_gradient = "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)"
    else:
        score_color = "#dc2626"
        bg_gradient = "linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)"
    
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                # คะแนนเครดิตขนาดใหญ่
                dbc.Col([
                    html.Div([
                        html.Div("คะแนนเครดิต", className="text-white mb-2", 
                                style={"fontSize": "14px", "fontFamily": "Sarabun", "letterSpacing": "0.5px", "opacity": "0.9"}),
                        html.Div([
                            html.Span(str(score), className="display-1 fw-bold text-white mb-0",
                                     style={"fontFamily": "Sarabun", "fontSize": "72px", "lineHeight": "1"}),
                            html.Div([
                                html.Span("/ 850", className="text-white ms-2", 
                                         style={"fontSize": "18px", "fontFamily": "Sarabun", "opacity": "0.8"})
                            ], className="d-inline-block align-bottom mb-3")
                        ]),
                        html.Div([
                            dbc.Badge(f"เรตติ้ง: {rating}", color="light", text_color="dark",
                                     className="px-3 py-2 me-2", 
                                     style={"fontSize": "13px", "fontWeight": "600"}),
                            get_risk_badge(score)
                        ], className="mt-3")
                    ], className="text-center")
                ], width=12, md=4, className="border-end border-white border-opacity-25"),
                
                # ข้อมูลเพิ่มเติม
                dbc.Col([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Small("ระดับความเสี่ยง", className="text-white d-block mb-2",
                                          style={"fontSize": "12px", "fontFamily": "Sarabun", "opacity": "0.9"}),
                                html.H5(data.get('risk_category', '-'), className="text-white fw-bold mb-0",
                                       style={"fontFamily": "Sarabun", "fontSize": "18px"})
                            ])
                        ], width=6, className="mb-3"),
                        dbc.Col([
                            html.Div([
                                html.Small("ช่วงคะแนน", className="text-white d-block mb-2",
                                          style={"fontSize": "12px", "fontFamily": "Sarabun", "opacity": "0.9"}),
                                html.H5(data.get('score_range', '-'), className="text-white fw-bold mb-0",
                                       style={"fontFamily": "Sarabun", "fontSize": "18px"})
                            ])
                        ], width=6, className="mb-3"),
                    ])
                ], width=12, md=8)
            ], className="align-items-center")
        ], className="p-4 p-md-5")
    ], className="mb-4 shadow-lg border-0", 
       style={"background": bg_gradient, "borderRadius": "20px"})
def create_recommendation_card_modern(data):
    """สร้างการ์ดคำแนะนำการอนุมัติแบบทันสมัย"""
    score = data.get('credit_score', 0)
    income = data.get('monthly_income', 0)
    
    if score >= 753:
        status = "แนะนำให้อนุมัติ"
        color = "success"
        icon = "check-circle-fill"
        multiplier = 5.0
        term_days = 1800  # 5 ปี
        term_text = "1,800 วัน (5 ปี)"
        term_reason = "ลูกค้ามีวินัยการเงินดีเยี่ยม สามารถให้ระยะเวลาผ่อนชำระยาวได้"
        advice = "ลูกค้ามีวินัยการเงินสูงมาก แนะนำเสนอวงเงินสูงสุดพร้อมอัตราดอกเบี้ยพิเศษ"
    elif score >= 681:
        status = "พิจารณาอนุมัติ"
        color = "primary"
        icon = "info-circle-fill"
        multiplier = 3.0
        term_days = 1080  # 3 ปี
        term_text = "1,080 วัน (3 ปี)"
        term_reason = "ลูกค้ามีความเสี่ยงปานกลาง แนะนำระยะเวลาปานกลางเพื่อสมดุลระหว่างสภาพคล่องและความเสี่ยง"
        advice = "ลูกค้ามีความเสี่ยงยอมรับได้ ควรตรวจสอบภาระหนี้ปัจจุบันประกอบการตัดสินใจ"
    elif score >= 616:
        status = "พิจารณาด้วยความระมัดระวัง"
        color = "warning"
        icon = "exclamation-triangle-fill"
        multiplier = 1.5
        term_days = 540  # 1.5 ปี
        term_text = "540 วัน (1.5 ปี)"
        term_reason = "ลูกค้ามีความเสี่ยงสูง แนะนำระยะเวลาสั้นเพื่อลดโอกาสการเปลี่ยนแปลงสถานะทางการเงิน"
        advice = "ลูกค้ามีความเสี่ยงค่อนข้างสูง แนะนำให้ขอเอกสารค้ำประกันหรือปรับลดวงเงิน"
    else:
        status = "ไม่แนะนำให้อนุมัติ"
        color = "danger"
        icon = "x-circle-fill"
        multiplier = 0
        term_days = 360  # 1 ปี
        term_text = "360 วัน (1 ปี) หากจำเป็นต้องอนุมัติ"
        term_reason = "ความเสี่ยงสูงมาก ควรให้ระยะเวลาสั้นที่สุดเพื่อลดโอกาสเป็นหนี้เสีย (NPL)"
        advice = "ลูกค้ามีประวัติค้างชำระหรือคะแนนต่ำเกินเกณฑ์มาตรฐาน ไม่แนะนำให้สร้างหนี้เพิ่ม"
    estimated_limit = income * multiplier
    return dbc.Card([
        dbc.CardBody([
            # Header
            html.Div([
                html.I(className=f"bi bi-{icon} me-2 text-{color}", style={"fontSize": "24px"}),
                html.Span("คำแนะนำการพิจารณาสินเชื่อ", className="fw-bold",
                         style={"fontSize": "18px", "fontFamily": "Sarabun"})
            ], className="d-flex align-items-center mb-4 pb-3 border-bottom"),
            
            # Status and Amount Row
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Small("สถานะการพิจารณา", className="text-muted d-block mb-2",
                                  style={"fontSize": "12px", "fontFamily": "Sarabun"}),
                        dbc.Badge(status, color=color, className="px-3 py-2",
                                 style={"fontSize": "14px", "fontWeight": "600"})
                    ])
                ], width=12, md=4, className="mb-3 mb-md-0"),
                
                dbc.Col([
                    html.Div([
                        html.Small("วงเงินกู้สูงสุดที่แนะนำ", className="text-muted d-block mb-2",
                                  style={"fontSize": "12px", "fontFamily": "Sarabun"}),
                        html.H4(f"฿{estimated_limit:,.2f}", className="text-dark fw-bold mb-0",
                               style={"fontFamily": "Sarabun", "fontSize": "24px"})
                    ])
                ], width=12, md=8)
            ], className="mb-3"),
            
            # Loan Term Row (NEW)
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.I(className="bi bi-calendar-range me-2 text-primary"),
                            html.Small("ระยะเวลาผ่อนชำระที่แนะนำ", className="text-muted d-inline",
                                      style={"fontSize": "12px", "fontFamily": "Sarabun"})
                        ], className="mb-2"),
                        html.H5(term_text, className="text-primary fw-bold mb-1",
                               style={"fontFamily": "Sarabun", "fontSize": "18px"}),
                        html.Small(term_reason, className="text-muted fst-italic",
                                  style={"fontSize": "11px", "fontFamily": "Sarabun"})
                    ], className="p-3 rounded-3", style={"backgroundColor": "#f8f9fa", "border": f"2px solid var(--bs-{color})", "borderLeft": f"5px solid var(--bs-{color})"})
                ], width=12)
            ], className="mb-3"),
            
            # Advice Box
            dbc.Alert([
                html.I(className="bi bi-lightbulb-fill me-2"),
                html.Span(advice, style={"fontSize": "13px", "fontFamily": "Sarabun"})
            ], color=color, className="mb-0", style={"borderRadius": "12px", "borderLeft": f"4px solid var(--bs-{color})"})
            
        ], className="p-4")
    ], className="mb-4 shadow-sm border-0", style={"borderRadius": "16px"})
def create_personal_info_card(data):
    """สร้างการ์ดข้อมูลส่วนบุคคล"""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="bi bi-person-fill me-2 text-primary"),
            html.Span("ข้อมูลส่วนบุคคล", className="fw-bold",
                     style={"fontSize": "16px", "fontFamily": "Sarabun"})
        ], className="bg-transparent border-0 pb-0 pt-3 px-4"),
        dbc.CardBody([
            create_info_row("รหัสลูกค้า", data.get('customer_id', '-'), "hash"),
            create_info_row("เลขบัตรประชาชน", data.get('national_id', '-'), "card-text"),
            create_info_row("ชื่อ-นามสกุล", data.get('borrower_name', '-'), "person-badge"),
            create_info_row("อายุ", format_value(data.get('age', '-'), 'age'), "calendar"),
            create_info_row("เพศ", data.get('gender', '-'), "gender-ambiguous"),
            create_info_row("ระดับการศึกษา", data.get('education', '-'), "mortarboard"),
            create_info_row("อาชีพ", data.get('occupation', '-'), "briefcase"),
            create_info_row("รายได้ต่อเดือน", format_value(data.get('monthly_income', '-'), 'monthly_income'), "currency-exchange"),
            create_info_row("เบอร์โทรศัพท์", data.get('phone_number', '-'), "telephone"),
        ], className="px-4 pb-4")
    ], className="shadow-sm border-0", style={"borderRadius": "16px"})
def create_loan_account_card(account, loan_num):
    """สร้างการ์ดข้อมูลบัญชีสินเชื่อ"""
    # สถานะบัญชี
    account_status = account.get('account_status', '-')
    if account_status == 'Active':
        status_badge = dbc.Badge("ใช้งานอยู่", color="success", className="px-2 py-1")
    elif account_status == 'Closed':
        status_badge = dbc.Badge("ปิดบัญชี", color="secondary", className="px-2 py-1")
    else:
        status_badge = dbc.Badge(account_status, color="warning", className="px-2 py-1")
    
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.Div([
                    html.I(className="bi bi-credit-card-fill me-2 text-primary"),
                    html.Span(f"บัญชีสินเชื่อ #{loan_num}", className="fw-bold",
                             style={"fontSize": "16px", "fontFamily": "Sarabun"})
                ]),
                status_badge
            ], className="d-flex justify-content-between align-items-center")
        ], className="bg-transparent border-0 pb-0 pt-3 px-4"),
        dbc.CardBody([
            # ข้อมูลสินเชื่อ
            html.Div([
                html.Small("รายละเอียดสินเชื่อ", className="text-primary fw-bold d-block mb-3",
                          style={"fontSize": "13px", "fontFamily": "Sarabun"}),
                create_info_row("เลขที่บัญชี", account.get('account_number', '-')),
                create_info_row("ประเภทสินเชื่อ", account.get('product_type', '-')),
                create_info_row("วงเงินอนุมัติ", format_value(account.get('credit_limit', '-'), 'credit_limit')),
                create_info_row("ยอดหนี้คงเหลือ", format_value(account.get('outstanding_balance', '-'), 'outstanding_balance')),
                create_info_row("ยอดผ่อนต่อเดือน", format_value(account.get('monthly_payment', '-'), 'monthly_payment')),
            ], className="mb-4"),
            
            # ประวัติการชำระ
            html.Div([
                html.Small("ประวัติการชำระและพฤติกรรม", className="text-primary fw-bold d-block mb-3",
                          style={"fontSize": "13px", "fontFamily": "Sarabun"}),
                create_info_row("ชำระตรงเวลา", format_value(account.get('payment_performance_pct', '-'), 'payment_performance_pct')),
                create_info_row("จำนวนงวดที่ค้าง", format_value(account.get('installments_overdue', '-'), 'installments_overdue')),
                create_info_row("วันที่ค้างชำระ (DPD)", format_value(account.get('days_past_due', '-'), 'days_past_due')),
                create_info_row("ยอดเงินค้างชำระ", format_value(account.get('overdue_amount', '-'), 'overdue_amount')),
                create_info_row("ค้างใน 12 เดือน", format_value(account.get('late_payment_count_12m', '-'), 'late_payment_count_12m')),
                create_info_row("ค้างใน 24 เดือน", format_value(account.get('late_payment_count_24m', '-'), 'late_payment_count_24m')),
                create_info_row("อัตราใช้วงเงิน", format_value(account.get('credit_utilization_rate', '-'), 'credit_utilization_rate')),
            ])
        ], className="px-4 pb-4")
    ], className="shadow-sm border-0 mb-3", style={"borderRadius": "16px"})
def create_member_detail_table(data):
    return html.Div([

        create_credit_score_hero(data),
        create_recommendation_card_modern(data),

        dbc.Tabs(
            [
                dbc.Tab(
                    label="ข้อมูลส่วนตัว",
                    tab_id="tab-personal"
                ),

                *[
                    dbc.Tab(
                        label=f"สินเชื่อ {i + 1}",
                        tab_id=f"tab-loan-{i + 1}"
                    )
                    for i in range(len(data.get("accounts", [])[:3]))
                ],
            ],
            id="member-detail-tabs",
            active_tab=None,
            className="mb-4"
        ),

        # 👇 content จะมาแสดงตรงนี้เมื่อคลิก
        html.Div(id="member-tab-content")
    ])

# ==================================================
# 3. Main Layout - Modern Design
# ==================================================
layout = dbc.Container([
    # Search Page
    html.Div([
        dbc.Row([
            dbc.Col([
                # Header Section
                html.Div([
                    html.Div([
                        html.I(className="bi bi-shield-check text-primary mb-3", 
                              style={"fontSize": "48px"}),
                        html.H1("ระบบตรวจสอบเครดิต", className="fw-bold mb-2", 
                               style={"fontFamily": "Sarabun", "fontSize": "42px", "color": "#1e293b", "marginTop": "80px"}),
                        html.P("ตรวจสอบข้อมูลสมาชิกและประเมินคุณสมบัติทางการเงิน",
                              className="text-muted mb-5",
                              style={"fontFamily": "Sarabun", "fontSize": "16px"})
                    ], className="text-center mb-5"),
                    
                    # Search Box
                    dbc.Card([
                        dbc.CardBody([
                            html.Label("เลขบัตรประชาชน", className="fw-bold mb-3",
                                      style={"fontFamily": "Sarabun", "fontSize": "14px", "color": "#64748b"}),
                            dbc.InputGroup([
                                dbc.InputGroupText(
                                    html.I(className="bi bi-search"),
                                    style={
                                        "backgroundColor": "#f8fafc",
                                        "border": "none",
                                        "borderRadius": "12px 0 0 12px"
                                    }
                                ),
                                dbc.Input(
                                    id="national-id-input",
                                    placeholder="กรอกเลขบัตรประชาชน 13 หลัก",
                                    type="text",
                                    style={
                                        "fontFamily": "Sarabun",
                                        "fontSize": "16px",
                                        "border": "none",
                                        "backgroundColor": "#f8fafc",
                                        "paddingLeft": "0"
                                    }
                                ),
                                dbc.Button(
                                    [html.I(className="bi bi-search me-2"), "ค้นหา"],
                                    id="search-btn",
                                    color="primary",
                                    style={
                                        "fontFamily": "Sarabun",
                                        "fontSize": "16px",
                                        "fontWeight": "600",
                                        "borderRadius": "0 12px 12px 0",
                                        "padding": "12px 32px"
                                    }
                                )
                            ], style={
                                "backgroundColor": "#f8fafc",
                                "borderRadius": "12px",
                                "padding": "8px"
                            })
                        ], className="p-4")
                    ], className="shadow-sm border-0", style={"borderRadius": "20px"}),
                    
                    # Search Result
                    html.Div(id="member-name-display", className="mt-4")
                    
                ], style={"maxWidth": "700px", "margin": "0 auto"})
            ], width=12)
        ], justify="center")
    ], id="search-page", style={"minHeight": "100vh", "paddingBottom": "100px"}),
    # Detail Page
    html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.I(className="bi bi-file-earmark-text text-primary me-2", style={"fontSize": "24px"}),
                    html.H3("รายงานข้อมูลเครดิตเชิงลึก", className="fw-bold mb-0 d-inline-block",
                           style={"fontFamily": "Sarabun", "color": "#1e293b"})
                ], className="d-flex align-items-center mb-4"),
                html.Div(id="detail-content")
            ], width=12)
        ])
    ], id="detail-page", style={
        "display": "none",
        "padding": "40px 20px",
        "minHeight": "100vh"
    })
], fluid=True, style={"minHeight": "100vh", "fontFamily": "Sarabun", "padding": "0"})
# ==================================================
# 4. Callbacks
# ==================================================
def register_callbacks(app):
    # 1. จัดการการค้นหาสมาชิก (เหมือนเดิม)
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
            content = dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.I(className="bi bi-person-check-fill text-success me-2", style={"fontSize": "24px"}),
                                html.Div([
                                    html.Small("พบข้อมูลสมาชิก", className="text-muted d-block", style={"fontSize": "12px", "fontFamily": "Sarabun"}),
                                    html.H5(data.get('borrower_name'), className="mb-0 fw-bold", style={"fontFamily": "Sarabun", "fontSize": "18px"})
                                ], className="d-inline-block")
                            ], className="d-flex align-items-center")
                        ], width=12, md=7),
                        dbc.Col([
                            dbc.Button(
                                [html.I(className="bi bi-file-text me-2"), "ดูรายงานเครดิต"],
                                id="view-detail-btn", color="primary", className="w-100",
                                style={"fontFamily": "Sarabun", "borderRadius": "10px", "padding": "12px 24px", "fontSize": "15px", "fontWeight": "600"}
                            )
                        ], width=12, md=5, className="mt-3 mt-md-0")
                    ], className="align-items-center")
                ], className="p-4")
            ], className="shadow-sm border-0 mt-4", style={"borderRadius": "16px"})
            
            return content, search_page_style, detail_page_style
            
        return dbc.Alert("ไม่พบข้อมูลสมาชิกในระบบ", color="danger", className="mt-4"), search_page_style, detail_page_style

    # 2. จัดการการเปลี่ยนหน้าไปยังรายงาน (เหมือนเดิม)
    @app.callback(
        [Output("search-page", "style", allow_duplicate=True),
         Output("detail-page", "style", allow_duplicate=True),
         Output("detail-content", "children")],
        Input("view-detail-btn", "n_clicks"),
        State("national-id-input", "value"),
        prevent_initial_call=True
    )
    def show_detail_page(n, nid):
        if n and nid:
            data = get_member_profile(nid)
            if data:
                return {"display": "none"}, {"display": "block", "padding": "40px 20px"}, create_member_detail_table(data)
        return dash.no_update, dash.no_update, dash.no_update

    # 3. 🔥 ใหม่: จัดการการแสดงผลเนื้อหาในแต่ละ Tab
    @app.callback(
        Output("member-tab-content", "children"),
        [Input("member-detail-tabs", "active_tab")],
        [State("national-id-input", "value")]
    )
    def render_tab_content(active_tab, nid):
        """ฟังก์ชันนี้จะทำงานเมื่อมีการคลิกที่ Tabs"""
        if not active_tab or not nid:
            # ถ้ายังไม่ได้เลือกอะไรเลย ให้แสดงคำแนะนำ
            return html.Div([
                html.I(className="bi bi-arrow-up-circle d-block mb-2", style={"fontSize": "32px", "color": "#0d6efd"}),
                "กรุณาคลิกเลือกหัวข้อด้านบนเพื่อดูรายละเอียด"
            ], className="text-center p-5 text-muted bg-white border rounded-3 mt-2", style={"fontFamily": "Sarabun"})

        data = get_member_profile(nid)
        if not data:
            return "ไม่พบข้อมูล"

        if active_tab == "tab-personal":
            return create_personal_info_card(data)

        if "tab-loan-" in active_tab:
            # ดึงลำดับของบัญชีจาก id (เช่น tab-loan-1 -> index 0)
            try:
                loan_index = int(active_tab.split("-")[-1]) - 1
                accounts = data.get("accounts", [])
                if loan_index < len(accounts):
                    return create_loan_account_card(accounts[loan_index], loan_index + 1)
            except:
                pass
        
        return html.Div("ไม่พบข้อมูลในส่วนนี้")

