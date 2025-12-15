from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import pandas as pd



from ..data_manager import (
    get_pg_engine,
    load_data,
    prepare_df_for_export,
    calculate_age_from_dob
)

PRIMARY_COLOR = "#007bff"


# ==================================================
# Layout
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

            row = df.iloc[0].to_dict()

            age = calculate_age_from_dob(row.get("dob"))
            row["อายุ (คำนวณ)"] = f"{age} ปี" if pd.notna(age) else "N/A"
            row["income"] = f"{row.get('income', 0):,.0f}"

            display_map = {
                "member_id": "รหัสสมาชิก",
                "prefix": "คำนำหน้า",
                "first_name": "ชื่อ",
                "last_name": "สกุล",
                "dob": "ว/ด/ป เกิด",
                "income": "รายได้ (บาท)",
                "career": "อาชีพ",
                "branch_code": "รหัสสาขา",
                "register_date": "วันที่สมัครสมาชิก",
                "approve_date": "วันที่อนุมัติ",
                "approval_days": "ระยะเวลาอนุมัติ_วัน",
                "อายุ (คำนวณ)": "อายุ (คำนวณ)",
            }

            result = [
                {"คุณสมบัติ": display_map[k], "ค่า": row[k]}
                for k in display_map
                if k in row
            ]

            return dash_table.DataTable(
                columns=[
                    {"name": "คุณสมบัติ", "id": "คุณสมบัติ"},
                    {"name": "ค่า", "id": "ค่า"},
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
            return dbc.Alert(f"❌ เกิดข้อผิดพลาด: {e}", color="danger")

    # ----------------------------------------------
    # Full data table
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
