# src/pages/review.py

from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import pandas as pd
import datetime
import numpy as np

# Imports จากภายในโปรเจกต์
from ..data_manager import (
    get_pg_engine, 
    load_data, 
    prepare_df_for_export, 
    calculate_age_from_dob
)

# --- กำหนดตัวแปร Global Scope ---
PRIMARY_COLOR = '#007bff'

# --- 1. Layout ของหน้า Review ---
def create_review_layout():
    """สร้าง Layout สำหรับหน้า Data Review (ตรวจสอบและค้นหา)"""
    return dbc.Container(
        children=[
            # Header
            html.Div(
                [
                    html.H1("🔍 Data Review: ตรวจสอบและค้นหาข้อมูลสมาชิก", 
                            className="text-white text-center fw-bolder mb-0"), 
                    html.P(
                        "ตรวจสอบข้อมูลรายบุคคลและคำนวณระยะเวลาการอนุมัติสมาชิก", 
                        className="text-white-50 text-center mb-0"
                    ),
                ], 
                className="py-4 px-4 mb-5 rounded-4", 
                style={
                    'background': 'linear-gradient(90deg, #007bff 0%, #00bcd4 100%)', 
                    'boxShadow': f'0 4px 15px {PRIMARY_COLOR}50' 
                }
            ),
            
            # --- Search Section (ค้นหาข้อมูลสมาชิกรายบุคคล) ---
            dbc.Card(
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-search fa-2x text-warning me-3"), 
                        html.H3("ค้นหาสมาชิก", className="card-title mb-0 fw-bold"), 
                        html.Small(" (ค้นหาด้วยรหัสสมาชิก)", className="text-muted ms-2"),
                    ], className="d-flex align-items-center mb-4 pb-2 border-bottom border-warning border-opacity-25"),
                    
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText(html.I(className="fas fa-key")),
                            dbc.Input(
                                id='member-id-search', 
                                type='text', 
                                placeholder='กรุณาพิมพ์รหัสสมาชิก (เช่น 100456)', 
                                className="form-control-lg", 
                                debounce=True
                            ),
                        ], className="mb-4 shadow-sm"
                    ),
                    # พื้นที่แสดงตารางผลการค้นหา
                    html.Div(id='search-output-table')
                ]),
                className="shadow-lg mb-5 rounded-4", style={'borderLeft': f'5px solid {PRIMARY_COLOR}'}
            ),
            
            # --- Full Data Table Section (ตารางข้อมูลทั้งหมดจาก Postgres) ---
            dbc.Card(
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-database fa-2x text-success me-3"), 
                        html.H3("ข้อมูลสมาชิกทั้งหมดในระบบ", className="card-title mb-0 fw-bold")
                    ], className="d-flex align-items-center mb-4 pb-2 border-bottom border-success border-opacity-25"),
                    
                    html.Div(id='full-data-table', className="table-responsive p-3 bg-light rounded-3 border"),
                ]), 
                className="shadow-lg mt-4 mb-5 rounded-4", 
                style={'borderLeft': f'5px solid {PRIMARY_COLOR}'}
            )
        ], 
        fluid=True,
        className="py-5 bg-light"
    )

layout = create_review_layout()

# --- 2. Callbacks ของหน้า Review ---
def register_callbacks(app):

    # Callback A: ค้นหาข้อมูลสมาชิกรายบุคคลจาก PostgreSQL
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
            
            # ค้นหาข้อมูลจากตาราง members ใน PostgreSQL
            # ใช้ Query parameter เพื่อป้องกัน SQL Injection
            query = f"SELECT * FROM members WHERE member_id = %s"
            df = pd.read_sql(query, engine, params=[search_id])
            engine.dispose()

            if not df.empty:
                row = df.iloc[0].to_dict()
                
                # 1. คำนวณอายุ
                age = calculate_age_from_dob(row.get('birthday'))
                
                # 2. คำนวณระยะเวลาอนุมัติ (Registration vs Approval)
                reg_date = pd.to_datetime(row.get('registration_date'))
                appr_date = pd.to_datetime(row.get('approval_date'))
                
                duration_text = "N/A"
                if pd.notna(reg_date) and pd.notna(appr_date):
                    delta = (appr_date - reg_date).days
                    duration_text = f"{delta} วัน"
                
                # 3. จัดรูปแบบข้อมูลที่จะแสดงในตาราง (Mapping ภาษาไทย)
                display_data = [
                    {"คุณสมบัติ": "รหัสสมาชิก", "ค่า": row.get('member_id')},
                    {"คุณสมบัติ": "ชื่อ-นามสกุล", "ค่า": f"{row.get('prefix')}{row.get('name')} {row.get('surname')}"},
                    {"คุณสมบัติ": "อายุ (คำนวณ)", "ค่า": f"{int(age)} ปี" if pd.notna(age) else "N/A"},
                    {"คุณสมบัติ": "รายได้", "ค่า": "{:,.2f} บาท".format(row.get('income', 0))},
                    {"คุณสมบัติ": "อาชีพ", "ค่า": row.get('career', '-')},
                    {"คุณสมบัติ": "วันที่สมัคร", "ค่า": reg_date.strftime('%d/%m/%Y') if pd.notna(reg_date) else "-"},
                    {"คุณสมบัติ": "วันที่อนุมัติ", "ค่า": appr_date.strftime('%d/%m/%Y') if pd.notna(appr_date) else "-"},
                    {"คุณสมบัติ": "🚩 ระยะเวลาการอนุมัติ", "ค่า": duration_text},
                ]

                return dbc.Card(
                    dbc.CardBody([
                        html.H5(f" ✅ พบข้อมูลสมาชิก: {search_id}", className="text-success mb-3"),
                        dash_table.DataTable(
                            columns=[{"name": "คุณสมบัติ", "id": "คุณสมบัติ"}, {"name": "ค่า", "id": "ค่า"}],
                            data=display_data,
                            style_header={'backgroundColor': PRIMARY_COLOR, 'color': 'white', 'fontWeight': 'bold'},
                            style_cell={'textAlign': 'left', 'padding': '10px'},
                            style_data_conditional=[{
                                'if': {'filter_query': '{คุณสมบัติ} contains "ระยะเวลาการอนุมัติ"'},
                                'backgroundColor': '#fff3cd', 'fontWeight': 'bold'
                            }]
                        )
                    ]), 
                    className="shadow-lg border-success border-start border-4"
                )
            else:
                return dbc.Alert(f"⚠️ ไม่พบข้อมูลสมาชิกที่มีรหัส: {search_id}", color="warning")
        except Exception as e: 
            return dbc.Alert(f"❌ เกิดข้อผิดพลาดในการค้นหา: {str(e)}", color="danger")


    # Callback B: ตารางข้อมูลทั้งหมด (PostgreSQL)
    @app.callback(
        Output('full-data-table', 'children'),
        [Input('url', 'pathname')]
    )
    def display_full_data_table(pathname):
        if pathname != "/review": 
            return None
        
        df = load_data() # ฟังก์ชันโหลดข้อมูลจาก Postgres ที่อยู่ใน data_manager.py
        if df.empty: 
            return dbc.Alert("ไม่พบข้อมูลในฐานข้อมูล PostgreSQL", color="secondary")
        
        df_display = prepare_df_for_export(df)
        
        return dash_table.DataTable(
            id='table-review-full', 
            columns=[{"name": i, "id": i} for i in df_display.columns], 
            data=df_display.to_dict('records'), 
            sort_action="native", 
            filter_action="native", 
            page_size=15,
            style_header={'backgroundColor': PRIMARY_COLOR, 'color': 'white', 'fontWeight': 'bold'}, 
            style_cell={'textAlign': 'left', 'fontFamily': 'sans-serif'}, 
            export_format='xlsx', 
            style_table={'overflowX': 'auto'}
        )