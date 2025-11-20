from dash.dependencies import Input, Output, State
# แก้ไขบรรทัดนี้: เพิ่ม html
from dash import dcc, html 
import dash_bootstrap_components as dbc
from dash import dash_table
import datetime
import pandas as pd
import numpy as np

# เปลี่ยนจาก 'from .data_manager' เป็น 'from data_manager'
from data_manager import get_mongo_client, calculate_age_from_dob, load_data, prepare_df_for_export, DB_NAME, COLLECTION_NAME


def register_callbacks(app):
    """ฟังก์ชันหลักสำหรับลงทะเบียน Callbacks ทั้งหมดให้กับ Dash App"""

    # --- Callback 1: อัปเดตเนื้อหาตาม URL (Routing) ---
    @app.callback(Output("page-content", "children"), [Input("url", "pathname")])
    def render_page_content(pathname):
        # เปลี่ยนจาก 'from .layout_...' เป็น 'from layout_...'
        from layout_home import render_home_tab
        from layout_analysis import render_analysis_tab
        from layout_review import render_review_tab
        
        if pathname == "/" or pathname == "/home":
            return render_home_tab()
        
        elif pathname == "/analysis":
            # โหลดข้อมูลอีกครั้งเพื่อให้ได้ข้อมูลล่าสุด
            df = load_data() 
            return render_analysis_tab(df)
            
        elif pathname == "/review":
            return render_review_tab() 
            
        return dbc.Jumbotron(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"เส้นทาง {pathname} ไม่ถูกต้อง"),
            ], 
            className="p-3" 
        )

    # --- Callback 2: การคำนวณอายุแบบ Real-time (Home Tab) ---
    @app.callback(
        Output('member-age-display', 'children'),
        [Input('member-dob', 'value')]
    )
    def update_age_display(dob_str):
        if not dob_str:
            return "--"
        age = calculate_age_from_dob(dob_str)
        return f"{int(age)} ปี" if pd.notna(age) else "รูปแบบวันที่ไม่ถูกต้อง"


    # --- Callback 3: การจัดการ Submit Form (Home Tab) ---
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
    def save_member_data(n_clicks, member_id, prefix, name, surname, dob, income, occupation, branch, reg_date, appr_date):
        if n_clicks is None:
            return ""
        
        client, status = get_mongo_client()
        if not status:
            return dbc.Alert("❌ ไม่สามารถเชื่อมต่อ MongoDB เพื่อบันทึกข้อมูลได้", color="danger")

        # 1. การตรวจสอบข้อมูลเบื้องต้น (ตามโค้ดเดิม)
        required_fields = {
            "รหัสสมาชิก": member_id, "คำนำหน้า": prefix, "ชื่อ": name, 
            "นามสกุล": surname, "ว/ด/ป เกิด": dob, "รายได้ (บาท)": income
        }
        missing_fields = [k for k, v in required_fields.items() if not v or str(v).strip() == ""]
        if missing_fields:
            return dbc.Alert(f"⚠️ กรุณากรอกข้อมูลที่จำเป็นให้ครบถ้วน: {', '.join(missing_fields)}", color="warning")

        # 2. การตรวจสอบรูปแบบข้อมูล (ตามโค้ดเดิม)
        try:
            int_member_id = int(str(member_id).strip()) 
            float_income = float(str(income).replace(',', '').strip())
            datetime.datetime.strptime(str(dob).strip(), '%d/%m/%Y')
            if reg_date and reg_date.strip(): datetime.datetime.strptime(str(reg_date).strip(), '%d/%m/%Y')
            if appr_date and appr_date.strip(): datetime.datetime.strptime(str(appr_date).strip(), '%d/%m/%Y')
            
        except ValueError as e:
            return dbc.Alert(f"❌ รูปแบบข้อมูลไม่ถูกต้อง: ตรวจสอบ 'รหัสสมาชิก' หรือ 'รายได้' ต้องเป็นตัวเลข และวันที่ต้องเป็นรูปแบบ DD/MM/YYYY.", color="danger")

        # 3. เตรียมเอกสารสำหรับ MongoDB (ตามโค้ดเดิม)
        new_member = {
            "รหัสสมาชิก": int_member_id, 
            "คำนำหน้า": prefix.strip(), 
            "ชื่อ": name.strip(),
            "สกุล": surname.strip(),
            "ว/ด/ป เกิด": str(dob).strip(),
            "รายได้ (บาท)": float_income,
            "อาชีพ": occupation.strip() if occupation else None,
            "รหัสสาขา": branch.strip() if branch else None, 
            "วันที่สมัครสมาชิก": str(reg_date).strip() if reg_date else None,
            "วันที่อนุมัติ": str(appr_date).strip() if appr_date else None,
            "Timestamp_บันทึก": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # 4. บันทึกข้อมูล
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        try:
            # ตรวจสอบรหัสสมาชิกซ้ำ
            existing_member_int = collection.find_one({"รหัสสมาชิก": int_member_id})
            
            if existing_member_int:
                return dbc.Alert(f"❌ บันทึกไม่สำเร็จ: มีรหัสสมาชิก {member_id} อยู่ในระบบแล้ว", color="danger")
                
            result = collection.insert_one(new_member)
            
            return dbc.Alert(
                f" บันทึกข้อมูลสมาชิก {member_id} สำเร็จ! (MongoDB ID: {result.inserted_id})",
                color="success"
            )
        except Exception as e:
            return dbc.Alert(f"❌ บันทึกข้อมูลล้มเหลว: {e}", color="danger")

    # --- Callback 4: ค้นหาข้อมูลสมาชิก (Data Review Tab) ---
    @app.callback(
        Output('search-output-table', 'children'),
        [Input('member-id-search', 'value')]
    )
    def search_member_data(member_id):
        if not member_id or not str(member_id).strip():
            return html.Div()
        
        client, status = get_mongo_client()
        if not status:
            return dbc.Alert("❌ ไม่สามารถเชื่อมต่อ MongoDB เพื่อค้นหาข้อมูลได้", color="danger")
            
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        try:
            search_id = str(member_id).strip()
            record = None
            
            # 1. พยายามแปลงเป็น Integer เพื่อค้นหาใน MongoDB ก่อน
            try:
                int_id = int(search_id)
                record = collection.find_one({"รหัสสมาชิก": int_id}) 
            except ValueError:
                pass 

            # 2. หากค้นหาด้วย Integer ไม่พบ (หรือ input ไม่ใช่เลข) ให้ลองค้นหาด้วย String
            if record is None:
                record = collection.find_one({"รหัสสมาชิก": search_id})

            
            if record:
                if '_id' in record:
                    del record['_id']
                
                # คำนวณอายุ Real-time
                dob_str = record.get('ว/ด/ป เกิด')
                age = calculate_age_from_dob(dob_str)
                record['อายุ (คำนวณ)'] = f"{int(age)} ปี" if pd.notna(age) else "N/A"
                
                # จัดรูปแบบรายได้
                income_value = record.get('รายได้ (บาท)', '0')
                if isinstance(income_value, (str, int, float)):
                    try:
                        income_value_clean = str(income_value).replace(',', '').strip()
                        record['รายได้ (บาท)'] = "{:,.0f}".format(float(income_value_clean))
                    except ValueError:
                        record['รายได้ (บาท)'] = income_value 
                
                df_result = pd.DataFrame(list(record.items()), columns=['คุณสมบัติ', 'ค่า'])

                return dbc.Card(
                    dbc.CardBody([
                        html.H5(f" พบข้อมูลสมาชิก: {search_id}", className="text-success mb-3"),
                        dash_table.DataTable(
                            id='search-result-table',
                            columns=[{"name": "คุณสมบัติ", "id": "คุณสมบัติ"}, {"name": "ค่า", "id": "ค่า"}],
                            data=df_result.to_dict('records'),
                            style_header={'backgroundColor': '#2980b9', 'color': 'white', 'fontWeight': 'bold'},
                            style_cell={'textAlign': 'left'},
                        )
                    ]),
                    className="shadow-lg border-success border-start border-4"
                )
            else:
                return dbc.Alert(f"⚠️ ไม่พบข้อมูลสมาชิกที่มีรหัส: {search_id}", color="warning")
                
        except Exception as e:
            return dbc.Alert(f"❌ เกิดข้อผิดพลาดในการค้นหา: {e}", color="danger")


    # --- Callback 5: สร้างตารางข้อมูลทั้งหมด (Review Tab) ---
    @app.callback(
        Output('full-data-table', 'children'),
        [Input('url', 'pathname')]
    )
    def display_full_data_table(pathname):
        if pathname != "/review":
            return None
        
        df = load_data() 
        
        if df.empty:
            return dbc.Alert("ไม่พบข้อมูล (DataFrame ว่างเปล่า)", color="secondary")

        df_display = prepare_df_for_export(df)

        data_table = dash_table.DataTable(
            id='table-review-full',
            columns=[{"name": i, "id": i} for i in df_display.columns],
            data=df_display.to_dict('records'),
            sort_action="native", 
            filter_action="native", 
            page_action="native",
            page_current=0,
            page_size=15, 
            style_header={'backgroundColor': '#198754', 'color': 'white', 'fontWeight': 'bold'},
            style_cell={'textAlign': 'left', 'fontFamily': 'sans-serif'},
            export_format='xlsx', 
            style_table={'overflowX': 'auto', 'minWidth': '100%'}, 
        )
        return data_table


    # --- Callback 6: ดาวน์โหลดข้อมูลทั้งหมดเป็น CSV ---
    @app.callback(
        Output("download-dataframe-csv", "data"),
        [Input("btn-download-csv", "n_clicks")],
        prevent_initial_call=True,
    )
    def download_csv(n_clicks):
        df = load_data()
        
        if df.empty:
            return dcc.no_update
            
        df_export = prepare_df_for_export(df)
        
        return dcc.send_data_frame(
            df_export.to_csv, 
            filename=f"member_data_export_{datetime.date.today().strftime('%Y%m%d')}.csv"
        )