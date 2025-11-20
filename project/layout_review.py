# layout_review.py

from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc

def render_review_tab():
    """สร้างเนื้อหาสำหรับหน้า Data Review (ตารางและช่องค้นหา)"""

    return html.Div(
        children=[
            html.H2(" Data Review & Search (ค้นหาข้อมูลสมาชิก)", className="text-warning"),
            html.Hr(className="mb-4"),
            
            # ส่วนค้นหาข้อมูลสมาชิกรายบุคคล
            dbc.Card(
                dbc.CardBody([
                    html.H4("ค้นหาสมาชิกด้วยรหัสสมาชิก", className="card-title text-muted"),
                    dbc.Input(
                        id='member-id-search', 
                        type='text', 
                        placeholder='พิมพ์รหัสสมาชิกที่ต้องการค้นหา (เช่น 100456)...', 
                        className="mb-3",
                        debounce=True 
                    ),
                    html.Div(id='search-output-table', className="mt-4")
                ]),
                className="shadow-lg mb-5 border-start border-4 border-warning"
            ),
            
            # ส่วนแสดงตารางข้อมูลทั้งหมดและปุ่มดาวน์โหลด
            dbc.Card(
                dbc.CardBody([
                    html.H4("ตารางแสดงข้อมูลสมาชิกทั้งหมด", className="text-success"),
                    html.P("ตารางนี้สามารถเรียงลำดับและกรองข้อมูลได้ (Filter/Sortable).", className="text-muted"),
                    dbc.Button(
                        [html.I(className="bi bi-download me-2"), "ดาวน์โหลดข้อมูลทั้งหมด (.csv)"],
                        id="btn-download-csv", 
                        color="success", 
                        className="mb-3"
                    ),
                    dcc.Download(id="download-dataframe-csv"), 
                    html.Div(id='full-data-table', className="mt-4"),
                ]),
                className="shadow-sm mt-4 border-start border-4 border-success"
            )
        ]
    )