# src/pages/review.py

from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import pandas as pd
import datetime
import numpy as np 


from ..data_manager import (
    get_pg_engine, 
    load_data, 
    prepare_df_for_export, 
    calculate_age_from_dob, 
)

PRIMARY_COLOR = '#007bff'

# ... (ส่วน Layout create_review_layout() ไม่มีการเปลี่ยนแปลง) ...

layout = create_review_layout()


# --- 2. Callbacks ของหน้า Review ---
def register_callbacks(app):

    # Callback A: ค้นหาข้อมูลสมาชิก (Search)
    @app.callback(
        Output('search-output-table', 'children'),
        [Input('member-id-search', 'value')]
    )
    def search_member_data(member_id):
        if not member_id or not str(member_id).strip(): 
            return html.Div()
        
        try:
            engine = get_pg_engine() 
            search_id = str(member_id).strip()
            
            # --- PostgreSQL Query ---
            query = """
            SELECT 
                member_id, prefix, name, surname, birthday,
                income, career, branch_code,
                registration_date, 
                approval_date, -- <<<< คอลัมน์ "วันที่อนุมัติ"
                (approval_date - registration_date) AS approval_days_calculated -- <<<< คอลัมน์ "ระยะเวลาอนุมัติ"
            FROM members 
            WHERE member_id = %s
            """
            
            df = pd.read_sql(query, engine, params=[search_id]) 

            if df.empty:
                return dbc.Alert(f"⚠️ ไม่พบข้อมูลสมาชิกที่มีรหัส: {search_id}", 
                                 color="warning")

            row = df.iloc[0].to_dict() 
            
            # --- Robust Data Cleaning and Calculation ---
            
            # Age Calculation (ใช้ 'birthday' แทน 'dob')
            dob_key = 'birthday' if 'birthday' in row else 'dob'
            age = calculate_age_from_dob(row.get(dob_key))
            row["อายุ (คำนวณ)"] = f"{age} ปี" if pd.notna(age) else "N/A"
            
            # Income Formatting
            income_value = row.get('income')
            formatted_income = "N/A"
            if pd.notna(income_value) and income_value is not None:
                try:
                    formatted_income = f"{float(income_value):,.0f}" 
                except (ValueError, TypeError):
                    formatted_income = str(income_value) 
            row["income"] = formatted_income
                
            
            # *** การจัดการคอลัมน์ approval_days_calculated (Timedelta) ***
            # Timedelta จาก DB จะอยู่ในรูป Timedelta object ต้องแปลงเป็นจำนวนวัน
            appr_days_raw = row.get('approval_days_calculated')
            if pd.notna(appr_days_raw) and appr_days_raw is not None:
                try:
                    # แปลง Timedelta เป็นจำนวนวัน (เช่น 7 days -> 7)
                    appr_days = appr_days_raw.days 
                    row["approval_days_calculated"] = f"{appr_days} วัน"
                except AttributeError:
                    # ถ้าไม่ใช่ Timedelta (อาจเป็น int หรือ float)
                    row["approval_days_calculated"] = f"{appr_days_raw} วัน"
                except Exception:
                     row["approval_days_calculated"] = "N/A"
            else:
                row["approval_days_calculated"] = "N/A"
            
            
            # [*** การปรับปรุงที่เด็ดขาด: แปลงค่าทั้งหมดให้เป็น String/Native Python Type ***]
            cleaned_row = {}
            for k, v in row.items():
                if pd.isna(v) or v is None or (isinstance(v, str) and v.strip() == ''):
                    cleaned_row[k] = "N/A"
                elif isinstance(v, pd.Timestamp):
                    cleaned_row[k] = str(v.date())
                elif isinstance(v, np.generic):
                    try:
                        cleaned_row[k] = str(v.item()) 
                    except (ValueError, AttributeError, TypeError):
                        cleaned_row[k] = str(v)
                else:
                    cleaned_row[k] = str(v)
            
            # --- Mapping and Result Generation ---
            
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
                "approval_date": "วันที่อนุมัติ",             # <<<< แสดงผล
                "approval_days_calculated": "ระยะเวลาอนุมัติ (วัน)", # <<<< แสดงผล
                "อายุ (คำนวณ)": "อายุ (คำนวณ)",
            }
            
            # สร้าง List of Dictionaries สำหรับ DataTable
            result_list = []
            for db_key, display_name in display_map.items():
                if db_key in cleaned_row:
                    result_list.append({"คุณสมบัติ": display_name, "ค่า": cleaned_row[db_key]})
                
            
            # --- Output Table with Card Wrapper ---
            data_table = dash_table.DataTable(
                id='search-result-table', 
                columns=[
                    {"name": "คุณสมบัติ", "id": "คุณสมบัติ"}, 
                    {"name": "ค่า", "id": "ค่า", "type": "text"}
                ], 
                data=result_list, 
                style_header={
                    'backgroundColor': PRIMARY_COLOR, 
                    'color': 'white', 
                    'fontWeight': 'bold'
                }, 
                style_cell={'textAlign': 'left'}
            )
            
            return dbc.Card(
                dbc.CardBody([
                    html.H5(f" ✅ พบข้อมูลสมาชิก: {search_id}", 
                            className="text-success mb-3"), 
                    data_table
                ]), 
                className="shadow-lg border-success border-start border-4"
            )

        except Exception as e: 
            return dbc.Alert(f"❌ เกิดข้อผิดพลาดในการค้นหา: {e}", color="danger")


    # Callback B: ตารางข้อมูลทั้งหมด (ใช้ load_data ที่สะอาดแล้ว)
    @app.callback(
        Output('full-data-table', 'children'),
        [Input('url', 'pathname')]
    )
    def display_full_data_table(pathname):
        if pathname != "/review": 
            return None
        df = load_data() 
        if df.empty: 
            return dbc.Alert("ไม่พบข้อมูล (DataFrame ว่างเปล่า)", 
                             color="secondary")
        
        # คอลัมน์ approval_date และ approval_days ควรมีอยู่ใน df ที่เตรียมไว้แล้ว
        df_display = prepare_df_for_export(df)
        
        data_table = dash_table.DataTable(id='table-review-full', 
                                          columns=[{"name": i, "id": i} for i in df_display.columns], 
                                          data=df_display.to_dict('records'), 
                                          sort_action="native", 
                                          filter_action="native", 
                                          page_action="native", 
                                          page_current=0, 
                                          page_size=15, 
                                          style_header={'backgroundColor': PRIMARY_COLOR, 'color': 'white', 'fontWeight': 'bold'}, 
                                          style_cell={'textAlign': 'left', 'fontFamily': 'sans-serif'}, 
                                          export_format='xlsx', 
                                          style_table={'overflowX': 'auto', 'minWidth': '100%'}, 
                                          )
        return data_table