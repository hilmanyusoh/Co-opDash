# src/pages/review.py (ฉบับแก้ไข: แก้ไข NameError: collection is not defined)

from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import pandas as pd
import datetime

# Imports จากภายใน src/
from ..data_manager import get_mongo_client, load_data, prepare_df_for_export, calculate_age_from_dob, DB_NAME, COLLECTION_NAME


# --- กำหนดตัวแปร Global Scope ---
PRIMARY_COLOR = '#007bff'


# --- 1. Layout ของหน้า Review ---
def create_review_layout():
    """สร้าง Layout สำหรับหน้า Data Review (ตรวจสอบและค้นหา)"""
    # ... (ส่วน Layout ไม่มีการเปลี่ยนแปลง) ...
    
    return dbc.Container(
        children=[
            # Header 
            html.Div(
                [
                    html.H1("🔍 Data Review: ตรวจสอบและค้นหาข้อมูลสมาชิก", 
                            className="text-white text-center fw-bolder mb-0"), 
                    html.P(
                        "ตารางข้อลูลสมาชิกพร้อมฟังก์ชันค้นหาและกรองข้อมูล", 
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
                    html.Div([html.I(className="fas fa-search fa-2x text-warning me-3"), html.H3("ค้นหาสมาชิก", className="card-title mb-0 fw-bold"), html.Small(" (Search by Member ID)", className="text-muted ms-2"),],
                        className="d-flex align-items-center mb-4 pb-2 border-bottom border-warning border-opacity-25"),
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText(html.I(className="fas fa-key")),
                            dbc.Input(id='member-id-search', type='text', placeholder='กรุณาพิมพ์รหัสสมาชิก (เช่น 100456)', className="form-control-lg", debounce=True),
                        ], className="mb-4 shadow-sm"
                    ),
                    dbc.Card(id='search-output-table', className="mt-4 p-3 border-light bg-white")
                ]),
                className="shadow-lg mb-5 rounded-4", style={'borderLeft': f'5px solid {PRIMARY_COLOR}'}
            ),
            
            # --- Full Data Table Section (ตารางข้อมูลทั้งหมด) ---
            dbc.Card(
                dbc.CardBody([
                    html.Div([html.I(className="fas fa-database fa-2x text-success me-3"), html.H3("ข้อมูลสมาชิกทั้งหมด", className="card-title mb-0 fw-bold"), html.Small(" (Complete Dataset)", className="text-muted ms-2"),],
                        className="d-flex align-items-center mb-4 pb-2 border-bottom border-success border-opacity-25"),
                    
                    dbc.Row([
                        dbc.Col(html.P("ตารางนี้รองรับการกรอง (Filter) และการเรียงลำดับ (Sort) ข้อมูล", className="text-muted small align-self-end mb-4"), 
                                width=12, 
                                className="text-end")
                    ], className="align-items-center"),

                    html.Div(id='full-data-table', 
                             className="table-responsive p-3 bg-light rounded-3 border"),
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

    # Callback A: ค้นหาข้อมูลสมาชิก (Search)
    @app.callback(
        Output('search-output-table', 'children'),
        [Input('member-id-search', 'value')]
    )
    def search_member_data(member_id):
        if not member_id or not str(member_id).strip(): 
            return html.Div()
        client, status = get_mongo_client()
        if not status: 
            return dbc.Alert("❌ ไม่สามารถเชื่อมต่อ MongoDB เพื่อค้นหาข้อมูลได้", 
                             color="danger")
        
        # *** แก้ไข: กำหนด db และ collection ที่นี่เพื่อให้เข้าถึงได้แน่นอนเมื่อ status เป็น True ***
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        try:
            search_id = str(member_id).strip()
            record = None
            
            # 1. พยายามค้นหาโดยแปลงเป็น integer ก่อน
            try: 
                int_id = int(search_id)
                record = collection.find_one({"รหัสสมาชิก": int_id}) 
            except ValueError: 
                pass 
            
            # 2. ถ้าไม่เจอหรือเป็น String ตั้งแต่แรก ให้ค้นหาเป็น String
            if record is None: 
                # แม้ว่ารหัสสมาชิกควรเป็น int ใน DB แต่เผื่อกรณีโหลดข้อมูลไม่สมบูรณ์
                record = collection.find_one({"รหัสสมาชิก": search_id})

            if record:
                if '_id' in record: 
                    del record['_id']
                age = calculate_age_from_dob(record.get('ว/ด/ป เกิด'))
                record['อายุ (คำนวณ)'] = f"{int(age)} ปี" if pd.notna(age) else "N/A"
                try: 
                    income_value_clean = str(record.get('รายได้ (บาท)', '0')).replace(',', '').strip()
                except: income_value_clean = 0
                record['รายได้ (บาท)'] = "{:,.0f}".format(float(income_value_clean))
                
                df_result = pd.DataFrame(list(record.items()), columns=['คุณสมบัติ', 'ค่า'])
                return dbc.Card(dbc.CardBody([html.H5(f" ✅ พบข้อมูลสมาชิก: {search_id}", 
                                                      className="text-success mb-3"), dash_table.DataTable(id='search-result-table', columns=[{"name": "คุณสมบัติ", "id": "คุณสมบัติ"}, {"name": "ค่า", "id": "ค่า"}], data=df_result.to_dict('records'), style_header={'backgroundColor': PRIMARY_COLOR, 'color': 'white', 'fontWeight': 'bold'}, style_cell={'textAlign': 'left'}, )]), className="shadow-lg border-success border-start border-4")
            else:
                return dbc.Alert(f"⚠️ ไม่พบข้อมูลสมาชิกที่มีรหัส: {search_id}", color="warning")
        except Exception as e: 
            # ถ้าเกิดข้อผิดพลาดอื่น ๆ ที่ไม่ใช่ NameError ในส่วนการค้นหา
            return dbc.Alert(f"❌ เกิดข้อผิดพลาดในการค้นหา: {e}", color="danger")


    # Callback B: ตารางข้อมูลทั้งหมด
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
        df_display = prepare_df_for_export(df)
        data_table = dash_table.DataTable(id='table-review-full', 
                                          columns=[{"name": i, "id": i} for i in df_display.columns], data=df_display.to_dict('records'), 
                                          sort_action="native", 
                                          filter_action="native", 
                                          page_action="native", 
                                          page_current=0, 
                                          page_size=15, 
                                          style_header={'backgroundColor': PRIMARY_COLOR, 'color': 'white', 'fontWeight': 'bold'}, 
                                          style_cell={'textAlign': 'left', 'fontFamily': 'sans-serif'}, export_format='xlsx', 
                                          style_table={'overflowX': 'auto', 'minWidth': '100%'}, )
        return data_table