import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd

from ..data_manager import get_member_profile

# ==================================================
# Helper Functions
# ==================================================

def format_value(val, key):
    """ฟังก์ชันจัดการหน่วยให้ตรงตาม Schema credit_scoring"""
    if val == "-" or val is None or val == "":
        return "-"
    
    # 1. ยกเว้น 'เลขที่บัญชี' (account_number) แสดงเป็นข้อความดิบๆ
    if key == "account_number":
        return str(val)

    # 2. กลุ่มเปอร์เซ็นต์ (%) - ดักจับคำว่า pct หรือ rate (เช่น credit_utilization_rate)
    if any(x in key for x in ["pct", "rate"]):
        try:
            return f"{float(val):,.2f} %"
        except:
            return val

    # 3. กลุ่มเงินบาท (สำคัญ!) - ดักจับคำว่า amount (เช่น overdue_amount), income, balance, limit, payment
    if any(x in key for x in ["amount", "income", "balance", "limit", "payment", "approved", "value"]):
        try:
            return f"{float(val):,.2f} บาท"
        except:
            return val

    # 4. กลุ่มระยะเวลา (วัน)
    if "days" in key:
        try:
            return f"{int(float(val))} วัน"
        except:
            return val

    # 5. กลุ่มจำนวน (งวด/ครั้ง/บัญชี) - ดักจับคำว่า count, overdue (ที่ไม่ใช่ amount), installments, accounts
    if any(x in key for x in ["count", "overdue", "installments", "accounts", "months", "inquiries"]):
        try:
            return f"{int(float(val))} งวด/ครั้ง"
        except:
            return val
            
    return val

def create_member_detail_table(data):
    """สร้างตารางข้อมูลแยกหมวดหมู่โดยรวมคอลัมน์พฤติกรรมการชำระเงินทั้งหมด"""
    groups = [
        ("ข้อมูลส่วนบุคคล", [
            ("รหัสลูกค้า", "customer_id"), 
            ("เลขบัตรประชาชน", "national_id"),
            ("ชื่อผู้กู้", "borrower_name"), 
            ("อายุ", "age"), 
            ("เพศ", "gender"),
            ("ระดับการศึกษา", "education"), 
            ("อาชีพ", "occupation"), 
            ("รายได้ต่อเดือน", "monthly_income"),
            ("เบอร์โทรศัพท์", "phone_number"),
            ("ที่อยู่", "address_detail")
        ]),
        ("รายละเอียดสินเชื่อ", [
            ("เลขที่บัญชี", "account_number"), 
            ("ประเภทสินเชื่อ", "product_type"),
            ("วงเงินอนุมัติ", "credit_limit"),
            ("ยอดหนี้คงเหลือ", "outstanding_balance"), 
            ("ยอดผ่อนต่อเดือน", "monthly_payment"), 
            ("สถานะบัญชี", "account_status")
        ]),
        ("ประวัติการชำระและพฤติกรรม", [
            ("ชำระตรงเวลา (%)", "payment_performance_pct"),
            ("จำนวนงวดที่ค้าง", "installments_overdue"),
            ("จำนวนวันที่ค้างชำระ (DPD)", "days_past_due"),
            ("ยอดเงินค้างชำระ", "overdue_amount"),
            ("ค้างชำระในรอบ 12 เดือน", "late_payment_count_12m"),
            ("ค้างชำระในรอบ 24 เดือน", "late_payment_count_24m"),
            ("อัตราใช้วงเงิน (%)", "credit_utilization_rate"),
            ("จำนวนบัญชีทั้งหมด", "total_accounts")
        ]),
        ("ผลการประเมินเครดิต", [
            ("คะแนนเครดิต", "credit_score"), 
            ("เรตติ้ง", "credit_rating"),
            ("ระดับความเสี่ยง", "risk_category"),
            ("ช่วงคะแนน", "score_range")
        ])
    ]
    
    content = []
    for group_name, fields in groups:
        content.append(html.Tr([
            html.Td(html.H6(group_name, className="text-primary fw-bold mt-3 mb-1 border-bottom pb-1"), colSpan=2, className="border-0")
        ]))
        
        for label, key in fields:
            val = format_value(data.get(key, "-"), key)
            content.append(html.Tr([
                html.Td(label, className="text-muted border-0 ps-3 py-1", style={"width": "45%", "fontSize": "0.9rem"}),
                html.Td(html.B(val, className="fw-bold"), className="border-0 py-1", style={"fontSize": "0.9rem"})
            ]))
            
    return html.Div([
        dbc.Table(html.Tbody(content), borderless=True, hover=True, size="sm", className="m-0"),
    ], id="pdf-content-area", style={"padding": "10px 30px", "backgroundColor": "white"})

# ==================================================
# Layout
# ==================================================

layout = dbc.Container([
    # หน้าค้นหา
    html.Div([
        dbc.Row([
            dbc.Col([
                html.H3("Member Verification", className="fw-light text-secondary mt-5 mb-1"),
                html.H2("ตรวจสอบข้อมูลเครดิตสมาชิก", className="fw-bold mb-4"),
            ], width=12, className="text-center")
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.P("ระบุเลขบัตรประชาชน 13 หลัก", className="text-muted mb-3 small text-center"),
                        dbc.InputGroup([
                            dbc.Input(id="national-id-input", placeholder="0-0000-00000-00-0", type="text", className="py-2"),
                            dbc.Button([html.I(className="fas fa-search me-2"), "ค้นหา"], id="search-btn", color="dark"),
                        ]),
                        html.Div(id="member-name-display", className="mt-4")
                    ], className="p-4")
                ], className="shadow-sm border-0", style={"borderRadius": "15px"})
            ], width={"size": 6, "offset": 3})
        ]),
    ], id="search-page", style={"display": "block"}),

    # หน้าแสดงรายละเอียด
    html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.H4("ประวัติส่วนตัว", className="fw-bold mb-0"),
                            dbc.Button([html.I(className="fas fa-file-pdf me-2"), "ดาวน์โหลด PDF"], 
                                     id="download-pdf-btn", color="danger", className="rounded-pill btn-sm"),
                        ], className="d-flex justify-content-between align-items-center")
                    ], className="bg-light"),
                    dbc.CardBody(id="detail-content", className="px-0"),
                ], className="shadow-sm border-0", style={"borderRadius": "15px"})
            ], width=12)
        ]),
    ], id="detail-page", style={"display": "none"}),

    html.Div(id="pdf-script-output", style={"display": "none"}),
    dcc.Store(id="current-national-id", data=None)
], fluid=True)

# ==================================================
# Callbacks
# ==================================================

def register_callbacks(app):
    @app.callback(
        Output("member-name-display", "children"),
        Input("search-btn", "n_clicks"),
        State("national-id-input", "value"),
        prevent_initial_call=True
    )
    def handle_search(n_clicks, national_id):
        if not national_id: return ""
        data = get_member_profile(national_id)
        if data and data.get('borrower_name'):
            return html.Div([
                html.Div([
                    html.H4(data.get('borrower_name'), className="mb-0 fw-bold"),
                    dbc.Button("ดูประวัติและเครดิต", id="view-detail-btn", color="primary", outline=True, className="rounded-pill btn-sm")
                ], className="d-flex justify-content-between align-items-center p-3 rounded-3", style={"backgroundColor": "#f8f9fa"})
            ])
        return dbc.Alert("ไม่พบข้อมูล", color="danger", className="mt-3")

    @app.callback(
        [Output("search-page", "style"), 
         Output("detail-page", "style"),
         Output("detail-content", "children"),
         Output("current-national-id", "data")],
        Input("view-detail-btn", "n_clicks"),  
        State("national-id-input", "value"),
        prevent_initial_call=True
    )
    def toggle_pages(n_view, national_id):
        if n_view:
            data = get_member_profile(national_id)
            if data:
                return ({"display": "none"}, {"display": "block"}, create_member_detail_table(data), national_id)
        return {"display": "block"}, {"display": "none"}, dash.no_update, dash.no_update

    app.clientside_callback(
        "window.dash_clientside.clientside.pdf_gen",
        Output("pdf-script-output", "children"),
        Input("download-pdf-btn", "n_clicks"),
        prevent_initial_call=True
    )