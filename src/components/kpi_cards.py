from dash import html
import dash_bootstrap_components as dbc
import pandas as pd
from typing import Any

#  Color Palette
COLOR_MAP = {
    "primary": "#007bff",   
    "purple": "#6f42c1",    
    "success": "#28a745",   
    "orange": "#fd7e14",    
    "info": "#17a2b8",      
    "pink": "#ff69ed",
    "red": "#ff4d4d",
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
    """สร้าง Card KPI แบบมี Gradient และ Icon"""
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
                    html.H3(value, className="text-white fw-bold mb-0", style={"letterSpacing": "1px"}),
                    html.Small(unit, className="text-white-50") if unit else None,
                ], className="text-end"),
            ], className="d-flex justify-content-between align-items-center"),
        ], className="py-3"),
        className="shadow-lg rounded-3 border-0 h-100 hover-zoom",
        style={"background": f"linear-gradient(135deg, {card_color} 0%, {card_color}cc 100%)"}
    )

# ==================================================
# 2. KPI Overview (สำหรับหน้าแรก)
# ==================================================
def render_overview_kpis(df: pd.DataFrame) -> dbc.Row:
    if df.empty:
        return dbc.Alert("ไม่พบข้อมูล Overview", color="warning", className="text-center")

    total_members = len(df)
    total_branches = df["branch_no"].nunique() if "branch_no" in df.columns else 0
    prov_col = "province_name" if "province_name" in df.columns else "province"
    total_provinces = df[prov_col].nunique() if prov_col in df.columns else 0
    
    total_income = df["Income_Clean"].sum() if "Income_Clean" in df.columns else 0
    income_display = f"{total_income / 1_000_000:.2f}M" if total_income >= 1_000_000 else f"{total_income:,.0f}"

    return dbc.Row([
        dbc.Col(render_kpi_card("สมาชิกทั้งหมด", f"{total_members:,}", "คน", "fa-users", "primary"), lg=3, md=6),
        dbc.Col(render_kpi_card("สาขาที่ให้บริการ", f"{total_branches:,}", "สาขา", "fa-store", "purple"), lg=3, md=6),
        dbc.Col(render_kpi_card("จังหวัดที่ครอบคลุม", f"{total_provinces:,}", "จังหวัด", "fa-map-marked-alt", "success"), lg=3, md=6),
        dbc.Col(render_kpi_card("รายได้รวมสมาชิก", income_display, "บาท", "fa-hand-holding-usd", "orange"), lg=3, md=6),
    ], className="g-3 mb-4")

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
        dbc.Col(render_kpi_card("สมาชิกเพศชาย", f"{male_count:,}", "คน", "fa-mars", "success"), lg=3, md=6),
        dbc.Col(render_kpi_card("สมาชิกเพศหญิง", f"{female_count:,}", "คน", "fa-venus", "pink"), lg=3, md=6),
        dbc.Col(render_kpi_card("กลุ่ม Gen หลัก", popular_gen, "Majority", "fa-id-card", "purple"), lg=3, md=6),
    ], className="g-3 mb-4")

# ==================================================
# 4. KPI Branches
# ==================================================
def render_branch_kpis(df: pd.DataFrame) -> dbc.Row:
    if df.empty:
        return dbc.Alert("ไม่พบข้อมูลสาขา", color="warning", className="text-center")

    branch_col = "branch_name" if "branch_name" in df.columns else "branch_no"
    total_branches = df[branch_col].nunique() if branch_col in df.columns else 0

    top_branch = "N/A"
    top_count = 0
    if total_branches > 0:
        counts = df[branch_col].value_counts()
        top_branch = counts.idxmax()
        top_count = counts.max()

    avg_income = 0
    if "Income_Clean" in df.columns:
        valid_income = df[df["Income_Clean"] > 0]["Income_Clean"]
        avg_income = valid_income.mean() if not valid_income.empty else 0

    avg_approval_days = "0"
    if "registration_date" in df.columns and "approval_date" in df.columns:
        reg_dt = pd.to_datetime(df["registration_date"], errors='coerce')
        app_dt = pd.to_datetime(df["approval_date"], errors='coerce')
        days_diff = (app_dt - reg_dt).dt.days
        valid_diff = days_diff[days_diff >= 0]
        if not valid_diff.empty:
            avg_approval_days = f"{valid_diff.mean():.1f}"
    
    return dbc.Row([
        dbc.Col(render_kpi_card("สาขาทั้งหมด", f"{total_branches:,}", "แห่ง", "fa-store", "primary"), lg=3, md=6),
        dbc.Col(render_kpi_card("สาขายอดนิยม (Top)", f"{top_branch}", f"({top_count:,} คน)", "fa-trophy", "orange"), lg=3, md=6),
        dbc.Col(render_kpi_card("ระยะเวลาอนุมัติเฉลี่ย", avg_approval_days, "วัน (เฉลี่ย)", "fa-clock", "info"), lg=3, md=6),
        dbc.Col(render_kpi_card("รายได้เฉลี่ยสมาชิก", f"{avg_income:,.0f}", "บาท/เดือน", "fa-money-bill-wave", "success"), lg=3, md=6),
    ], className="g-3 mb-4")
    
# ==================================================
# 5. KPI Address (อัปเดตชื่อคอลัมน์ให้ตรงกับ SQL JOIN)
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
# 6. KPI Performance (คงเดิมแต่เพิ่ม Type Hint)
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