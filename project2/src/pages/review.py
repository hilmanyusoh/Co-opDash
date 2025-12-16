# src/pages/review.py

from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np 


from ..data_manager import (
    get_pg_engine,
    load_data,
    prepare_df_for_export,
    calculate_age_from_dob
)

PRIMARY_COLOR = "#007bff"


# ==================================================
# Layout (ไม่มีการเปลี่ยนแปลง)
# ==================================================

def create_review_layout():
    return dbc.Container(
        children=[
            html.Div(
                [
                    html.H1("🔍 Data Review: ตรวจสอบและค้นหาข้อมูลสมาชิก",
                            className="text-white text-center fw-bolder mb-0"),
                    html.P("ตารางข้อมูลสมาชิกพร้อมฟังก์ชันค้นหาและกรองข้อมูล",
                           className="text-white-50 text-center mb-0"),
                ],
                className="py-4 px-4 mb-5 rounded-4",
                style={
                    "background": "linear-gradient(90deg, #007bff 0%, #00bcd4 100%)",
                    "boxShadow": f"0 4px 15px {PRIMARY_COLOR}50",
                },
            ),

            # Search
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H4("ค้นหาสมาชิก (Member ID)", className="mb-3"),
                        dbc.Input(
                            id="member-id-search",
                            placeholder="เช่น 100456",
                            debounce=True,
                        ),
                        html.Div(id="search-output-table", className="mt-4"),
                    ]
                ),
                className="shadow mb-5",
            ),

            # Full table
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H4("ข้อมูลสมาชิกทั้งหมด", className="mb-3"),
                        html.Div(id="full-data-table"),
                    ]
                ),
                className="shadow",
            ),
        ],
        fluid=True,
        className="py-5",
    )


layout = create_review_layout()

# ==================================================
# Callbacks
# ==================================================

def register_callbacks(app):

    # ----------------------------------------------
    # Search by Member ID
    # ----------------------------------------------
    @app.callback(
        Output("search-output-table", "children"),
        Input("member-id-search", "value"),
    )
    def search_member(member_id):
        if not member_id:
            return ""

        try:
            engine = get_pg_engine()

            query = """
            SELECT *
            FROM members
            WHERE member_id = %s
            """

            df = pd.read_sql(query, engine, params=[member_id])

            if df.empty:
                return dbc.Alert(
                    f"⚠️ ไม่พบสมาชิกที่มีรหัส {member_id}",
                    color="warning",
                )

            # แปลงแถวเป็น Series เพื่อใช้ฟังก์ชันทำความสะอาดของ Pandas
            row_series = df.iloc[0]

            # 1. ทำความสะอาดค่า Null/NaN ใน Series โดยเติมด้วย "N/A"
            row_series = row_series.fillna("N/A")

            # 2. แปลงเป็น Dictionary 
            row = row_series.to_dict()

            # --- [การคำนวณและจัดรูปแบบ] ---
            
            dob_key = 'birthday' if 'birthday' in row else 'dob'
            
            # การคำนวณ Age (จัดการ Null โดยใช้ .get() และค่าที่ถูก fillna แล้ว)
            age_input = row.get(dob_key)
            if age_input != "N/A":
                age = calculate_age_from_dob(age_input)
                row["อายุ (คำนวณ)"] = f"{age} ปี" if pd.notna(age) else "N/A"
            else:
                row["อายุ (คำนวณ)"] = "N/A"

            # Income Formatting
            income_value = row.get('income', 'N/A')
            if income_value != "N/A":
                try:
                    # ถ้าเป็นตัวเลข/สตริงตัวเลข ให้ format
                    row["income"] = f"{float(income_value):,.0f}" 
                except (ValueError, TypeError):
                    # ถ้าแปลงไม่ได้ ให้เก็บค่าเดิม (ซึ่งคือค่าที่ fillna แล้ว)
                    row["income"] = str(income_value)
            
            # [*** การทำความสะอาดขั้นสุดท้าย ***]: แปลงทุกค่าให้เป็น String อย่างชัดเจน
            cleaned_row = {k: str(v) for k, v in row.items()}

            # --------------------------------------------------------

            display_map = {
                "member_id": "รหัสสมาชิก",
                "prefix": "คำนำหน้า",
                "name": "ชื่อ", 
                "surname": "สกุล",                 
                "birthday": "ว/ด/ป เกิด", 
                "income": "รายได้ (บาท)",
                "career": "อาชีพ",
                "branch_code": "รหัสสาขา",                
                "registration_date": "วันที่สมัครสมาชิก", 
                "approval_date": "วันที่อนุมัติ", 
                "Approval_days": "ระยะเวลาอนุมัติ (วัน)", 
                "อายุ (คำนวณ)": "อายุ (คำนวณ)",
            }
            
            # สร้าง List of Dictionaries สำหรับ DataTable
            result = []
            for k, display_name in display_map.items():
                # ดึงค่าจาก cleaned_row (ซึ่งรับประกันว่าทุกค่าเป็น String)
                if k in cleaned_row:
                    result.append({"คุณสมบัติ": display_name, "ค่า": cleaned_row[k]})
                
            
            return dash_table.DataTable(
                columns=[
                    {"name": "คุณสมบัติ", "id": "คุณสมบัติ"},
                    {"name": "ค่า", "id": "ค่า", "type": "text"}, 
                ],
                data=result,
                style_header={
                    "backgroundColor": PRIMARY_COLOR,
                    "color": "white",
                    "fontWeight": "bold",
                },
                style_cell={"textAlign": "left"},
            )

        except Exception as e:
            error_message = f"❌ เกิดข้อผิดพลาด: {e}"
            return dbc.Alert(error_message, color="danger")

    # ----------------------------------------------
    # Full data table (ไม่มีการเปลี่ยนแปลง)
    # ----------------------------------------------
    @app.callback(
        Output("full-data-table", "children"),
        Input("url", "pathname"),
    )
    def load_full_table(pathname):
        if pathname != "/review":
            return ""

        df = load_data()

        if df.empty:
            return dbc.Alert("ไม่พบข้อมูลในระบบ", color="secondary")

        df_display = prepare_df_for_export(df)

        return dash_table.DataTable(
            columns=[{"name": c, "id": c} for c in df_display.columns],
            data=df_display.to_dict("records"),
            filter_action="native",
            sort_action="native",
            page_action="native",
            page_size=15,
            export_format="xlsx",
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": PRIMARY_COLOR,
                "color": "white",
                "fontWeight": "bold",
            },
            style_cell={"textAlign": "left"},
        )