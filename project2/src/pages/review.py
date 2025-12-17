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

# ==================================================
# Layout
# ==================================================

def create_review_layout():
    """สร้าง Layout สำหรับหน้า Data Review"""
    return html.Div(
        style={"backgroundColor": "#f8fafc", "minHeight": "100vh"},
        children=[
            dbc.Container(
                fluid=True,
                className="py-4 px-4",
                children=[
                    # Header Section
                    html.Div(
                        className="mb-4",
                        children=[
                            html.H2(
                                "🔍 ค้นหาและตรวจสอบข้อมูล",
                                style={"color": "#1e293b", "fontWeight": "600"},
                                className="mb-2"
                            ),
                            html.P(
                                "ค้นหารายละเอียดสมาชิกและดูภาพรวมข้อมูลทั้งหมด",
                                className="text-muted mb-0",
                                style={"fontSize": "0.95rem"}
                            ),
                        ]
                    ),
                    
                    # Search Section
                    dbc.Card(
                        dbc.CardBody([
                            html.Div(
                                [
                                    html.I(className="bi bi-search me-2", style={"color": "#6366f1", "fontSize": "1.1rem"}),
                                    html.H5("ค้นหาด้วยรหัสสมาชิก", className="d-inline mb-0", style={"color": "#475569"})
                                ],
                                className="mb-3 d-flex align-items-center"
                            ),
                            dbc.InputGroup(
                                [
                                    dbc.Input(
                                        id='member-id-search', 
                                        type='text', 
                                        placeholder='กรอกรหัสสมาชิก เช่น 100456', 
                                        debounce=True,
                                        style={"borderColor": "#e2e8f0", "fontSize": "0.95rem"}
                                    ),
                                    dbc.InputGroupText(
                                        html.I(className="bi bi-search"),
                                        style={"backgroundColor": "#f1f5f9", "borderColor": "#e2e8f0"}
                                    ),
                                ],
                                className="mb-3"
                            ),
                            html.Div(id='search-output-container') 
                        ]),
                        className="shadow-sm border-0 mb-4"
                    ),

                    # Full Data Table Section
                    dbc.Card(
                        dbc.CardBody([
                            html.Div(
                                [
                                    html.I(className="bi bi-table me-2", style={"color": "#6366f1", "fontSize": "1.1rem"}),
                                    html.H5("ตารางข้อมูลทั้งหมด", className="d-inline mb-0", style={"color": "#475569"})
                                ],
                                className="mb-3 d-flex align-items-center"
                            ),
                            html.Div(id='full-data-table-container')
                        ]),
                        className="shadow-sm border-0"
                    )
                ]
            )
        ]
    )

layout = create_review_layout()

# ==================================================
# Callbacks
# ==================================================

def register_callbacks(app):

    @app.callback(
        Output('search-output-container', 'children'),
        Input('member-id-search', 'value')
    )
    def search_member(member_id):
        if not member_id or not str(member_id).strip():
            return html.Div(
                [
                    html.I(className="bi bi-info-circle me-2", style={"color": "#94a3b8"}),
                    "กรอกรหัสสมาชิกเพื่อเริ่มค้นหา"
                ],
                className="text-muted d-flex align-items-center",
                style={"fontSize": "0.9rem"}
            )

        try:
            engine = get_pg_engine()
            search_id = str(member_id).strip()
            
            query = "SELECT * FROM members WHERE member_id = %s"
            df = pd.read_sql(query, engine, params=(search_id,)) 
            engine.dispose()

            if df.empty:
                return dbc.Alert(
                    [
                        html.I(className="bi bi-x-circle-fill me-2"),
                        f"ไม่พบรหัสสมาชิก {search_id} ในระบบ"
                    ],
                    color="danger",
                    className="mt-2 d-flex align-items-center shadow-sm"
                )

            row = df.iloc[0].to_dict()

            # จัดการข้อมูล Income
            raw_income = row.get('income', 0)
            try:
                clean_income = float(str(raw_income).replace(',', ''))
                formatted_income = "{:,.2f} บาท".format(clean_income)
            except (ValueError, TypeError):
                formatted_income = f"{raw_income} บาท"

            # คำนวณระยะเวลาการอนุมัติ
            reg_date = pd.to_datetime(row.get('registration_date'), errors='coerce')
            appr_date = pd.to_datetime(row.get('approval_date'), errors='coerce')
            
            approval_period_text = "ข้อมูลไม่ครบถ้วน"
            approval_badge_color = "#94a3b8"
            
            if pd.notna(reg_date) and pd.notna(appr_date):
                diff = (appr_date - reg_date).days
                approval_period_text = f"{diff} วัน"
                
                # สีตามระยะเวลา
                if diff <= 3:
                    approval_badge_color = "#10b981"  # เขียว
                elif diff <= 7:
                    approval_badge_color = "#f59e0b"  # ส้ม
                else:
                    approval_badge_color = "#ef4444"  # แดง

            # คำนวณอายุ
            age = calculate_age_from_dob(row.get('birthday'))

            # จัดเตรียมข้อมูลแสดงผล
            full_name = f"{row.get('prefix','')} {row.get('name','')} {row.get('surname','')}"

            return dbc.Card(
                [
                    dbc.CardBody([
                        # ชื่อสมาชิก
                        html.Div(
                            [
                                html.I(className="bi bi-person-circle me-2", style={"color": "#6366f1", "fontSize": "1.5rem"}),
                                html.H4(full_name, className="d-inline mb-0", style={"color": "#1e293b"})
                            ],
                            className="mb-4 pb-3 d-flex align-items-center",
                            style={"borderBottom": "2px solid #e2e8f0"}
                        ),
                        
                        # Grid ข้อมูล
                        dbc.Row([
                            # Column 1
                            dbc.Col([
                                html.Div([
                                    html.Label("รหัสสมาชิก", className="text-muted small mb-1"),
                                    html.Div(row.get('member_id'), className="fw-semibold", style={"color": "#1e293b"})
                                ], className="mb-3"),
                                
                                html.Div([
                                    html.Label("อายุ", className="text-muted small mb-1"),
                                    html.Div(
                                        f"{int(age)} ปี" if pd.notna(age) else "N/A",
                                        className="fw-semibold",
                                        style={"color": "#1e293b"}
                                    )
                                ], className="mb-3"),
                                
                                html.Div([
                                    html.Label("รายได้", className="text-muted small mb-1"),
                                    html.Div(formatted_income, className="fw-semibold", style={"color": "#10b981"})
                                ], className="mb-3"),
                                
                                html.Div([
                                    html.Label("อาชีพ", className="text-muted small mb-1"),
                                    html.Div(row.get('career', '-'), className="fw-semibold", style={"color": "#1e293b"})
                                ]),
                            ], md=6),
                            
                            # Column 2
                            dbc.Col([
                                html.Div([
                                    html.Label("วันที่สมัคร", className="text-muted small mb-1"),
                                    html.Div(
                                        reg_date.strftime('%d/%m/%Y') if pd.notna(reg_date) else "-",
                                        className="fw-semibold",
                                        style={"color": "#1e293b"}
                                    )
                                ], className="mb-3"),
                                
                                html.Div([
                                    html.Label("วันที่อนุมัติ", className="text-muted small mb-1"),
                                    html.Div(
                                        appr_date.strftime('%d/%m/%Y') if pd.notna(appr_date) else "-",
                                        className="fw-semibold",
                                        style={"color": "#1e293b"}
                                    )
                                ], className="mb-3"),
                                
                                # ระยะเวลาการอนุมัติ (Highlight)
                                html.Div([
                                    html.Label("⏱️ ระยะเวลาการอนุมัติ", className="text-muted small mb-2"),
                                    html.Div(
                                        approval_period_text,
                                        className="px-3 py-2 rounded-3 text-center fw-bold",
                                        style={
                                            "backgroundColor": f"{approval_badge_color}20",
                                            "color": approval_badge_color,
                                            "fontSize": "1.1rem",
                                            "border": f"2px solid {approval_badge_color}"
                                        }
                                    )
                                ]),
                            ], md=6),
                        ])
                    ])
                ],
                className="mt-3 shadow-sm border-0"
            )

        except Exception as e:
            return dbc.Alert(
                [
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    f"เกิดข้อผิดพลาด: {str(e)}"
                ],
                color="danger",
                className="mt-2 d-flex align-items-center"
            )

    @app.callback(
        Output('full-data-table-container', 'children'),
        Input('url', 'pathname')
    )
    def update_full_table(pathname):
        if pathname != "/review":
            return None
            
        df = load_data()
        
        if df.empty:
            return dbc.Alert(
                [
                    html.I(className="bi bi-info-circle me-2"),
                    "ไม่พบข้อมูลในฐานข้อมูล"
                ],
                color="info",
                className="d-flex align-items-center"
            )
        
        df_display = prepare_df_for_export(df)
        
        return html.Div([
            html.Div(
                f"แสดง {len(df_display):,} รายการ",
                className="mb-2 text-muted",
                style={"fontSize": "0.9rem"}
            ),
            dash_table.DataTable(
                data=df_display.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df_display.columns],
                page_size=15,
                sort_action="native",
                filter_action="native",
                style_table={'overflowX': 'auto'},
                style_header={
                    'backgroundColor': '#f1f5f9',
                    'fontWeight': '600',
                    'color': '#475569',
                    'textAlign': 'center',
                    'padding': '12px',
                    'borderBottom': '2px solid #cbd5e1'
                },
                style_cell={
                    'textAlign': 'center',
                    'padding': '10px',
                    'fontFamily': 'system-ui, -apple-system, sans-serif',
                    'fontSize': '0.9rem',
                    'color': '#1e293b'
                },
                style_data={
                    'borderBottom': '1px solid #e2e8f0'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#f8fafc'
                    }
                ]
            )
        ])