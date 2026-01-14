from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from ..data_manager import load_data
from ..components.kpi_cards import render_member_kpis

CHART_HEIGHT = 340

# ==================================================
# Data Processing
# ==================================================
def process_member(df):
    if df.empty:
        return df

    if "gender_name" in df.columns:
        df["Gender"] = (
            df["gender_name"]
            .map({"นาย": "ชาย", "นาง": "หญิง", "นางสาว": "หญิง"})
            .fillna("อื่นๆ")
        )

    if "birthday" in df.columns:
        df["birthday"] = pd.to_datetime(df["birthday"], errors="coerce")

        def gen_map(x):
            if pd.isnull(x):
                return "Unknown"
            elif x.year <= 1964:
                return "Baby Boomer"
            elif x.year <= 1980:
                return "Gen X"
            elif x.year <= 1996:
                return "Gen Y"
            else:
                return "Gen Z"

        df["Gen"] = df["birthday"].apply(gen_map)

    if "income" in df.columns:
        df["Income_Clean"] = (
            df["income"]
            .astype(str)
            .str.replace(",", "")
            .pipe(pd.to_numeric, errors="coerce")
            .fillna(0)
        )

        bins = [0, 15000, 30000, 50000, 100000, float("inf")]
        labels = ["< 15K", "15K - 30K", "30K - 50K", "50K - 100K", "100K+"]
        df["Income_Level"] = pd.cut(
            df["Income_Clean"], bins=bins, labels=labels, right=False
        )

    if "registration_date" in df.columns:
        df["reg_date"] = pd.to_datetime(df["registration_date"], errors="coerce")

    return df

# ==================================================
# Chart Layout 
# ==================================================
def apply_layout(fig, height=CHART_HEIGHT):
    fig.update_layout(
        height=height,
        margin=dict(t=0, b=40, l=50, r=30),
        plot_bgcolor="rgba(248, 250, 252, 0.3)",
        paper_bgcolor="rgba(255, 255, 255, 0)",
        font=dict(
            family="Sarabun, sans-serif",
            color="#334155"
        ),
    )
    return fig

# ==================================================
# Charts
# ==================================================
def chart_growth_time(df):
    if "reg_date" not in df.columns: return go.Figure()

    # 1. เตรียมข้อมูลสมาชิกสะสม
    trend = (df.dropna(subset=["reg_date"])
             .groupby(df["reg_date"].dt.to_period("M"), observed=False)
             .size().reset_index(name="count"))
    
    if trend.empty: return go.Figure()
    trend["reg_date"] = trend["reg_date"].dt.to_timestamp()
    trend["cumulative"] = trend["count"].cumsum()

    # 2. สร้างกราฟ
    fig = go.Figure(go.Scatter(
        x=trend["reg_date"], y=trend["cumulative"],
        mode="lines",
        name="จำนวนสมาชิกสะสม", # ชื่อที่จะปรากฏใน Legend
        line=dict(color="#3b82f6", width=4, shape="spline"),
        fill="tozeroy",
        fillcolor="rgba(59, 130, 246, 0.1)",
        hovertemplate="<b>%{x|%B %Y}</b><br>สมาชิกสะสม: <span style='color:#3b82f6'>%{y:,.0f} คน</span><extra></extra>"
    ))

    # 3. ปรับ Layout ให้ Modern และเพิ่ม Legend
    fig.update_layout(
        margin=dict(t=40, b=20, l=10, r=10), # เพิ่ม margin-top เพื่อหลบ Legend
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        
        # การตั้งค่า Legend ให้ดูดี
        showlegend=True,
        legend=dict(
            orientation="h",       # แนวนอน
            yanchor="bottom",
            y=1.02,               # วางไว้เหนือกราฟเล็กน้อย
            xanchor="left",
            x=0,
            font=dict(size=12, color="#64748b")
        ),
        
        xaxis=dict(showgrid=False, tickfont=dict(color="#94a3b8"), tickformat="%b %y"),
        yaxis=dict(gridcolor="#f1f5f9", zeroline=False, tickfont=dict(color="#94a3b8"), side="right"),
        hoverlabel=dict(bgcolor="white", font_family="Sarabun", bordercolor="#e2e8f0")
    )

    return apply_layout(fig)

def chart_gender_career(df):
    if "Gender" not in df.columns:
        return go.Figure()

    career_col = "career_name" if "career_name" in df.columns else "career"
    if career_col not in df.columns:
        return go.Figure()

    top = df[career_col].value_counts().head(5).index
    data = df[df[career_col].isin(top)]

    fig = px.histogram(
        data,
        y=career_col,
        color="Gender",
        orientation="h",
        barmode="group",
    )

    fig.update_layout(legend=dict(orientation="h", y=-0.25))
    return apply_layout(fig)

def chart_income_pie(df):
    if "Income_Level" not in df.columns:
        return go.Figure()

    counts = df["Income_Level"].value_counts().sort_index()

    fig = go.Figure(
        go.Pie(
            labels=counts.index,
            values=counts.values,
            hole=0.45
        )
    )

    fig.update_layout(legend=dict(orientation="h", y=-0.15))
    return apply_layout(fig)

def chart_gen_area(df):
    if "Gen" not in df.columns:
        return go.Figure()

    prov_col = "province_name" if "province_name" in df.columns else "province"
    if prov_col not in df.columns:
        return go.Figure()

    data = (
        df.groupby([prov_col, "Gen"])
        .size()
        .reset_index(name="count")
    )

    fig = px.bar(
        data,
        x=prov_col,
        y="count",
        color="Gen",
        barmode="stack",
        # กำหนดลำดับสีให้ดูทันสมัยตามรูปภาพ
        color_discrete_map={"Gen X": "#636efa", "Gen Y": "#ef553b", "Gen Z": "#00cc96"}
    )

    fig.update_layout(
        # ปรับ margin ด้านล่าง (b) เพิ่มขึ้นเพื่อให้มีพื้นที่สำหรับชื่อจังหวัดที่ยาว
        margin=dict(b=100), 
        legend=dict(
            orientation="h", 
            yanchor="top",
            y=-0.5, # ขยับ legend ลงไปด้านล่างมากขึ้นเพื่อไม่ให้ทับชื่อแกน X
            xanchor="center",
            x=0.5
        ),
        xaxis=dict(title=None), # ลบชื่อแกน "province_name" ออกเพื่อให้ดูสะอาดตาขึ้น
        yaxis=dict(title="จำนวน (คน)")
    )
    
    return apply_layout(fig)

def chart_monthly_members(df):
    """กราฟแท่ง: จำนวนสมาชิกใหม่รายเดือน (เฉพาะปี 2025)"""

    if "reg_date" not in df.columns:
        return go.Figure()

    # 🔹 กรองเฉพาะปี 2025
    df_2025 = df[
        (df["reg_date"].notna()) &
        (df["reg_date"].dt.year == 2025)
    ]

    # 🔹 รวมจำนวนสมาชิกต่อเดือน (ม.ค. – ธ.ค.)
    monthly = (
        df_2025
        .groupby(df_2025["reg_date"].dt.month)
        .size()
        .reindex(range(1, 13), fill_value=0)  # ให้ครบ 12 เดือน
        .reset_index(name="total_members")
    )

    month_labels = [
        "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
        "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
    ]

    fig = go.Figure()

    # Layer หลัง (background)
    fig.add_bar(
        x=month_labels,
        y=monthly["total_members"] * 1.15,
        marker_color="rgba(59,130,246,0.15)",
        hoverinfo="skip"
    )

    # Layer หน้า (ข้อมูลจริง)
    fig.add_bar(
        x=month_labels,
        y=monthly["total_members"],
        marker_color="#3b82f6",
        text=monthly["total_members"],
        textposition="outside",
        hovertemplate=(
            "<b>%{x} 2025</b><br>"
            "สมาชิกใหม่ทั้งหมด: %{y} คน"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        title="<b>จำนวนสมาชิกใหม่รายเดือน ปี 2025</b>",
        barmode="overlay",
        bargap=0.5,
        showlegend=False,
        xaxis=dict(
            title="เดือน",
            showgrid=False
        ),
        yaxis=dict(
            title="จำนวนสมาชิก (คน)",
            showgrid=False,
            rangemode="tozero"
        ),
    )

    return apply_layout(fig)


# ==================================================
# Card Component 
# ==================================================
def chart_card(fig, title):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H6(
                    title,
                    className="fw-bold mb-2 chart-title",
                ),
                dcc.Graph(
                    figure=fig,
                    config={"displayModeBar": False},
                ),
            ],
            style={"padding": "12px"},
        ),
        className="shadow-sm rounded-3 border-0 mb-3",
    )

# ==================================================
# Layout
# ==================================================
def member_layout():
    df = process_member(load_data())

    return dbc.Container(
        fluid=True,
        style={"padding": "20px 30px", "maxWidth": "1400px"},
        children=[

            # ================= Header =================
            html.H3("ข้อมูลสมาชิก", className="page-title fw-bold mb-3"),
            render_member_kpis(df),

            # ================= Row 1 : Large chart =================
            dbc.Row([
                dbc.Col(
                    chart_card(
                        chart_growth_time(df),
                        "แนวโน้มการเพิ่มขึ้นของสมาชิกรายเดือน"
                    ),
                    lg=12
                ),
            ]),

            # ================= Row 2 : 2 charts =================
            dbc.Row([
                dbc.Col(
                    chart_card(
                        chart_monthly_members(df),
                        "จำนวนสมาชิกใหม่รายเดือน"
                    ),
                    lg=6
                ),
                dbc.Col(
                    chart_card(
                        chart_gender_career(df),
                        "สัดส่วนเพศแยกตามกลุ่มอาชีพ"
                    ),
                    lg=6
                ),
            ]),

            # ================= Row 3 : 2 charts =================
            dbc.Row([
                dbc.Col(
                    chart_card(
                        chart_income_pie(df),
                        "สัดส่วนสมาชิกแยกตามระดับรายได้"
                    ),
                    lg=6
                ),
                dbc.Col(
                    chart_card(
                        chart_gen_area(df),
                        "การกระจาย Generation ตามจังหวัด"
                    ),
                    lg=6
                ),
            ]),

        ],
    )
layout = member_layout()
