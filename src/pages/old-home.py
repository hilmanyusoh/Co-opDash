# src/pages/home.py

from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import datetime
import re

from sqlalchemy import text

from ..data_manager import get_pg_engine, calculate_age_from_dob


# Layout


def create_home_layout():
    member_count = 0
    db_status = False

    try:
        engine = get_pg_engine()
        if engine is not None:
            member_count = pd.read_sql("SELECT COUNT(*) FROM members", engine).iloc[
                0, 0
            ]
            db_status = True
            engine.dispose()
    except Exception:
        db_status = False

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
                                "บันทึกข้อมูลสมาชิกใหม่",
                                style={"color": "#1e293b", "fontWeight": "600"},
                                className="mb-2",
                            ),
                            html.P(
                                "กรอกข้อมูลสมาชิกเพื่อเพิ่มเข้าสู่ระบบ",
                                className="text-muted mb-0",
                                style={"fontSize": "0.95rem"},
                            ),
                        ],
                    ),
                    # Status Badge
                    dbc.Card(
                        dbc.CardBody(
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Div(
                                            [
                                                html.I(
                                                    className=f"bi bi-{'check-circle-fill' if db_status else 'x-circle-fill'} me-2",
                                                    style={
                                                        "fontSize": "1.2rem",
                                                        "color": (
                                                            "#10b981"
                                                            if db_status
                                                            else "#ef4444"
                                                        ),
                                                    },
                                                ),
                                                html.Span(
                                                    (
                                                        "เชื่อมต่อฐานข้อมูลสำเร็จ"
                                                        if db_status
                                                        else "ไม่สามารถเชื่อมต่อฐานข้อมูล"
                                                    ),
                                                    style={
                                                        "fontWeight": "500",
                                                        "color": "#1e293b",
                                                    },
                                                ),
                                            ],
                                            className="d-flex align-items-center",
                                        ),
                                        md=6,
                                        className="mb-2 mb-md-0",
                                    ),
                                    dbc.Col(
                                        html.Div(
                                            [
                                                html.I(
                                                    className="bi bi-people-fill me-2",
                                                    style={"color": "#6366f1"},
                                                ),
                                                html.Span(
                                                    "จำนวนสมาชิก: ",
                                                    className="text-muted",
                                                ),
                                                html.Strong(
                                                    f"{member_count:,}",
                                                    style={"color": "#1e293b"},
                                                ),
                                                html.Span(
                                                    " รายการ", className="text-muted"
                                                ),
                                            ],
                                            className="d-flex align-items-center",
                                        ),
                                        md=6,
                                    ),
                                ]
                            )
                        ),
                        className="shadow-sm border-0 mb-4",
                        style={
                            "borderLeft": f"4px solid {'#10b981' if db_status else '#ef4444'}"
                        },
                    ),
                    # Form Section
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                "ข้อมูลส่วนตัว",
                                                className="mb-4",
                                                style={
                                                    "color": "#475569",
                                                    "fontWeight": "600",
                                                },
                                            ),
                                            # รหัสสมาชิก
                                            dbc.Label(
                                                "รหัสสมาชิก",
                                                className="fw-semibold mb-1",
                                                style={
                                                    "color": "#64748b",
                                                    "fontSize": "0.9rem",
                                                },
                                            ),
                                            dbc.Input(
                                                id="member-id",
                                                placeholder="กรอกรหัสสมาชิก",
                                                className="mb-3",
                                                style={"borderColor": "#e2e8f0"},
                                            ),
                                            # คำนำหน้า
                                            dbc.Label(
                                                "คำนำหน้า",
                                                className="fw-semibold mb-1",
                                                style={
                                                    "color": "#64748b",
                                                    "fontSize": "0.9rem",
                                                },
                                            ),
                                            dbc.Select(
                                                id="member-prefix",
                                                options=[
                                                    {"label": "นาย", "value": "นาย"},
                                                    {"label": "นาง", "value": "นาง"},
                                                    {
                                                        "label": "นางสาว",
                                                        "value": "นางสาว",
                                                    },
                                                ],
                                                value="นาย",
                                                className="mb-3",
                                                style={"borderColor": "#e2e8f0"},
                                            ),
                                            # ชื่อ
                                            dbc.Label(
                                                "ชื่อ",
                                                className="fw-semibold mb-1",
                                                style={
                                                    "color": "#64748b",
                                                    "fontSize": "0.9rem",
                                                },
                                            ),
                                            dbc.Input(
                                                id="member-name",
                                                placeholder="กรอกชื่อ",
                                                className="mb-3",
                                                style={"borderColor": "#e2e8f0"},
                                            ),
                                            # นามสกุล
                                            dbc.Label(
                                                "นามสกุล",
                                                className="fw-semibold mb-1",
                                                style={
                                                    "color": "#64748b",
                                                    "fontSize": "0.9rem",
                                                },
                                            ),
                                            dbc.Input(
                                                id="member-surname",
                                                placeholder="กรอกนามสกุล",
                                                className="mb-3",
                                                style={"borderColor": "#e2e8f0"},
                                            ),
                                            # วันเกิด
                                            dbc.Label(
                                                "วันเกิด",
                                                className="fw-semibold mb-1",
                                                style={
                                                    "color": "#64748b",
                                                    "fontSize": "0.9rem",
                                                },
                                            ),
                                            dbc.Input(
                                                id="member-dob",
                                                placeholder="วว/ดด/ปปปป (เช่น 15/08/2543)",
                                                className="mb-2",
                                                style={"borderColor": "#e2e8f0"},
                                            ),
                                            html.Div(
                                                id="member-age-display",
                                                className="mb-3",
                                                style={
                                                    "color": "#6366f1",
                                                    "fontSize": "0.9rem",
                                                    "fontWeight": "500",
                                                },
                                            ),
                                        ]
                                    ),
                                    className="shadow-sm border-0 h-100",
                                ),
                                lg=6,
                                className="mb-4",
                            ),
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                "💼 ข้อมูลการทำงาน",
                                                className="mb-4",
                                                style={
                                                    "color": "#475569",
                                                    "fontWeight": "600",
                                                },
                                            ),
                                            # รายได้
                                            dbc.Label(
                                                "รายได้ (บาท)",
                                                className="fw-semibold mb-1",
                                                style={
                                                    "color": "#64748b",
                                                    "fontSize": "0.9rem",
                                                },
                                            ),
                                            dbc.Input(
                                                id="member-income",
                                                placeholder="กรอกรายได้",
                                                className="mb-3",
                                                style={"borderColor": "#e2e8f0"},
                                            ),
                                            # อาชีพ
                                            dbc.Label(
                                                "อาชีพ",
                                                className="fw-semibold mb-1",
                                                style={
                                                    "color": "#64748b",
                                                    "fontSize": "0.9rem",
                                                },
                                            ),
                                            dbc.Input(
                                                id="member-occupation",
                                                placeholder="กรอกอาชีพ (ถ้ามี)",
                                                className="mb-3",
                                                style={"borderColor": "#e2e8f0"},
                                            ),
                                            # รหัสสาขา
                                            dbc.Label(
                                                "รหัสสาขา",
                                                className="fw-semibold mb-1",
                                                style={
                                                    "color": "#64748b",
                                                    "fontSize": "0.9rem",
                                                },
                                            ),
                                            dbc.Input(
                                                id="member-branch",
                                                placeholder="กรอกรหัสสาขา (ถ้ามี)",
                                                className="mb-3",
                                                style={"borderColor": "#e2e8f0"},
                                            ),
                                            # วันที่สมัคร
                                            dbc.Label(
                                                "วันที่สมัคร",
                                                className="fw-semibold mb-1",
                                                style={
                                                    "color": "#64748b",
                                                    "fontSize": "0.9rem",
                                                },
                                            ),
                                            dbc.Input(
                                                id="member-regdate",
                                                placeholder="วว/ดด/ปปปป (ถ้ามี)",
                                                className="mb-3",
                                                style={"borderColor": "#e2e8f0"},
                                            ),
                                            # วันที่อนุมัติ
                                            dbc.Label(
                                                "วันที่อนุมัติ",
                                                className="fw-semibold mb-1",
                                                style={
                                                    "color": "#64748b",
                                                    "fontSize": "0.9rem",
                                                },
                                            ),
                                            dbc.Input(
                                                id="member-apprdate",
                                                placeholder="วว/ดด/ปปปป (ถ้ามี)",
                                                className="mb-3",
                                                style={"borderColor": "#e2e8f0"},
                                            ),
                                        ]
                                    ),
                                    className="shadow-sm border-0 h-100",
                                ),
                                lg=6,
                                className="mb-4",
                            ),
                        ]
                    ),
                    # Submit Button & Message
                    dbc.Row(
                        dbc.Col(
                            [
                                dbc.Button(
                                    [
                                        html.I(className="bi bi-check-circle me-2"),
                                        "บันทึกข้อมูล",
                                    ],
                                    id="submit-button",
                                    size="lg",
                                    className="w-100 shadow-sm",
                                    style={
                                        "background": "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
                                        "border": "none",
                                        "fontWeight": "600",
                                        "padding": "12px",
                                    },
                                ),
                                html.Div(id="output-message", className="mt-3"),
                            ]
                        )
                    ),
                    # Required Fields Note
                    html.Div(
                        [
                            html.Small(
                                "📌 ต้องกรอก: รหัสสมาชิก, ชื่อ, นามสกุล, วันเกิด, รายได้",
                                className="text-muted",
                                style={"fontSize": "0.85rem"},
                            )
                        ],
                        className="mt-3 text-center",
                    ),
                ],
            )
        ],
    )


layout = create_home_layout()


# Callbacks
def register_callbacks(app):

    @app.callback(
        Output("member-age-display", "children"),
        Input("member-dob", "value"),
    )
    def update_age(dob):
        if not dob:
            return
        age = calculate_age_from_dob(dob)
        if pd.notna(age):
            return f"🎂 อายุ: {int(age)} ปี"
        return

    # บันทึกข้อมูลสมาชิก

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
        n_clicks,
        member_id,
        prefix,
        name,
        surname,
        dob,
        income,
        career,
        branch,
        reg_date,
        appr_date,
    ):
        try:
            if not all([member_id, name, surname, dob, income]):
                return dbc.Alert(
                    [
                        html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    ],
                    color="warning",
                    className="d-flex align-items-center",
                )

            engine = get_pg_engine()
            if engine is None:
                return dbc.Alert(
                    [
                        html.I(className="bi bi-x-circle-fill me-2"),
                    ],
                    color="danger",
                    className="d-flex align-items-center",
                )

            # Clean & convert data

            income_val = float(re.sub(r"[^0-9.]", "", income))

            dob_dt = datetime.datetime.strptime(dob, "%d/%m/%Y").date()
            reg_dt = (
                datetime.datetime.strptime(reg_date, "%d/%m/%Y").date()
                if reg_date
                else None
            )
            appr_dt = (
                datetime.datetime.strptime(appr_date, "%d/%m/%Y").date()
                if appr_date
                else None
            )

            approval_days = (appr_dt - reg_dt).days if reg_dt and appr_dt else None

            # SQL Insert
            sql = text(
                """
                INSERT INTO members (
                member_id, prefix, name, surname, birthday,
                income, career, branch_code,
                registration_date, approval_date
            ) VALUES (
                :member_id, :prefix, :name, :surname, :birthday,
                :income, :career, :branch_code,
                :registration_date, :approval_date
            )
        """
            )

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

            return dbc.Alert(
                [
                    html.I(className="bi bi-check-circle-fill me-2"),
                    f"บันทึกข้อมูลสมาชิก {name} {surname} สำเร็จแล้ว",
                ],
                color="success",
                duration=4000,
                className="d-flex align-items-center shadow-sm",
            )

        except Exception as e:
            msg = str(e)
            if "duplicate key" in msg.lower():
                msg = f"รหัสสมาชิก {member_id} มีอยู่ในระบบแล้ว"
            elif "invalid input" in msg.lower():
                msg = "รูปแบบข้อมูลไม่ถูกต้อง (ตรวจสอบวันที่และตัวเลข)"
            else:
                msg = "เกิดข้อผิดพลาดในการบันทึกข้อมูล"

            return dbc.Alert(
                [html.I(className="bi bi-x-circle-fill me-2"), msg],
                color="danger",
                className="d-flex align-items-center",
            )
