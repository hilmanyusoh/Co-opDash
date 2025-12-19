# src/components/kpi_cards.py

from dash import html
import dash_bootstrap_components as dbc
import pandas as pd
from typing import Any


# สีของการ์ด

COLOR_MAP = {
    "primary": "#007bff",
    "purple": "#6f42c1",
    "success": "#28a745",
    "orange": "#fd7e14",
    "info": "#17a2b8",
}


# =========================
# Single KPI Card
# =========================
def render_kpi_card(
    title: str,
    value: Any,
    unit: str = "",
    icon_class: str = "fa-chart-line",
    color_class: str = "primary",
) -> dbc.Card:
    """สร้าง KPI Card เดี่ยว"""

    card_color = COLOR_MAP.get(color_class, COLOR_MAP["primary"])

    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.I(
                            className=f"fas {icon_class} fa-2x me-3 text-white",
                            style={"opacity": "0.9"},
                        ),
                        html.Div(
                            [
                                html.H6(
                                    title,
                                    className="text-white-50 mb-1 fw-light",
                                    style={"fontSize": "0.85rem"},
                                ),
                                html.H3(value, className="text-white fw-bold mb-0"),
                                (
                                    html.Small(unit, className="text-white-50")
                                    if unit
                                    else None
                                ),
                            ],
                            className="text-end",
                        ),
                    ],
                    className="d-flex justify-content-between align-items-center",
                ),
            ],
            className="py-3",
        ),
        className="shadow rounded-3 border-0 h-100",
        style={
            "background": f"linear-gradient(135deg, {card_color} 0%, {card_color}cc 100%)",
        },
    )


# KPI Cards Group (ส่วนที่แก้ไข Logic)


def render_kpi_cards(df: pd.DataFrame) -> dbc.Row:
    """สร้างกลุ่ม KPI Cards"""

    if df.empty:
        return dbc.Alert(
            [
                html.I(className="fas fa-exclamation-circle me-2"),
                "ไม่พบข้อมูลสำหรับแสดง KPI",
            ],
            color="warning",
            className="mb-4 text-center",
        )

    # 1. จำนวนสมาชิกทั้งหมด
    total_members = len(df)

    # 2. ช่วงอายุยอดนิยม
    age_value = "N/A"
    if "Age_Group" in df.columns and not df["Age_Group"].isnull().all():
        try:
            mode_series = df["Age_Group"].mode()
            if len(mode_series) > 0:
                age_value = str(mode_series.iloc[0])
        except:
            pass

    # 3. สาขาที่สมาชิกใช้บริการมากที่สุด
    branch_value = "N/A"
    if "Branch_code" in df.columns and not df["Branch_code"].isnull().all():
        try:
            mode_series = df["Branch_code"].mode()
            if len(mode_series) > 0:
                branch_value = str(mode_series.iloc[0])
        except:
            pass

    # 4. รายได้ที่สมาชิกมีมากที่สุด (Mode Income)
    income_value = "N/A"
    if "Income_Clean" in df.columns and not df["Income_Clean"].isnull().all():
        try:
            non_zero_income = df[df["Income_Clean"] > 0]["Income_Clean"]

            if not non_zero_income.empty:
                # ใช้ .mode() เพื่อหารายได้ที่พบบ่อยที่สุด
                mode_income = non_zero_income.mode()

                if len(mode_income) > 0:
                    # แสดง Mode ตัวแรก และจัดรูปแบบให้มีจุลภาค
                    income_value = f"{mode_income.iloc[0]:,.0f}"
        except:
            pass

    return dbc.Row(
        [
            dbc.Col(
                render_kpi_card(
                    title="สมาชิกทั้งหมด",
                    value=f"{total_members:,}",
                    unit="คน",
                    icon_class="fa-users",
                    color_class="primary",
                ),
                lg=3,
                md=6,
                xs=12,
                className="mb-3",
            ),
            dbc.Col(
                render_kpi_card(
                    title="ช่วงอายุยอดนิยม",
                    value=age_value,
                    unit="ปี",
                    icon_class="fa-birthday-cake",
                    color_class="purple",
                ),
                lg=3,
                md=6,
                xs=12,
                className="mb-3",
            ),
            dbc.Col(
                render_kpi_card(
                    title="สาขาที่ใช้บริการมากที่สุด",
                    value=branch_value,
                    unit="รหัสสาขา",
                    icon_class="fa-building",
                    color_class="success",
                ),
                lg=3,
                md=6,
                xs=12,
                className="mb-3",
            ),
            dbc.Col(
                render_kpi_card(
                    # [แก้ไข Title]: เปลี่ยนชื่อหัวข้อ
                    title="รายได้ที่พบบ่อยที่สุด",
                    value=income_value,
                    unit="บาท",
                    icon_class="fa-dollar-sign",
                    color_class="orange",
                ),
                lg=3,
                md=6,
                xs=12,
                className="mb-3",
            ),
        ],
        className="g-3",
    )
