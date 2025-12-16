# src/pages/home.py

from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import datetime
import re

from sqlalchemy import text

from ..data_manager import get_pg_engine, calculate_age_from_dob

# ==================================================
# Layout
# ==================================================

def create_home_layout():
    member_count = 0
    db_status = False

    try:
        engine = get_pg_engine()
        if engine is not None:
            member_count = pd.read_sql(
                "SELECT COUNT(*) FROM members",
                engine
            ).iloc[0, 0]
            db_status = True
            engine.dispose()
    except Exception:
        db_status = False

    return html.Div(
        children=[
            html.H2("บันทึกข้อมูลสมาชิกใหม่", className="text-primary"),
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

    # -------------------------------
    # แสดงอายุแบบ real-time
    # -------------------------------
    @app.callback(
        Output("member-age-display", "children"),
        Input("member-dob", "value"),
    )
    def update_age(dob):
        if not dob:
            return "--"
        age = calculate_age_from_dob(dob)
        if pd.notna(age):
            return f"{int(age)} ปี"
        return "รูปแบบวันที่ไม่ถูกต้อง"

    # -------------------------------
    # บันทึกข้อมูลสมาชิก
    # -------------------------------
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
        prevent_initial_call=True,
    )
    def save_member(
        n_clicks, member_id, prefix, name, surname,
        dob, income, career, branch, reg_date, appr_date
    ):
        try:
            # -------------------------------
            # Validate required fields
            # -------------------------------
            if not all([member_id, name, surname, dob, income]):
                return dbc.Alert("กรุณากรอกข้อมูลที่มีเครื่องหมาย * ให้ครบ", color="warning")

            engine = get_pg_engine()
            if engine is None:
                return dbc.Alert("❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้", color="danger")

            # -------------------------------
            # Clean & convert data
            # -------------------------------
            income_val = float(re.sub(r"[^0-9.]", "", income))

            dob_dt = datetime.datetime.strptime(dob, "%d/%m/%Y").date()
            reg_dt = datetime.datetime.strptime(reg_date, "%d/%m/%Y").date() if reg_date else None
            appr_dt = datetime.datetime.strptime(appr_date, "%d/%m/%Y").date() if appr_date else None

            approval_days = (appr_dt - reg_dt).days if reg_dt and appr_dt else None

            # -------------------------------
            # SQL Insert
            # -------------------------------
            
            sql = text("""
                INSERT INTO members (
                member_id, prefix, name, surname, birthday,
                income, career, branch_code,
                registration_date, approval_date
            ) VALUES (
                :member_id, :prefix, :name, :surname, :birthday,
                :income, :career, :branch_code,
                :registration_date, :approval_date
            )
        """)

            params = {
                "member_id": int(member_id),
                "prefix": prefix,
                "name": name,
                "surname": surname,
                "birthday": dob_dt,
                "income": income_val,
                "career": career,
                "branch_code": branch,
                "registration_date": reg_dt,
                "approval_date": appr_dt,
            }


            with engine.begin() as conn:
                conn.execute(sql, params)

            engine.dispose()

            return dbc.Alert("✅ บันทึกข้อมูลสมาชิกสำเร็จ", color="success", duration=4000)

        except Exception as e:
            msg = str(e)
            if "duplicate key" in msg.lower():
                msg = f"รหัสสมาชิก {member_id} มีอยู่ในระบบแล้ว"
            elif "invalid input" in msg.lower():
                msg = "รูปแบบข้อมูลไม่ถูกต้อง (วันที่/ตัวเลข)"

            return dbc.Alert(f"❌ บันทึกล้มเหลว: {msg}", color="danger")
