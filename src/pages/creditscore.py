import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

from ..data_manager import get_member_profile

# ==================================================
# Helper Functions
# ==================================================

def create_member_detail_table(data):
    """สร้างตารางข้อมูลแยกหมวดหมู่เพื่อให้ดูเป็นระเบียบและครบถ้วน"""
    
    # กำหนดกลุ่มข้อมูล
    groups = [
        ("ข้อมูลส่วนบุคคล", [
            ("รหัสลูกค้า", "customer_id"), ("เลขบัตรประชาชน", "national_id"),
            ("ชื่อผู้กู้", "borrower_name"), ("อายุ", "age"), ("เพศ", "gender"),
            ("ระดับการศึกษา", "education"), ("อาชีพ", "occupation"), ("รายได้ต่อเดือน", "monthly_income")
        ]),
        ("รายละเอียดสินเชื่อ", [
            ("เลขที่บัญชี", "account_number"), ("ประเภทสินเชื่อ", "product_type"),
            ("วงเงินอนุมัติ", "approved_amount"), ("ยอดหนี้คงเหลือ", "outstanding_balance"),
            ("ยอดผ่อนต่อเดือน", "monthly_payment"), ("สถานะบัญชี", "account_status")
        ]),
        ("ประวัติการชำระและพฤติกรรม", [
            ("ชำระตรงเวลา (%)", "payment_performance_pct"),
            ("จำนวนงวดที่ค้าง", "installments_overdue"),
            ("อัตราใช้วงเงิน (%)", "credit_utilization_rate"),
            ("จำนวนบัญชีทั้งหมด", "total_accounts")
        ]),
        ("ผลการประเมินเครดิต", [
            ("คะแนนเครดิต", "credit_score"), ("เรตติ้ง", "credit_rating"),
            ("วันที่ออกรายงาน", "report_date")
        ])
    ]
    
    content = []
    for group_name, fields in groups:
        # หัวข้อหมวดหมู่
        content.append(html.Tr([
            html.Td(html.H6(group_name, className="text-primary fw-bold mt-3 mb-1"), colSpan=2, className="border-0")
        ]))
        
        # ข้อมูลในหมวดหมู่
        for label, key in fields:
            val = data.get(key, "-")
            if any(x in key for x in ["income", "amount", "balance", "payment", "limit"]):
                try: val = f"{float(val):,.2f} บาท"
                except: pass
            
            content.append(html.Tr([
                html.Td(label, className="text-muted border-0 ps-4", style={"width": "45%"}),
                html.Td(html.B(val), className="border-0")
            ]))
            
    return dbc.Table(html.Tbody(content), borderless=True, hover=True, className="my-2")

# ==================================================
# Layout (Minimalist Style)
# ==================================================

layout = dbc.Container([
    # ส่วนหัวข้อ
    dbc.Row([
        dbc.Col([
            html.H3("Member Verification", className="fw-light text-secondary mt-5 mb-1"),
            html.H2("ตรวจสอบข้อมูลเครดิตสมาชิก", className="fw-bold mb-4"),
        ], width=12, className="text-center")
    ]),
    
    # การ์ดค้นหา (Shadow Soft)
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("ระบุเลขบัตรประชาชน 13 หลัก เพื่อเรียกดูประวัติสมาชิก", 
                           className="text-muted mb-3 small text-center"),
                    dbc.InputGroup([
                        dbc.Input(
                            id="national-id-input", 
                            placeholder="0-0000-00000-00-0", 
                            type="text",
                            className="border-end-0 py-2",
                            style={"borderRadius": "10px 0 0 10px"}
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-search me-2"), "ค้นหา"], 
                            id="search-btn", 
                            color="dark", 
                            className="px-4",
                            style={"borderRadius": "0 10px 10px 0"}
                        ),
                    ], className="mb-2"),
                    
                    # พื้นที่แสดงผลลัพธ์
                    html.Div(id="member-name-display", className="mt-4")
                ], className="p-4")
            ], className="shadow-sm border-0", style={"borderRadius": "15px"})
        ], width={"size": 6, "offset": 3})
    ]),

    # Modal (รายละเอียด)
    dbc.Modal([
        dbc.ModalHeader(
            dbc.ModalTitle("Member Profile Detail", className="fw-bold"),
            close_button=True,
            className="border-0 ps-4 pt-4"
        ),
        dbc.ModalBody(id="modal-member-detail-content", className="px-0"),
        dbc.ModalFooter(
            dbc.Button("ปิดหน้าต่าง", id="close-modal-btn", color="light", className="px-4"),
            className="border-0"
        ),
    ], id="member-detail-modal", size="lg", centered=True, style={"borderRadius": "15px"}),

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
        if not national_id:
            return ""
        
        data = get_member_profile(national_id)
        
        if data and data.get('borrower_name'):
            return html.Div([
                html.Hr(className="opacity-10 mb-4"),
                html.Div([
                    html.Div([
                        html.Small("พบข้อมูลสมาชิก", className="text-success d-block mb-1 fw-bold"),
                        html.H4(data.get('borrower_name'), className="mb-0 fw-bold"),
                    ]),
                    dbc.Button(
                        "ดูประวัติโดยละเอียด", 
                        id="open-modal-link",
                        color="primary", 
                        outline=True,
                        className="rounded-pill px-4 btn-sm"
                    )
                ], className="d-flex justify-content-between align-items-center p-3 rounded-3", 
                   style={"backgroundColor": "#f8f9fa"})
            ])
        else:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-circle me-2"),
                "ไม่พบเลขบัตรประชาชนนี้ในระบบ กรุณาลองใหม่อีกครั้ง"
            ], color="danger", className="border-0 shadow-none rounded-3 mt-3")

    @app.callback(
        [Output("member-detail-modal", "is_open"),
         Output("modal-member-detail-content", "children")],
        [Input("open-modal-link", "n_clicks"),
         Input("close-modal-btn", "n_clicks")],
        [State("national-id-input", "value"),
         State("member-detail-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_modal(n_open, n_close, national_id, is_open):
        ctx = dash.callback_context
        if not ctx.triggered:
            return is_open, dash.no_update
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == "open-modal-link" and n_open:
            data = get_member_profile(national_id)
            if data:
                return True, create_member_detail_table(data)
        
        return False, dash.no_update