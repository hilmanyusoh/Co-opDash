# src/pages/review.py

from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import pandas as pd
import datetime

# --- Imports จากภายใน src/ ---
from ..data_manager import get_mongo_client, load_data, prepare_df_for_export, calculate_age_from_dob, DB_NAME, COLLECTION_NAME


# --- 1. Layout ของหน้า Review ---
def create_review_layout():
    """สร้าง Layout สำหรับหน้า Data Review"""
    # ... (Layout Component ทั้งหมดคัดลอกมาจาก layout_review.py เดิม) ...
    return dbc.Container(
        children=[
            html.H1("ตรวจสอบและค้นหาข้อมูลสมาชิก", className="text-warning text-center my-5 fw-light border-bottom border-warning pb-2"),
            
            # --- Search Section ---
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
                className="shadow-lg mb-5 rounded-4", style={'borderLeft': '5px solid #ffc107'}
            ),
            
            # --- Full Data Table Section ---
            dbc.Card(
                dbc.CardBody([
                    html.Div([html.I(className="fas fa-database fa-2x text-success me-3"), html.H3("ข้อมูลสมาชิกทั้งหมด", className="card-title mb-0 fw-bold"), html.Small(" (Complete Dataset)", className="text-muted ms-2"),],
                        className="d-flex align-items-center mb-4 pb-2 border-bottom border-success border-opacity-25"),
                    dbc.Row([
                        dbc.Col(dbc.Button([html.I(className="fas fa-file-excel me-2"), "ดาวน์โหลดข้อมูลทั้งหมด (.csv)"], id="btn-download-csv", color="success", className="mb-4 shadow-sm fw-bold", size="lg"), width="auto"),
                        dbc.Col(html.P("ตารางนี้รองรับการกรอง (Filter) และการเรียงลำดับ (Sort) ข้อมูล", className="text-muted small align-self-end mb-4"), width=True, className="text-end")
                    ], className="align-items-center"),

                    dcc.Download(id="download-dataframe-csv"), 
                    html.Div(id='full-data-table', className="table-responsive p-3 bg-light rounded-3 border"),
                ]),
                className="shadow-lg mt-4 mb-5 rounded-4", style={'borderLeft': '5px solid #198754'}
            )
        ],
        fluid=True,
        className="py-5 bg-light"
    )

layout = create_review_layout()


# --- 2. Callbacks ของหน้า Review ---
def register_callbacks(app):
    """ลงทะเบียน Callbacks เฉพาะส่วน Review (Callback 4, 5, 6 เดิม)"""

    # Callback A: ค้นหาข้อมูลสมาชิก
    @app.callback(
        Output('search-output-table', 'children'),
        [Input('member-id-search', 'value')]
    )
    def search_member_data(member_id):
        if not member_id or not str(member_id).strip(): return html.Div()
        client, status = get_mongo_client()
        if not status: return dbc.Alert("❌ ไม่สามารถเชื่อมต่อ MongoDB เพื่อค้นหาข้อมูลได้", color="danger")
        db = client[DB_NAME]; collection = db[COLLECTION_NAME]

        try:
            search_id = str(member_id).strip()
            record = None
            try: int_id = int(search_id); record = collection.find_one({"รหัสสมาชิก": int_id}) 
            except ValueError: pass 
            if record is None: record = collection.find_one({"รหัสสมาชิก": search_id})

            if record:
                if '_id' in record: del record['_id']
                age = calculate_age_from_dob(record.get('ว/ด/ป เกิด'))
                record['อายุ (คำนวณ)'] = f"{int(age)} ปี" if pd.notna(age) else "N/A"
                try: income_value_clean = str(record.get('รายได้ (บาท)', '0')).replace(',', '').strip()
                except: income_value_clean = 0
                record['รายได้ (บาท)'] = "{:,.0f}".format(float(income_value_clean))
                
                df_result = pd.DataFrame(list(record.items()), columns=['คุณสมบัติ', 'ค่า'])
                return dbc.Card(dbc.CardBody([html.H5(f" พบข้อมูลสมาชิก: {search_id}", className="text-success mb-3"), dash_table.DataTable(id='search-result-table', columns=[{"name": "คุณสมบัติ", "id": "คุณสมบัติ"}, {"name": "ค่า", "id": "ค่า"}], data=df_result.to_dict('records'), style_header={'backgroundColor': '#2980b9', 'color': 'white', 'fontWeight': 'bold'}, style_cell={'textAlign': 'left'}, )]), className="shadow-lg border-success border-start border-4")
            else:
                return dbc.Alert(f"⚠️ ไม่พบข้อมูลสมาชิกที่มีรหัส: {search_id}", color="warning")
        except Exception as e: return dbc.Alert(f"❌ เกิดข้อผิดพลาดในการค้นหา: {e}", color="danger")


    # Callback B: สร้างตารางข้อมูลทั้งหมด
    @app.callback(
        Output('full-data-table', 'children'),
        [Input('url', 'pathname')]
    )
    def display_full_data_table(pathname):
        if pathname != "/review": return None
        df = load_data() 
        if df.empty: return dbc.Alert("ไม่พบข้อมูล (DataFrame ว่างเปล่า)", color="secondary")
        df_display = prepare_df_for_export(df)
        data_table = dash_table.DataTable(id='table-review-full', columns=[{"name": i, "id": i} for i in df_display.columns], data=df_display.to_dict('records'), sort_action="native", filter_action="native", page_action="native", page_current=0, page_size=15, style_header={'backgroundColor': '#198754', 'color': 'white', 'fontWeight': 'bold'}, style_cell={'textAlign': 'left', 'fontFamily': 'sans-serif'}, export_format='xlsx', style_table={'overflowX': 'auto', 'minWidth': '100%'}, )
        return data_table


    # Callback C: ดาวน์โหลดข้อมูลทั้งหมดเป็น CSV
    @app.callback(
        Output("download-dataframe-csv", "data"),
        [Input("btn-download-csv", "n_clicks")],
        prevent_initial_call=True,
    )
    def download_csv(n_clicks):
        df = load_data()
        if df.empty: return dcc.no_update
        df_export = prepare_df_for_export(df)
        return dcc.send_data_frame(
            df_export.to_csv, 
            filename=f"member_data_export_{datetime.date.today().strftime('%Y%m%d')}.csv"
        )