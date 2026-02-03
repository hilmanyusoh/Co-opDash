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
# 6. KPI Amount 
# ==================================================
def render_amount_kpis(df: pd.DataFrame) -> dbc.Row:
    if df.empty:
        return dbc.Alert("ยังไม่มีข้อมูลทางการเงิน", color="warning")

    # 1. ยอดรวมที่ลูกหนี้ค้างเราทั้งหมด
    total_debt = (df['credit_limit'] * df['credit_limit_used_pct'] / 100).sum()

    # 2. ลูกค้ากลุ่มเสี่ยง (ใช้เงินเกือบเต็มวงเงิน)
    risky_count = len(df[df['credit_limit_used_pct'] > 95])
    # เปลี่ยนจาก % เป็น "จำนวนคน" จะทำให้เจ้าของรู้สึกต้องรีบจัดการมากกว่า
    
    # 3. ยอดที่เพิ่งจ่ายออก (โอนกู้ใหม่) เดือนนี้
    new_disbursement = 0
    if 'registration_date' in df.columns:
        df['registration_date'] = pd.to_datetime(df['registration_date'])
        latest = df['registration_date'].max()
        new_disbursement = df[
            (df['registration_date'].dt.month == latest.month) & 
            (df['registration_date'].dt.year == latest.year)
        ]['credit_limit'].sum()

    # 4. เป้าหมายที่ต้องตามเก็บให้ได้เดือนนี้
    collection_target = df['yearly_debt_payments'].sum() / 12

    def format_baht(val):
        if val >= 1_000_000: return f"{val/1_000_000:.2f} ล้าน"
        return f"{val:,.0f}"

    return dbc.Row([
        dbc.Col(render_kpi_card(
            "เงินค้างในมือลูกค้า", 
            format_baht(total_debt), 
            "ยอดลูกหนี้รวมทั้งหมด", 
            "fa-sack-dollar", "primary"
        ), lg=3, md=6),
        
        dbc.Col(render_kpi_card(
            "ลูกค้ากลุ่มเสี่ยง", 
            f"{risky_count} ราย", 
            "ต้องติดตามเป็นพิเศษ", 
            "fa-triangle-exclamation", "danger"
        ), lg=3, md=6),
        
        dbc.Col(render_kpi_card(
            "ยอดปล่อยกู้เดือนนี้", 
            format_baht(new_disbursement), 
            "เงินโอนออกให้ลูกค้าใหม่", 
            "fa-money-bill-transfer", "info"
        ), lg=3, md=6),
        
        dbc.Col(render_kpi_card(
            "เป้าเก็บเงินเดือนนี้", 
            format_baht(collection_target), 
            "ยอดชำระที่ต้องตามเก็บ", 
            "fa-calendar-check", "success"
        ), lg=3, md=6),
    ], className="g-3 mb-4")

# ==================================================
# 6. KPI : สรุปภาพรวมความเติบโตขององค์กร 
# ==================================================
def render_performance_kpis(df: pd.DataFrame) -> dbc.Row:
    # 1. ตรวจสอบความว่างเปล่าของข้อมูล
    if df.empty:
        return dbc.Alert("ไม่พบข้อมูลสำหรับการวิเคราะห์", color="warning")

    # 2. เตรียมข้อมูลวันที่
    temp_df = df.copy()
    # ตรวจสอบคอลัมน์และแปลงเป็น Datetime
    reg_col = 'registration_date' if 'registration_date' in temp_df.columns else 'reg_date'
    temp_df['reg_date_clean'] = pd.to_datetime(temp_df[reg_col], errors='coerce')
    temp_df = temp_df.dropna(subset=['reg_date_clean']).sort_values('reg_date_clean')

    # ทำความสะอาดข้อมูลรายได้ (Income)
    if "income" in temp_df.columns:
        temp_df["Income_Clean"] = (
            temp_df["income"].astype(str).str.replace(",", "")
            .pipe(pd.to_numeric, errors="coerce").fillna(0)
        )

    # --------------------------------------------------
    # 3. ตรรกะการคำนวณ (Logic Calculation)
    # --------------------------------------------------
    
    # ก. ยอดสมาชิกใหม่เฉลี่ย (คำนวณจาก 6 เดือนล่าสุดที่มีข้อมูล)
    monthly_new = temp_df.set_index('reg_date_clean').resample('ME').size()
    avg_monthly_new = monthly_new.tail(6).mean() if not monthly_new.empty else 0

    # ข. เป้าหมายสมาชิกในอีก 12 เดือนข้างหน้า
    current_total = len(temp_df)
    target_next_year = current_total + (avg_monthly_new * 12)

    # ค. ความเร็วการเติบโต (FIX: เปลี่ยนจาก 2026 เป็นปี 2025 ตามที่คุณต้องการ)
    analysis_year = 2025 
    count_this_year = len(temp_df[temp_df['reg_date_clean'].dt.year == analysis_year])
    count_last_year = len(temp_df[temp_df['reg_date_clean'].dt.year == analysis_year - 1])

    growth_pct = 0
    if count_last_year > 0:
        # สูตร: ((ใหม่ - เก่า) / เก่า) * 100
        growth_pct = ((count_this_year - count_last_year) / count_last_year) * 100
    elif count_this_year > 0:
        growth_pct = 100.0 # กรณีปีที่แล้วไม่มีแต่ปีนี้มีสมาชิก

    # ง. มูลค่าธุรกิจรวมที่คาดหวัง (อ้างอิงจากรายได้เฉลี่ยต่อหัว)
    avg_income = temp_df["Income_Clean"].mean() if "Income_Clean" in temp_df.columns else 0
    total_value_forecast = target_next_year * avg_income

    # --------------------------------------------------
    # 4. การแสดงผล (UI Rendering)
    # --------------------------------------------------
    return dbc.Row(
        [
            # KPI 1: เป้าหมายสมาชิก
            dbc.Col(
                render_kpi_card(
                    "เป้าหมายสมาชิกปีหน้า",
                    f"{int(target_next_year):,}",
                    "คน (คาดการณ์ 12 เดือน)",
                    "fa-bullseye",
                    "primary",
                ),
                lg=3, md=6,
            ),
            # KPI 2: อัตราการเติบโต (จุดที่แก้ไข -100%)
            dbc.Col(
                render_kpi_card(
                    f"ความเร็วการโตปี {analysis_year}",
                    f"{growth_pct:+.1f}%",
                    f"เทียบกับปี {analysis_year - 1}",
                    "fa-rocket",
                    "success" if growth_pct >= 0 else "danger",
                ),
                lg=3, md=6,
            ),
            # KPI 3: มูลค่าธุรกิจคาดหวัง
            dbc.Col(
                render_kpi_card(
                    "มูลค่าธุรกิจที่คาดหวัง",
                    f"{total_value_forecast / 1_000_000:.1f} ล้าน",
                    "บาท (เมื่อถึงเป้าหมาย)",
                    "fa-sack-dollar",
                    "purple",
                ),
                lg=3, md=6,
            ),
            # KPI 4: สมาชิกใหม่ต่อเดือน
            dbc.Col(
                render_kpi_card(
                    "สมาชิกใหม่เฉลี่ย",
                    f"{int(avg_monthly_new)}",
                    "คน / เดือน (สถิติ 6 เดือน)",
                    "fa-user-plus",
                    "info",
                ),
                lg=3, md=6,
            ),
        ],
        className="g-3 mb-4",
    )