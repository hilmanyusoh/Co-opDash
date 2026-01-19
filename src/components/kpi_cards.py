from dash import html
import dash_bootstrap_components as dbc
import pandas as pd
from typing import Any
from datetime import datetime

from .theme import THEME

# ==================================================
# KPI Card (Theme-based)
# ==================================================
def render_kpi_card(
    title: str,
    value: Any,
    unit: str = "",
    icon_class: str = "fa-chart-line",
    color: str = "primary",
) -> dbc.Card:

    accent = THEME.get(color, THEME["primary"])

    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.Div(
                            html.I(
                                className=f"fas {icon_class}",
                                style={
                                    "color": accent,
                                    "fontSize": "26px",
                                },
                            ),
                            className="me-3",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    title,
                                    style={
                                        "fontSize": "0.85rem",
                                        "color": THEME["muted"],
                                        "fontWeight": 600,
                                    },
                                ),
                                html.Div(
                                    value,
                                    style={
                                        "fontSize": "1.6rem",
                                        "fontWeight": 700,
                                        "color": THEME["text"],
                                    },
                                ),
                                html.Div(
                                    unit,
                                    style={
                                        "fontSize": "0.75rem",
                                        "color": THEME["muted"],
                                    },
                                )
                                if unit
                                else None,
                            ]
                        ),
                    ],
                    className="d-flex align-items-center",
                )
            ],
            className="py-3 px-3",
        ),
        className="shadow-sm rounded-3 border-0 h-100",
        style={
            "borderLeft": f"5px solid {accent}",
            "backgroundColor": THEME["bg_card"],
        },
    )

# ==================================================
# Overview KPI
# ==================================================
def render_overview_kpis(df: pd.DataFrame) -> dbc.Row:
    if df.empty:
        return dbc.Alert("ไม่พบข้อมูล Overview", color="warning")

    total_members = len(df)
    total_branches = df["branch_no"].nunique() if "branch_no" in df.columns else 0
    prov_col = "province_name" if "province_name" in df.columns else "province"
    total_provinces = df[prov_col].nunique() if prov_col in df.columns else 0
    total_income = df["Income_Clean"].sum() if "Income_Clean" in df.columns else 0

    income_display = (
        f"{total_income/1_000_000:.2f}M"
        if total_income >= 1_000_000
        else f"{total_income:,.0f}"
    )

    return dbc.Row(
        [
            dbc.Col(render_kpi_card("สมาชิกทั้งหมด", f"{total_members:,}", "คน", "fa-users", "primary"), lg=3, md=6),
            dbc.Col(render_kpi_card("สาขา", f"{total_branches:,}", "สาขา", "fa-store", "info"), lg=3, md=6),
            dbc.Col(render_kpi_card("จังหวัด", f"{total_provinces:,}", "จังหวัด", "fa-map", "success"), lg=3, md=6),
            dbc.Col(render_kpi_card("รายได้รวม", income_display, "บาท", "fa-coins", "orange"), lg=3, md=6),
        ],
        className="g-3 mb-4",
    )

# ==================================================
# 3. KPI member 
# ==================================================
def render_member_kpis(df: pd.DataFrame) -> dbc.Row:
    if df.empty:
        return dbc.Alert("ไม่พบข้อมูล member", color="warning", className="text-center")

    total_members = len(df)
    male_count = len(df[df["gender_name"] == "นาย"]) if "gender_name" in df.columns else 0
    female_count = len(df[df["gender_name"].isin(["นาง", "นางสาว"])]) if "gender_name" in df.columns else 0

    popular_gen = "N/A"
    if "birthday" in df.columns and not df["birthday"].isnull().all():
        df['birthday'] = pd.to_datetime(df['birthday'], errors='coerce')
        def get_gen(b_date):
            if pd.isnull(b_date): return None
            y = b_date.year
            if 1946 <= y <= 1964: return "Baby Boomer"
            if 1965 <= y <= 1980: return "Gen X"
            if 1981 <= y <= 1996: return "Gen Y"
            return "Gen Z"
        df['gen_temp'] = df['birthday'].apply(get_gen)
        popular_gen = df['gen_temp'].mode()[0] if not df['gen_temp'].mode().empty else "N/A"

    return dbc.Row([
        dbc.Col(render_kpi_card("สมาชิกทั้งหมด", f"{total_members:,}", "คน", "fa-users", "red"), lg=3, md=6),
        dbc.Col(render_kpi_card("เพศชาย", f"{male_count:,}", "คน", "fa-mars", "success"), lg=3, md=6),
        dbc.Col(render_kpi_card("เพศหญิง", f"{female_count:,}", "คน", "fa-venus", "pink"), lg=3, md=6),
        dbc.Col(render_kpi_card("กลุ่ม Gen หลัก", popular_gen, "ส่วนใหญ่", "fa-id-card", "purple"), lg=3, md=6),
    ], className="g-3 mb-4")

import pandas as pd
from dash import html
import dash_bootstrap_components as dbc

# ==================================================
# Branch KPI (เวอร์ชันสมบูรณ์)
# ==================================================
def render_branch_kpis(df: pd.DataFrame) -> dbc.Row:
    if df.empty:
        return dbc.Alert("ไม่พบข้อมูลสาขา", color="warning", className="text-center")

    # -------------------------------
    # 1. ตั้งค่าคอลัมน์สาขา
    # -------------------------------
    branch_col = "branch_name" if "branch_name" in df.columns else "branch_no"
    total_branches = df[branch_col].nunique() if branch_col in df.columns else 0

    # -------------------------------
    # 2. สาขาที่มีสมาชิกมากที่สุด
    # -------------------------------
    top_branch = "N/A"
    top_count = 0
    if total_branches > 0:
        counts = df[branch_col].value_counts()
        top_branch = counts.idxmax()
        top_count = counts.max()

    # -------------------------------
    # 3. รายได้รวมทุกสาขา
    # -------------------------------
    total_income_pool = (
        df["Income_Clean"].sum()
        if "Income_Clean" in df.columns
        else 0
    )

    # -------------------------------
    # 4. สมาชิกใหม่ล่าสุด (เดือนล่าสุดในข้อมูล)
    # -------------------------------
    latest_members_count = 0
    latest_month_label = ""

    if "registration_date" in df.columns:
        df["registration_date"] = pd.to_datetime(df["registration_date"], errors="coerce")
        valid_dates = df["registration_date"].dropna()

        if not valid_dates.empty:
            latest_date = valid_dates.max()
            y, m = latest_date.year, latest_date.month

            latest_members_count = len(
                df[
                    (df["registration_date"].dt.year == y) &
                    (df["registration_date"].dt.month == m)
                ]
            )

            thai_months = [
                "", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
                "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
            ]
            latest_month_label = f"{thai_months[m]} {y}"

    # -------------------------------
    # 5. Helper: format ตัวเลข
    # -------------------------------
    def format_val(val: float) -> str:
        if val >= 1_000_000:
            return f"{val / 1_000_000:.2f}M"
        elif val >= 1_000:
            return f"{val / 1_000:.1f}K"
        return f"{val:,.0f}"

    # -------------------------------
    # 6. Render KPI Cards
    # -------------------------------
    return dbc.Row(
        [
            dbc.Col(
                render_kpi_card("สาขาทั้งหมด",f"{total_branches:,}","แห่ง","fa-store","primary",),
                lg=3, md=6,
            ),

            dbc.Col(
                render_kpi_card("สาขาที่มีสมาชิกสูงสุด",str(top_branch),f"{top_count:,} คน","fa-users","info",),
                lg=3, md=6,
            ),

            dbc.Col(
                render_kpi_card("รายได้รวมทุกสาขา",f"฿{format_val(total_income_pool)}","บาท","fa-sack-dollar","success",),
                lg=3, md=6,
            ),

            dbc.Col(
                render_kpi_card("สมาชิกใหม่ล่าสุด",f"{latest_members_count:,}",f"({latest_month_label})","fa-user-plus","purple",),
                lg=3, md=6,
            ),
        ],
        className="g-3 mb-4",
    )

# ==================================================
# 5. KPI Address 
# ==================================================
def render_address_kpis(df: pd.DataFrame) -> dbc.Row:
    if df.empty:
        return dbc.Alert("ไม่พบข้อมูลที่อยู่", color="warning", className="text-center")

    # คำนวณ Unique values โดยใช้ชื่อคอลัมน์จริงจาก SQL JOIN
    n_province = df['province_name'].nunique() if 'province_name' in df.columns else 0
    n_district = df['district_area'].nunique() if 'district_area' in df.columns else 0
    n_subdistrict = df['sub_area'].nunique() if 'sub_area' in df.columns else 0
    n_village = df['village_no'].nunique() if 'village_no' in df.columns else 0

    return dbc.Row([
        dbc.Col(render_kpi_card("จังหวัดทั้งหมด", f"{n_province:,}", "จังหวัด", "fa-map-location-dot", "primary"), lg=3, md=6),
        dbc.Col(render_kpi_card("อำเภอทั้งหมด", f"{n_district:,}", "อำเภอ", "fa-city", "success"), lg=3, md=6),
        dbc.Col(render_kpi_card("ตำบลทั้งหมด", f"{n_subdistrict:,}", "ตำบล", "fa-house-chimney-window", "orange"), lg=3, md=6),
        dbc.Col(render_kpi_card("หมู่บ้านทั้งหมด", f"{n_village:,}", "หมู่บ้าน", "fa-tree-city", "red"), lg=3, md=6),
    ], className="g-3 mb-4")

# ==================================================
# 6. KPI Performance 
# ==================================================
def render_performance_kpis(df: pd.DataFrame) -> dbc.Row:
    if df.empty:
        return dbc.Alert("ไม่พบข้อมูลสำหรับการวิเคราะห์ประสิทธิภาพ", color="warning")

    # เตรียมข้อมูลวันที่
    temp_df = df.copy()
    temp_df['reg_date'] = pd.to_datetime(temp_df['registration_date'], errors='coerce')
    temp_df = temp_df.dropna(subset=['reg_date']).sort_values('reg_date')

    # 1. Monthly Growth 6 เดือนล่าสุด
    monthly_counts = temp_df.set_index('reg_date').resample('ME').size()
    avg_growth_per_month = monthly_counts.tail(6).mean() if not monthly_counts.empty else 0
    
    # 2. คาดการณ์สมาชิกในอีก 12 เดือน
    current_members = len(temp_df)
    projected_12m = current_members + (avg_growth_per_month * 12)

    # 3. Growth Rate (%) ปีต่อปี
    current_year = pd.Timestamp.now().year
    this_year_count = len(temp_df[temp_df['reg_date'].dt.year == current_year])
    last_year_count = len(temp_df[temp_df['reg_date'].dt.year == current_year - 1])
    
    growth_rate = 0
    if last_year_count > 0:
        growth_rate = ((this_year_count - last_year_count) / last_year_count) * 100
    
    # 4. ประมาณการรายได้รวมในอนาคต
    avg_income = temp_df["Income_Clean"].mean() if "Income_Clean" in temp_df.columns else 0
    forecasted_income = projected_12m * avg_income

    return dbc.Row([
        dbc.Col(render_kpi_card("เป้าหมายสมาชิก (12 ด.)", f"{int(projected_12m):,}", "คน (Forecast)", "fa-chart-line", "primary"), lg=3, md=6),
        dbc.Col(render_kpi_card("อัตราการเติบโตปีนี้", f"{growth_rate:+.1f}%", "เทียบปีที่แล้ว", "fa-arrow-up", "success"), lg=3, md=6),
        dbc.Col(render_kpi_card("ประมาณการรายได้สะสม", f"{forecasted_income / 1_000_000:.1f}M", "บาท (Forecast)", "fa-coins", "purple"), lg=3, md=6),
        dbc.Col(render_kpi_card("อัตราสมาชิกใหม่", f"{int(avg_growth_per_month)}", "คน / เดือน", "fa-user-plus", "info"), lg=3, md=6),
    ], className="g-3 mb-4")
    
# ==================================================
# 7. KPI Amount 
# ==================================================
def render_amount_kpis(df: pd.DataFrame) -> dbc.Row:   
    # ตรวจสอบว่ามีข้อมูลและคอลัมน์ที่จำเป็นหรือไม่
    required_cols = ["income", "net_yearly_income", "yearly_debt_payments"]
    if df.empty or not all(col in df.columns for col in required_cols):
        return dbc.Alert("ไม่พบข้อมูลสำหรับการคำนวณรายได้-รายจ่าย", color="info", className="text-center")

    # 1. รายได้รวมทั้งหมด (Gross Income)
    total_gross_income = df["income"].sum()

    # 2. รายรับ (Net Income) - ในที่นี้ใช้ net_yearly_income
    total_net_income = df["net_yearly_income"].sum()

    # 3. รายจ่าย (Expenses/Debt) - ในที่นี้คือภาระหนี้รายปี
    total_expenses = df["yearly_debt_payments"].sum()
    
    # 4. คงเหลือ (Disposable Income) - รายรับหักรายจ่าย
    total_disposable = total_net_income - total_expenses

    # ฟังก์ชันช่วยจัดรูปแบบตัวเลข (M = Million, K = Thousand)
    def format_val(val):
        if val >= 1_000_000:
            return f"฿{val / 1_000_000:.2f}M"
        elif val >= 1_000:
            return f"฿{val / 1_000:.1f}K"
        return f"฿{val:,.0f}"

    return dbc.Row([
        # 1. รายได้รวมทั้งหมด
        dbc.Col(render_kpi_card(
            "รายได้รวมทั้งหมด",
            format_val(total_gross_income),
            "",
            "fa fa-credit-card",
            "primary"
        ), lg=3, md=6),
        
        # 2. รายรับ
        dbc.Col(render_kpi_card(
            "รายรับสุทธิ",
            format_val(total_net_income),
            "",
            "fa-solid fa-arrow-up",
            "info"
        ), lg=3, md=6),
        
        # 3. รายจ่าย
        dbc.Col(render_kpi_card(
            "รายจ่าย/ภาระหนี้",
            format_val(total_expenses),
            "",
            "fa fa-arrow-down",
            "red"
        ), lg=3, md=6),
        
        # 4. คงเหลือ
        dbc.Col(render_kpi_card(
            "คงเหลือสุทธิ",
            format_val(total_disposable),
            "",
            "fa-wallet",
            "success"
        ), lg=3, md=6),
    ], className="g-3 mb-4")
