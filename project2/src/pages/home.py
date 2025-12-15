# src/pages/home.py

from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import datetime
# =========================================
# เพิ่ม Import ที่จำเป็นสำหรับ SQLAlchemy Text และ Regex
from sqlalchemy import text 
import re 
# =========================================

from ..data_manager import get_pg_engine, calculate_age_from_dob


# ==================================================
# Layout
# ==================================================

def create_home_layout():

    member_count = 0
    db_status = False

    try:
        engine = get_pg_engine()
        # ใช้ pandas.read_sql ในการนับจำนวน
        member_count = pd.read_sql(
            "SELECT COUNT(*) FROM members",
            engine
        ).iloc[0, 0]
        db_status = True
        # สำคัญ: ควรเรียก engine.dispose() เมื่อใช้เสร็จแล้ว
        engine.dispose()
    except Exception:
        pass

    return html.Div(
        children=[
            html.H2(" บันทึกข้อมูลสมาชิกใหม่ ", className="text-primary"),
            html.Hr(),

            dbc.Alert(
                f"{'เชื่อมต่อ PostgreSQL สำเร็จ' if db_status else '❌ ไม่สามารถเชื่อมต่อ PostgreSQL ได้'} | จำนวนสมาชิก: {member_count:,} รายการ",
                color="success" if db_status else "danger",
            ),

            html.H4("กรอกรายละเอียดสมาชิก", className="mt-4"),

            dbc.Card(
                dbc.CardBody(
                    [
                        dbc.Input(id="member-id", placeholder="รหัสสมาชิก*", className="mb-2"),
                        dbc.Select(
                            id="member-prefix",
                            options=[
                                {"label": "นาย", "value": "นาย"},
                                {"label": "นาง", "value": "นาง"},
                                {"label": "นางสาว", "value": "นางสาว"},
                            ],
                            value="นาย",
                            className="mb-2",
                        ),
                        dbc.Input(id="member-name", placeholder="ชื่อ*", className="mb-2"),
                        dbc.Input(id="member-surname", placeholder="นามสกุล*", className="mb-2"),
                        dbc.Input(id="member-dob", placeholder="วันเกิด DD/MM/YYYY*", className="mb-2"),
                        html.Div(id="member-age-display", className="mb-2 text-primary"),
                        dbc.Input(id="member-income", placeholder="รายได้*", className="mb-2"),
                        dbc.Input(id="member-occupation", placeholder="อาชีพ", className="mb-2"),
                        dbc.Input(id="member-branch", placeholder="รหัสสาขา", className="mb-2"),
                        dbc.Input(id="member-regdate", placeholder="วันที่สมัคร DD/MM/YYYY", className="mb-2"),
                        dbc.Input(id="member-apprdate", placeholder="วันที่อนุมัติ DD/MM/YYYY", className="mb-3"),
                        dbc.Button("บันทึกข้อมูล", id="submit-button", color="primary"),
                        html.Div(id="output-message", className="mt-3"),
                    ]
                ),
                className="shadow",
            ),
        ]
    )


layout = create_home_layout()

# ==================================================
# Callbacks
# ==================================================

def register_callbacks(app):

    # อายุ real-time
    @app.callback(
        Output("member-age-display", "children"),
        Input("member-dob", "value"),
    )
    def update_age(dob):
        if not dob:
            return "--"
        age = calculate_age_from_dob(dob)
        # ตรวจสอบค่า age
        if pd.notna(age):
             return f"{int(age)} ปี" 
        else:
             return "รูปแบบวันที่ไม่ถูกต้อง"

    # Submit form
    @app.callback(
        Output("output-message", "children"),
        Input("submit-button", "n_clicks"),
        State("member-id", "value"),
        State("member-prefix", "value"),
        State("member-name", "value"),
        State("member-surname", "value"),
        State("member-dob", "value"),
        State("member-income", "value"),
        State("member-occupation", "value"),
        State("member-branch", "value"),
        State("member-regdate", "value"),
        State("member-apprdate", "value"),
        prevent_initial_call=True # ป้องกันการทำงานตั้งแต่แรก
    )
    def save_member(
        n_clicks, member_id, prefix, name, surname,
        dob, income, career, branch, reg_date, appr_date
    ):
        if not n_clicks:
            return ""

        try:
            engine = get_pg_engine()
            if engine is None:
                return dbc.Alert("❌ บันทึกล้มเหลว: ไม่สามารถเชื่อมต่อฐานข้อมูลได้", color="danger")

            # 1. การตรวจสอบและเตรียมข้อมูล
            # **การทำความสะอาดรายได้:** ลบจุลภาค (,) และช่องว่าง ก่อนแปลงเป็น float
            income_val = float(re.sub(r'[,\s]', '', income)) 

            # แปลงวันที่
            dob_dt = datetime.datetime.strptime(dob, "%d/%m/%Y")
            
            reg_dt = datetime.datetime.strptime(reg_date, "%d/%m/%Y") if reg_date else None
            appr_dt = datetime.datetime.strptime(appr_date, "%d/%m/%Y") if appr_date else None

            approval_days = (appr_dt - reg_dt).days if reg_dt and appr_dt else None
            
            # 2. การสร้าง SQL Query ด้วย text() และ Named Parameters 
            # **แก้ไขชื่อคอลัมน์จาก register_date เป็น registration_date และ approve_date เป็น approval_date**
            sql = text("""
            INSERT INTO members
            (member_id, prefix, name, surname, birthday,
             income, career, branch_code,
             registration_date, approval_date, approval_days, created_at)
            VALUES (:member_id, :prefix, :name, :surname, :birthday,
                    :income, :career, :branch_code,
                    :registration_date, :approval_date, :approval_days, NOW())
            """)

            # 3. สร้าง Dictionary Parameters
            # **แก้ไข Key ใน Dictionary ให้ตรงกับ Named Parameters ใน SQL**
            params = {
                'member_id': int(member_id),
                'prefix': prefix,
                'name': name,
                'surname': surname,
                'birthday': dob_dt.date(),
                'income': income_val, 
                'career': career,
                'branch_code': branch,
                'registration_date': reg_dt.date() if reg_dt else None, # <-- แก้ไข Key
                'approval_date': appr_dt.date() if appr_dt else None, # <-- แก้ไข Key
                'approval_days': approval_days,
            }

            # 4. Execute
            with engine.begin() as conn:
                # ส่ง sql object ที่สร้างจาก text() และ dictionary parameters
                conn.execute(sql, params)
            
            engine.dispose()

            return dbc.Alert("✅ บันทึกข้อมูลสมาชิกสำเร็จ", color="success", duration=5000)

        except Exception as e:
            error_detail = str(e)
            
            # เพิ่มการจัดการ error ที่เป็นประโยชน์
            if "duplicate key" in error_detail.lower():
                error_msg = f"รหัสสมาชิก {member_id} มีอยู่ในระบบแล้ว"
            elif "UndefinedColumn" in error_detail:
                # ถ้าเกิด error ชื่อคอลัมน์อีกครั้ง จะแจ้งเตือนเพื่อตรวจสอบชื่อคอลัมน์อื่น
                error_msg = f"ชื่อคอลัมน์ไม่ถูกต้อง (ตรวจสอบ Case Sensitivity ในตาราง members): {error_detail}"
            elif "invalid input syntax" in error_detail.lower():
                 error_msg = f"รูปแบบข้อมูลไม่ถูกต้อง (เช่น วันที่ หรือ ตัวเลข): {error_detail}"
            else:
                error_msg = error_detail

            return dbc.Alert(f"❌ บันทึกล้มเหลว: {error_msg}", color="danger")