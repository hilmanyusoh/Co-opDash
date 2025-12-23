from dash import html
import dash_bootstrap_components as dbc
import pandas as pd
from typing import Any

# ชุดสีมาตรฐานสำหรับ overview
COLOR_MAP = {
    "primary": "#007bff",   
    "purple": "#6f42c1",    
    "success": "#28a745",   
    "orange": "#fd7e14",    
    "info": "#17a2b8",      #
}

# ==================================================
# 1. Component พื้นฐาน: Single KPI Card
# ==================================================
def render_kpi_card(
    title: str,
    value: Any,
    unit: str = "",
    icon_class: str = "fa-chart-line",
    color_class: str = "primary",
) -> dbc.Card:
    card_color = COLOR_MAP.get(color_class, COLOR_MAP["primary"])
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.I(
                    className=f"fas {icon_class} fa-2x me-3 text-white",
                    style={"opacity": "0.8"}
                ),
                html.Div([
                    html.H6(title, className="text-white-50 mb-1 fw-light", style={"fontSize": "0.85rem"}),
                    html.H3(value, className="text-white fw-bold mb-0"),
                    html.Small(unit, className="text-white-50") if unit else None,
                ], className="text-end"),
            ], className="d-flex justify-content-between align-items-center"),
        ], className="py-3"),
        className="shadow rounded-3 border-0 h-100",
        style={"background": f"linear-gradient(135deg, {card_color} 0%, {card_color}cc 100%)"}
    )


# 2. KPI Overview
def render_overview_kpis(df: pd.DataFrame) -> dbc.Row:
    if df.empty:
        return dbc.Alert("ไม่พบข้อมูลสำหรับการคำนวณสถิติ Overview", color="warning", className="text-center")

    # คำนวณค่าต่างๆ
    total_members = len(df)
    total_branches = df["branch_no"].nunique() if "branch_no" in df.columns else 0
    
    # ตรวจสอบชื่อคอลัมน์จังหวัด (จาก SQL คุณคือ province_name)
    prov_col = "province_name" if "province_name" in df.columns else "province"
    total_provinces = df[prov_col].nunique() if prov_col in df.columns else 0

    # คำนวณรายได้รวม
    total_income = df["Income_Clean"].sum() if "Income_Clean" in df.columns else 0
    income_display = f"{total_income / 1_000_000:.2f}M" if total_income >= 1_000_000 else f"{total_income:,.0f}"

    return dbc.Row([
        dbc.Col(render_kpi_card("สมาชิกทั้งหมด", f"{total_members:,}", "คน", "fa-users", "primary"), lg=3, md=6, className="mb-3"),
        dbc.Col(render_kpi_card("สาขาที่เปิดให้บริการ", f"{total_branches:,}", "สาขา", "fa-store", "purple"), lg=3, md=6, className="mb-3"),
        dbc.Col(render_kpi_card("จังหวัดที่ครอบคลุม", f"{total_provinces:,}", "จังหวัด", "fa-map-marked-alt", "success"), lg=3, md=6, className="mb-3"),
        dbc.Col(render_kpi_card("รายได้รวมสมาชิก", income_display, "บาท", "fa-hand-holding-usd", "orange"), lg=3, md=6, className="mb-3"),
    ], className="g-3")


# 3. KPI Demographics

def render_demographic_kpis(df: pd.DataFrame) -> dbc.Row:
    if df.empty:
        return dbc.Alert("ไม่พบข้อมูลสำหรับการวิเคราะห์ Demographics", color="warning", className="text-center")

    # 1. นับเพศชาย-หญิง (นาย=ชาย, นาง/นางสาว=หญิง)
    male_count = 0
    female_count = 0
    if "gender_name" in df.columns:
        male_count = len(df[df["gender_name"] == "นาย"])
        female_count = len(df[df["gender_name"].isin(["นาง", "นางสาว"])])

    # 2. คำนวณ Generation (Gen ยอดนิยม)
    # ต้องมีคอลัมน์ birthday และถูกแปลงเป็น datetime แล้วใน preprocess_data
    popular_gen = "N/A"
    if "birthday" in df.columns and not df["birthday"].isnull().all():
        def get_generation(b_date):
            if pd.isnull(b_date): return None
            year = b_date.year
            if 1946 <= year <= 1964: return "Baby Boomer"
            if 1965 <= year <= 1980: return "Gen X"
            if 1981 <= year <= 1996: return "Gen Y"
            if 1997 <= year <= 2012: return "Gen Z"
            return "Other"
        
        df['gen'] = df['birthday'].apply(get_generation)
        mode_gen = df['gen'].mode()
        if not mode_gen.empty:
            popular_gen = mode_gen[0]

    # 3. รายได้เฉลี่ย (Average Income)
    avg_income = 0
    if "Income_Clean" in df.columns:
        # คำนวณเฉพาะคนที่มีรายได้มากกว่า 0 เพื่อความแม่นยำของค่าเฉลี่ย
        valid_income = df[df["Income_Clean"] > 0]["Income_Clean"]
        if not valid_income.empty:
            avg_income = valid_income.mean()

    return dbc.Row([
        # 1. ชาย ทั้งหมด
        dbc.Col(render_kpi_card(
            title="สมาชิกเพศชาย",
            value=f"{male_count:,}",
            unit="คน",
            icon_class="fa-mars",
            color_class="primary"
        ), lg=3, md=6, className="mb-3"),

        # 2. หญิง ทั้งหมด
        dbc.Col(render_kpi_card(
            title="สมาชิกเพศหญิง",
            value=f"{female_count:,}",
            unit="คน",
            icon_class="fa-venus",
            color_class="orange"
        ), lg=3, md=6, className="mb-3"),

        # 3. Generation (กลุ่มหลัก)
        dbc.Col(render_kpi_card(
            title="กลุ่ม Gen หลัก",
            value=popular_gen,
            unit="Majority",
            icon_class="fa-id-card",
            color_class="purple"
        ), lg=3, md=6, className="mb-3"),

        # 4. รายได้เฉลี่ย
        dbc.Col(render_kpi_card(
            title="รายได้เฉลี่ย",
            value=f"{avg_income:,.0f}",
            unit="บาท / เดือน",
            icon_class="fa-wallet",
            color_class="success"
        ), lg=3, md=6, className="mb-3"),
    ], className="g-3")