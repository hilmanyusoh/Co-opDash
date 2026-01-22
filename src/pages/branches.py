from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from functools import lru_cache

from ..data_manager import load_data
from ..components.kpi_cards import render_branch_kpis
from ..components.chart_card import chart_card
from ..components.theme import THEME

CHART_HEIGHT = 340

# ==================================================
# Branch Colors (Standardized Mapping)
# ==================================================
BRANCH_COLORS = {
    "สาขา 1": THEME["purple"],
    "สาขา 2": THEME["primary"],
    "สาขา 3": THEME["success"],
    "สาขา 4": THEME["warning"],
    "สาขา 5": THEME["danger"],
}

# ==================================================
# 1. Data Processing (ยังคง Logic เดิม)
# ==================================================
def process_branch(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    if "registration_date" in df.columns:
        df["registration_date"] = pd.to_datetime(df["registration_date"], errors="coerce")
    if "approval_date" in df.columns:
        df["approval_date"] = pd.to_datetime(df["approval_date"], errors="coerce")

    if {"registration_date", "approval_date"}.issubset(df.columns):
        df["Days_to_Approve"] = (df["approval_date"] - df["registration_date"]).dt.days.clip(lower=0)
    else:
        df["Days_to_Approve"] = 0

    if "income" in df.columns:
        df["Income_Clean"] = df["income"].astype(str).str.replace(",", "").pipe(pd.to_numeric, errors="coerce").fillna(0)
    else:
        df["Income_Clean"] = 0

    branch_map = {1: "สาขา 1", 2: "สาขา 2", 3: "สาขา 3", 4: "สาขา 4", 5: "สาขา 5"}
    if "branch_no" in df.columns:
        df["branch_name"] = df["branch_no"].map(branch_map).fillna(
            df["branch_no"].astype(str).apply(lambda x: f"สาขา {x}")
        )
    else:
        df["branch_name"] = "ไม่ระบุ"

    return df

@lru_cache(maxsize=1)
def load_branch_data():
    df = load_data()
    return process_branch(df)

# ==================================================
# 3. Layout Helper (Standardized Font & Margins)
# ==================================================
def apply_branch_layout(fig, height=CHART_HEIGHT, right_margin=30):
    fig.update_layout(
        height=height,
        margin=dict(t=40, b=35, l=45, r=right_margin), # ปรับ Margin ตามที่กำหนด
        paper_bgcolor=THEME["paper"],
        plot_bgcolor=THEME["bg_plot"],
        font=dict(
            family="Sarabun, sans-serif",
            color=THEME["text"],
            size=13  # กำหนดขนาดฟอนต์มาตรฐาน
        ),
        hovermode="closest",
        transition_duration=0,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor=THEME["grid"])
    return fig

# ==================================================
# 4. Charts
# ==================================================
def chart_member_column(df):
    if df.empty: return go.Figure()
    counts = df.groupby("branch_name").size().reset_index(name="count").sort_values("branch_name")
    
    fig = px.bar(
        counts, x="branch_name", y="count", text="count",
        color="branch_name", color_discrete_map=BRANCH_COLORS # ใช้ระบบสีคงที่
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    return apply_branch_layout(fig)

def chart_income_line(df):
    if df.empty: return go.Figure()
    avg_income = df.groupby("branch_name")["Income_Clean"].mean().reset_index().sort_values("branch_name")
    
    fig = go.Figure(go.Scatter(
        x=avg_income["branch_name"], y=avg_income["Income_Clean"],
        mode="lines+markers+text",
        line=dict(color=THEME["primary"], width=3),
        marker=dict(size=10, line=dict(width=2, color="white")),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.12)",
        text=[f"฿{v:,.0f}" for v in avg_income["Income_Clean"]],
        textposition="top center"
    ))
    return apply_branch_layout(fig)

def chart_approval_mode(df):
    if df.empty: return go.Figure()
    modes = df.groupby("branch_name")["Days_to_Approve"].apply(
        lambda x: x.mode().iloc[0] if not x.mode().empty else 0
    ).reset_index().sort_values("Days_to_Approve")
    
    fig = px.bar(
        modes, y="branch_name", x="Days_to_Approve", orientation="h",
        text="Days_to_Approve", color="branch_name", color_discrete_map=BRANCH_COLORS
    )
    fig.update_traces(texttemplate="%{text} วัน", textposition="outside")
    return apply_branch_layout(fig)

def chart_member_income_dual(df):
    if df.empty: return go.Figure()
    
    summary = df.groupby("branch_name").agg(
        member_count=("branch_name", "count"),
        total_income=("Income_Clean", "sum")
    ).reset_index().sort_values("branch_name")

    fig = go.Figure()

    # 1. แท่งกราฟ: ลบออกจาก Legend โดยใช้ showlegend=False
    fig.add_bar(
        x=summary["branch_name"],
        y=summary["member_count"],
        text=summary["member_count"],
        textposition="outside",
        # บังคับสีแท่งให้ตรงตามสาขา
        marker_color=[BRANCH_COLORS.get(b, THEME["muted"]) for b in summary["branch_name"]],
        name="จำนวนสมาชิก",
        showlegend=False, # <--- ลบข้อความ "จำนวนสมาชิก" ออกจาก Legend
        hovertemplate="<b>%{x}</b><br>สมาชิก: %{y:,} คน<extra></extra>"
    )

    # 2. เส้นกราฟ: ปรับสีเส้น (Line Color) และความหนา
    fig.add_scatter(
        x=summary["branch_name"],
        y=summary["total_income"],
        yaxis="y2",
        mode="lines+markers",
        # เปลี่ยนสีเส้นตรงนี้ (ตัวอย่างใช้สีน้ำเงินเข้ม Slate Blue)
        line=dict(color="#475569", width=3, dash="dot"), 
        marker=dict(size=10, symbol="diamond", line=dict(width=2, color="white")),
        name="รายได้รวม",
        hovertemplate="<b>%{x}</b><br>รายได้รวม: ฿%{y:,.0f}<extra></extra>"
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.3, # <--- ขยับ Legend ลงด้านล่างมากขึ้นเพื่อไม่ให้ทับชื่อสาขา
            xanchor="center",
            x=0.5,
            font=dict(size=12)
        ),
        yaxis=dict(title="จำนวนสมาชิก (คน)"),
        yaxis2=dict(
            title="รายได้รวม (บาท)",
            overlaying="y",
            side="right",
            showgrid=False,
            tickformat=",.0f"
        )
    )
    # ใช้ right_margin=70 เพื่อป้องกันตัวเลขหลักล้านเบียดขอบ
    return apply_branch_layout(fig, right_margin=70)

# ==================================================
# 5. Main Layout
# ==================================================
def branch_layout():
    df = load_branch_data()
    if df.empty:
        return dbc.Container(dbc.Alert("ไม่พบข้อมูล", color="warning", className="mt-5"))

    return dbc.Container(
        fluid=True,
        style={"padding": "20px 30px", "maxWidth": "1400px", "margin": "0 auto"},
        children=[
            html.H3("ข้อมูลสาขา", className="fw-bold mb-3"),
            render_branch_kpis(df),
            dbc.Row([
                dbc.Col(chart_card(chart_member_column(df), "จำนวนสมาชิกแต่ละสาขา"), lg=6),
                dbc.Col(chart_card(chart_income_line(df), "รายได้เฉลี่ยต่อคน"), lg=6),
            ], className="g-3 mb-3"),
            dbc.Row([
                dbc.Col(chart_card(chart_approval_mode(df), "ระยะเวลาอนุมัติที่พบบ่อย"), lg=6),
                dbc.Col(chart_card(chart_member_income_dual(df), "จำนวนสมาชิก vs รายได้รวม"), lg=6),
            ], className="g-3"),
        ],
    )

layout = branch_layout()