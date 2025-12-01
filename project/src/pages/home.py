# src/pages/home.py

from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import datetime

from ..data_manager import get_mongo_client, calculate_age_from_dob, DB_NAME, COLLECTION_NAME


# Layout ของหน้า Home 
def create_home_layout():
    
    client_status = False
    member_count = 0
    
    try:
        client, client_status = get_mongo_client()
        if client_status:
            db = client[DB_NAME] 
            collection = db[COLLECTION_NAME] 
            member_count = collection.count_documents({})
    except Exception:
        pass 

    form_layout = html.Div([
        dbc.Row([dbc.Col(html.Div("รหัสสมาชิก*", className="form-label"), md=12),]),
       
        dbc.Row([dbc.Col(dbc.Input(id='member-id', 
                                   type='text', 
                                   placeholder='เช่น 100456', 
                                   required=True), md=4),], 
                className="mb-3"),
        
        dbc.Row([dbc.Col(html.Div("คำนำหน้า*", className="form-label"), md=2), 
                 dbc.Col(html.Div("ชื่อ*", className="form-label"), md=5), 
                 dbc.Col(html.Div("นามสกุล*", className="form-label"), md=5),]),
        dbc.Row([dbc.Col(dbc.Select(id='member-prefix', 
                                    options=[{"label": "นาย", "value": "นาย"}, 
                                             {"label": "นาง", "value": "นาง"}, 
                                             {"label": "นางสาว", "value": "นางสาว"}, 
                                             {"label": "อื่นๆ", "value": "อื่นๆ"},], 
                                    value="นาย", required=True), md=2), 
                 dbc.Col(dbc.Input(id='member-name', 
                                   type='text', 
                                   placeholder='ชื่อจริง', 
                                   required=True), md=5), 
                 
                 dbc.Col(dbc.Input(id='member-surname', 
                                   type='text', 
                                   placeholder='นามสกุล', 
                                   required=True), md=5),], 
                className="mb-3"),

        dbc.Row([dbc.Col(html.Div("ว/ด/ป เกิด (DD/MM/YYYY)*",className="form-label"), md=3), 
                 dbc.Col(html.Div("อายุ (คำนวณ)", className="form-label"), md=3), 
                 dbc.Col(html.Div("รายได้ (บาท)*", className="form-label"), md=6),]),
        
        dbc.Row([dbc.Col(dbc.Input(id='member-dob', type='text', placeholder='15/05/1990', required=True), md=3), 
                 dbc.Col(html.Div(id='member-age-display', children="--", 
                                  className='p-2 bg-light border rounded text-center text-primary font-bold'), md=3), 
                 dbc.Col(dbc.Input(id='member-income', 
                                   type='text', 
                                   placeholder='ตัวเลขเท่านั้น (เช่น 45000)', 
                                   required=True), md=6),], 
                className="mb-3"),

        dbc.Row([dbc.Col(html.Div("อาชีพ", className="form-label"), md=6), 
                 dbc.Col(html.Div("รหัสสาขา", className="form-label"), md=6),]),
        
        dbc.Row([dbc.Col(dbc.Input(id='member-occupation', 
                                   type='text', 
                                   placeholder='อาชีพปัจจุบัน'), md=6), 
                 dbc.Col(dbc.Input(id='member-branch', 
                                   type='text', 
                                   placeholder='รหัสสาขา'), md=6),], 
                className="mb-3"),

        dbc.Row([dbc.Col(html.Div("วันที่สมัคร (DD/MM/YYYY)",className="form-label"), md=4), 
                dbc.Col(html.Div("วันที่อนุมัติ (DD/MM/YYYY)",className="form-label"), md=4), 
                dbc.Col(html.Div(), md=4), ]),
        
        dbc.Row([dbc.Col(dbc.Input(
            id='member-regdate', 
            type='text', 
            placeholder='วันที่สมัคร'), 
                         md=4), 
                dbc.Col(dbc.Input(
                    id='member-apprdate', 
                    type='text', 
                    placeholder='วันที่อนุมัติ'), 
                        md=4), 
                dbc.Col(dbc.Button('บันทึกข้อมูลสมาชิก', 
                                   id='submit-button', 
                                   color='primary', 
                                   className='w-100'),md=4, 
                        className="d-grid gap-2"),], 
                className="mb-4"),
        
        html.Div(id='output-message', className="mt-3")
    ], className="p-4 border rounded shadow-lg bg-light")

    return html.Div(
        children=[
            html.H2(" บันทึกข้อมูลสมาชิกใหม่ ", className="text-primary"),
            html.Hr(className="mb-4"),
            dbc.Alert(
                f"{'เชื่อมต่อ MongoDB สำเร็จ' 
                
                if client_status else '❌ ไม่สามารถเชื่อมต่อ MongoDB ได้'} | จำนวนเอกสาร: {member_count:,} รายการ",
                color="success" if client_status else "danger",
            ),
            html.H4("กรอกรายละเอียดสมาชิก", className="mt-4"),
            form_layout
        ]
    )

layout = create_home_layout()


# Callbacks ของหน้า Home 
def register_callbacks(app):

    # Callback A: การคำนวณอายุแบบ Real-time
    @app.callback(
        Output('member-age-display', 'children'),
        [Input('member-dob', 'value')]
    )
    def update_age_display(dob_str):
        if not dob_str:
            return "--"
        age = calculate_age_from_dob(dob_str)
        return f"{int(age)} ปี" if pd.notna(age) else "รูปแบบวันที่ไม่ถูกต้อง"


    # Callback B: การจัดการ Submit Form
    @app.callback(
        Output('output-message', 'children'),
        [Input('submit-button', 'n_clicks')],
        [
            State('member-id', 'value'), 
            State('member-prefix', 'value'), 
            State('member-name', 'value'), 
            State('member-surname', 'value'), 
            State('member-dob', 'value'), 
            State('member-income', 'value'),
            State('member-occupation', 'value'), 
            State('member-branch', 'value'), 
            State('member-regdate', 'value'), 
            State('member-apprdate', 'value'),
        ]
    )
    def save_member_data(n_clicks, 
                         member_id, 
                         prefix, 
                         name, 
                         surname, 
                         dob, 
                         income, 
                         occupation, 
                         branch, 
                         reg_date, 
                         appr_date):
        if n_clicks is None: 
            return ""
        
        client, status = get_mongo_client()
        if not status: return dbc.Alert("❌ ไม่สามารถเชื่อมต่อ MongoDB เพื่อบันทึกข้อมูลได้", color="danger")

        # ตรวจสอบข้อมูลเบื้องต้น
        required_fields = {
            "รหัสสมาชิก": member_id, 
            "คำนำหน้า": prefix, 
            "ชื่อ": name, 
            "นามสกุล": surname, 
            "ว/ด/ป เกิด": dob, 
            "รายได้ (บาท)": income}
        missing_fields = [k for k, v in required_fields.items() if not v or str(v).strip() == ""]
        
        if missing_fields: 
            return dbc.Alert(f"⚠️ กรุณากรอกข้อมูลที่จำเป็นให้ครบถ้วน: {', '.join(missing_fields)}", color="warning")

        # ตรวจสอบรูปแบบข้อมูล
        try:
            int_member_id = int(str(member_id).strip()) 
            float_income = float(str(income).replace(',', '').strip())
            datetime.datetime.strptime(str(dob).strip(), '%d/%m/%Y')
            
            if reg_date and reg_date.strip(): 
                datetime.datetime.strptime(str(reg_date).strip(), '%d/%m/%Y')
            
            if appr_date and appr_date.strip(): 
                datetime.datetime.strptime(str(appr_date).strip(), '%d/%m/%Y')
        
        except ValueError as e: 
            
            return dbc.Alert(f"❌ รูปแบบข้อมูลไม่ถูกต้อง: ตรวจสอบ 'รหัสสมาชิก'/'รายได้' (ตัวเลข) และวันที่ (DD/MM/YYYY).", color="danger")

        # บันทึกข้อมูล
        new_member = {
            "รหัสสมาชิก": int_member_id, 
            "คำนำหน้า": prefix.strip(), 
            "ชื่อ": name.strip(), 
            "สกุล": surname.strip(), 
            "ว/ด/ป เกิด": str(dob).strip(),
            "รายได้ (บาท)": float_income, 
            "อาชีพ": occupation.strip() 
            if occupation 
            else None, 
            "รหัสสาขา": branch.strip() 
            if branch 
            else None, 
            "วันที่สมัครสมาชิก": str(reg_date).strip() 
            if reg_date 
            else None, 
            "วันที่อนุมัติ": str(appr_date).strip() 
            if appr_date 
            else None,
            "Timestamp_บันทึก": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        try:
            if collection.find_one({"รหัสสมาชิก": int_member_id}):
                return dbc.Alert(f"❌ บันทึกไม่สำเร็จ: มีรหัสสมาชิก {member_id} อยู่ในระบบแล้ว", color="danger")
            result = collection.insert_one(new_member)
            
            return dbc.Alert(f" บันทึกข้อมูลสมาชิก {member_id} สำเร็จ! (MongoDB ID: {result.inserted_id})", color="success")
        
        except Exception as e:
            return dbc.Alert(f"❌ บันทึกข้อมูลล้มเหลว: {e}", color="danger")