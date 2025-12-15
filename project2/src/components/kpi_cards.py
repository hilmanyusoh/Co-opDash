# src/components/kpi_cards.py

from dash import html
import dash_bootstrap_components as dbc
import pandas as pd
from typing import Any

# =========================
# สีของการ์ด
# =========================
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
    color_class: str = "primary"
) -> dbc.Card:
    """สร้าง KPI Card เดี่ยว"""
    
    card_color = COLOR_MAP.get(color_class, COLOR_MAP["primary"])

    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.I(
                    className=f"fas {icon_class} fa-2x me-3 text-white",
                    style={"opacity": "0.9"}
                ),
                html.Div([
                    html.H6(
                        title,
                        className="text-white-50 mb-1 fw-light",
                        style={"fontSize": "0.85rem"}
                    ),
                    html.H3(
                        value,
                        className="text-white fw-bold mb-0"
                    ),
                    html.Small(
                        unit,
                        className="text-white-50"
                    ) if unit else None,
                ],
                className="text-end"),
            ],
            className="d-flex justify-content-between align-items-center"),
        ],
        className="py-3"),
        className="shadow rounded-3 border-0 h-100",
        style={
            "background": f"linear-gradient(135deg, {card_color} 0%, {card_color}cc 100%)",
        },
    )


# =========================
# KPI Cards Group
# =========================
def render_kpi_cards(df: pd.DataFrame) -> dbc.Row:
    """สร้างกลุ่ม KPI Cards"""
    
    if df.empty:
        return dbc.Alert(
            [
                html.I(className="fas fa-exclamation-circle me-2"),
                "ไม่พบข้อมูลสำหรับแสดง KPI"
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
    
    # 3. จำนวนสาขา
    num_branches = "N/A"
    if "branch_code" in df.columns and not df["branch_code"].isnull().all():
        num_branches = df["branch_code"].nunique()
    
    # 4. รายได้เฉลี่ย
    income_value = "N/A"
    if "Income_Clean" in df.columns and not df["Income_Clean"].isnull().all():
        try:
            avg_income = df["Income_Clean"].mean()
            if pd.notna(avg_income):
                income_value = f"{avg_income:,.0f}"
        except:
            pass
    
    return dbc.Row([
        dbc.Col(
            render_kpi_card(
                title="สมาชิกทั้งหมด",
                value=f"{total_members:,}",
                unit="คน",
                icon_class="fa-users",
                color_class="primary",
            ),
            lg=3, md=6, xs=12, className="mb-3",
        ),
        dbc.Col(
            render_kpi_card(
                title="ช่วงอายุยอดนิยม",
                value=age_value,
                unit="ปี",
                icon_class="fa-birthday-cake",
                color_class="purple",
            ),
            lg=3, md=6, xs=12, className="mb-3",
        ),
        dbc.Col(
            render_kpi_card(
                title="จำนวนสาขา",
                value=num_branches if isinstance(num_branches, str) else f"{num_branches:,}",
                unit="สาขา",
                icon_class="fa-building",
                color_class="success",
            ),
            lg=3, md=6, xs=12, className="mb-3",
        ),
        dbc.Col(
            render_kpi_card(
                title="รายได้เฉลี่ย",
                value=income_value,
                unit="บาท",
                icon_class="fa-dollar-sign",
                color_class="orange",
            ),
            lg=3, md=6, xs=12, className="mb-3",
        ),
    ], className="g-3")