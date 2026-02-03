import dash
from dash import dcc, html, Input, Output, State, callback, ClientsideFunction
import dash_bootstrap_components as dbc
import pandas as pd

from ..data_manager import get_member_profile

# ==================================================
# Helper Functions
# ==================================================

def create_member_detail_table(data):
    """สร้างตารางข้อมูลแยกหมวดหมู่เพื่อให้ดูเป็นระเบียบและครบถ้วน"""
    groups = [
        ("ข้อมูลส่วนบุคคล", [
            ("รหัสลูกค้า", "customer_id"), ("เลขบัตรประชาชน", "national_id"),
            ("ชื่อผู้กู้", "borrower_name"), ("อายุ", "age"), ("เพศ", "gender"),
            ("ระดับการศึกษา", "education"), ("อาชีพ", "occupation"), ("รายได้ต่อเดือน", "monthly_income")
        ]),
        ("รายละเอียดสินเชื่อ", [
            ("เลขที่บัญชี", "account_number"), ("ประเภทสินเชื่อ", "product_type"),
            ("ยอดหนี้คงเหลือ", "outstanding_balance"), ("ยอดผ่อนต่อเดือน", "monthly_payment"), 
            ("สถานะบัญชี", "account_status")
        ]),
        ("ประวัติการชำระและพฤติกรรม", [
            ("ชำระตรงเวลา (%)", "payment_performance_pct"),
            ("จำนวนงวดที่ค้าง", "installments_overdue"),
            ("อัตราใช้วงเงิน (%)", "credit_utilization_rate"),
            ("จำนวนบัญชีทั้งหมด", "total_accounts")
        ]),
        ("ผลการประเมินเครดิต", [
            ("คะแนนเครดิต", "credit_score"), ("เรตติ้ง", "credit_rating"),
            ("ระดับความเสี่ยง", "risk_category")
        ])
    ]
    
    content = []
    for group_name, fields in groups:
        content.append(html.Tr([
            html.Td(html.H6(group_name, className="text-primary fw-bold mt-2 mb-0 small border-bottom pb-1"), colSpan=2, className="border-0")
        ]))
        
        for label, key in fields:
            val = data.get(key, "-")
            if any(x in key for x in ["income", "amount", "balance", "payment", "limit"]):
                try: val = f"{float(val):,.2f} บาท"
                except: pass
            
            content.append(html.Tr([
                html.Td(label, className="text-muted border-0 ps-3 small py-1", style={"width": "45%"}),
                html.Td(html.B(val,className="small fw-bold"), className="border-0 py-1")
            ]))
            
    # สำคัญ: ต้องครอบด้วย Div ที่มี ID 'pdf-content-area' เพื่อให้ JavaScript จับภาพได้
    return html.Div([
        dbc.Table(html.Tbody(content), borderless=True, hover=True, size="sm", className="m-0"),
    ], id="pdf-content-area", style={"padding": "10px 20px", "backgroundColor": "white"})

# ==================================================
# Layout
# ==================================================

layout = dbc.Container([
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

    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("ประวัติส่วนตัว", className="fw-bold"), close_button=True),
        dbc.ModalBody(id="modal-member-detail-content", className="px-0"),
        dbc.ModalFooter([
            dbc.Button([html.I(className="fas fa-file-pdf me-2"), "ดาวน์โหลด PDF"], 
                       id="download-pdf-btn", color="danger", className="me-auto rounded-pill"),
            dbc.Button("ปิด", id="close-modal-btn", color="light", className="rounded-pill"),
        ]),
    ], id="member-detail-modal", size="md", centered=True),

    html.Div(id="pdf-script-output", style={"display": "none"})
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
                    dbc.Button("ดูประวัติและเครดิต", id="open-modal-link", color="primary", outline=True, className="rounded-pill btn-sm")
                ], className="d-flex justify-content-between align-items-center p-3 rounded-3", style={"backgroundColor": "#f8f9fa"})
            ])
        return dbc.Alert("ไม่พบข้อมูล", color="danger", className="mt-3")

    @app.callback(
        [Output("member-detail-modal", "is_open"), Output("modal-member-detail-content", "children")],
        [Input("open-modal-link", "n_clicks"), Input("close-modal-btn", "n_clicks")],
        [State("national-id-input", "value"), State("member-detail-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_modal(n_open, n_close, national_id, is_open):
        ctx = dash.callback_context
        if not ctx.triggered: return is_open, dash.no_update
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == "open-modal-link" and n_open:
            data = get_member_profile(national_id)
            if data: return True, create_member_detail_table(data)
        return False, dash.no_update

    # --- Clientside Callback ที่แก้ปัญหา 'jsPDF undefined' ---
    app.clientside_callback(
        """
        async function(n_clicks) {
            if (!n_clicks) return null;

            const loadScript = (src) => {
                return new Promise((resolve, reject) => {
                    if (document.querySelector(`script[src="${src}"]`)) return resolve();
                    const script = document.createElement('script');
                    script.src = src;
                    script.onload = resolve;
                    script.onerror = reject;
                    document.head.appendChild(script);
                });
            };

            try {
                // โหลด Library ทันทีที่กดปุ่ม
                await loadScript("https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js");
                await loadScript("https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js");

                const element = document.getElementById('pdf-content-area');
                if (!element) return null;

                // ตรวจสอบตัวแปร jsPDF จากหลายๆ ชื่อที่เป็นไปได้
                const jspdfLib = window.jspdf || window.jspdf_umd;
                const jsPDF = jspdfLib ? jspdfLib.jsPDF : window.jsPDF;
                
                if (!jsPDF) throw new Error("Library jsPDF not found");

                const canvas = await html2canvas(element, { scale: 2 });
                const imgData = canvas.toDataURL('image/png');
                const pdf = new jsPDF('p', 'mm', 'a4');
                const pdfWidth = pdf.internal.pageSize.getWidth();
                const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
                
                pdf.text("Credit Scoring Report", 15, 15);
                pdf.addImage(imgData, 'PNG', 0, 20, pdfWidth, pdfHeight);
                pdf.save("Credit_Report.pdf");
            } catch (err) {
                alert("PDF Error: " + err.message);
            }
            return null;
        }
        """,
        Output("pdf-script-output", "children"),
        Input("download-pdf-btn", "n_clicks"),
        prevent_initial_call=True
    )