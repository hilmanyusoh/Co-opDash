# layout_home.py

from dash import dcc, html
import dash_bootstrap_components as dbc
# เปลี่ยนจาก 'from .data_manager' เป็น 'from data_manager'
from data_manager import get_mongo_client 

def render_home_tab():
    """สร้างเนื้อหาสำหรับหน้า Home/Create"""
    
    client_status = False
    member_count = 0
    
    # ดึงสถานะการเชื่อมต่อและนับจำนวนเอกสาร
    try:
        client, client_status = get_mongo_client()
        if client_status:
            db = client["members_db"] # ใช้ชื่อ DB ที่กำหนดใน data_manager
            collection = db["members"] # ใช้ชื่อ Collection ที่กำหนดใน data_manager
            member_count = collection.count_documents({})
    except Exception:
        pass # ถ้าเกิดข้อผิดพลาดในการเชื่อมต่อ/นับ ให้สถานะเป็น False

    form_layout = html.Div([
        # Row 1: รหัสสมาชิก
        dbc.Row([
            dbc.Col(html.Div("รหัสสมาชิก*", className="form-label"), md=12),
        ]),
        dbc.Row([
            dbc.Col(dbc.Input(id='member-id', type='text', placeholder='เช่น 100456', required=True), md=4),
        ], className="mb-3"),
        
        # Row 2: คำนำหน้าชื่อ, ชื่อ, นามสกุล
        dbc.Row([
            dbc.Col(html.Div("คำนำหน้า*", className="form-label"), md=2),
            dbc.Col(html.Div("ชื่อ*", className="form-label"), md=5),
            dbc.Col(html.Div("นามสกุล*", className="form-label"), md=5),
        ]),
        dbc.Row([
            dbc.Col(
                dbc.Select(
                    id='member-prefix', 
                    options=[
                        {"label": "นาย", "value": "นาย"},
                        {"label": "นาง", "value": "นาง"},
                        {"label": "นางสาว", "value": "นางสาว"},
                        {"label": "อื่นๆ", "value": "อื่นๆ"},
                    ],
                    value="นาย", 
                    required=True
                ), 
                md=2
            ),
            dbc.Col(dbc.Input(id='member-name', type='text', placeholder='ชื่อจริง', required=True), md=5),
            dbc.Col(dbc.Input(id='member-surname', type='text', placeholder='นามสกุล', required=True), md=5),
        ], className="mb-3"),

        # Row 3: ว/ด/ป เกิด, อายุ (คำนวณ), รายได้
        dbc.Row([
            dbc.Col(html.Div("ว/ด/ป เกิด (DD/MM/YYYY)*", className="form-label"), md=3),
            dbc.Col(html.Div("อายุ (คำนวณ)", className="form-label"), md=3),
            dbc.Col(html.Div("รายได้ (บาท)*", className="form-label"), md=6),
        ]),
        dbc.Row([
            dbc.Col(dbc.Input(id='member-dob', type='text', placeholder='15/05/1990', required=True), md=3),
            dbc.Col(html.Div(id='member-age-display', children="--", 
                             className='p-2 bg-light border rounded text-center text-primary font-bold'), md=3),
            dbc.Col(dbc.Input(id='member-income', type='text', placeholder='ตัวเลขเท่านั้น (เช่น 45000)', required=True), md=6),
        ], className="mb-3"),

        # Row 4: อาชีพ, รหัสสาขา
        dbc.Row([
            dbc.Col(html.Div("อาชีพ", className="form-label"), md=6),
            dbc.Col(html.Div("รหัสสาขา", className="form-label"), md=6),
        ]),
        dbc.Row([
            dbc.Col(dbc.Input(id='member-occupation', type='text', placeholder='อาชีพปัจจุบัน'), md=6),
            dbc.Col(dbc.Input(id='member-branch', type='text', placeholder='รหัสสาขา'), md=6),
        ], className="mb-3"),

        # Row 5: วันที่สมัคร, วันที่อนุมัติ, ปุ่มบันทึก
        dbc.Row([
            dbc.Col(html.Div("วันที่สมัคร (DD/MM/YYYY)", className="form-label"), md=4),
            dbc.Col(html.Div("วันที่อนุมัติ (DD/MM/YYYY)", className="form-label"), md=4),
            dbc.Col(html.Div(), md=4), 
        ]),
        dbc.Row([
            dbc.Col(dbc.Input(id='member-regdate', type='text', placeholder='วันที่สมัคร'), md=4),
            dbc.Col(dbc.Input(id='member-apprdate', type='text', placeholder='วันที่อนุมัติ'), md=4),
            dbc.Col(
                dbc.Button('บันทึกข้อมูลสมาชิก', id='submit-button', color='primary', className='w-100'),
                md=4,
                className="d-grid gap-2" 
            ),
        ], className="mb-4"),
        
        html.Div(id='output-message', className="mt-3")
    ], className="p-4 border rounded shadow-lg bg-light")


    return html.Div(
        children=[
            html.H2(" บันทึกข้อมูลสมาชิกใหม่ (Create New Record)", className="text-primary"),
            html.Hr(className="mb-4"),
            dbc.Alert(
                f"สถานะ: {'✅ เชื่อมต่อ MongoDB สำเร็จ' if client_status else '❌ ไม่สามารถเชื่อมต่อ MongoDB ได้'} | จำนวนเอกสาร: {member_count:,} รายการ",
                color="success" if client_status else "danger",
            ),
            html.H4("กรอกรายละเอียดสมาชิก", className="mt-4"),
            form_layout
        ]
    )