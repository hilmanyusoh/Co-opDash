from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from functools import lru_cache

from ..data_manager import load_data
from ..components.kpi_cards import render_amount_kpis
from ..components.chart_card import chart_card
from ..components.theme import THEME

# ==================================================
# Config
# ==================================================
CHART_HEIGHT = 340
UI_REVISION_KEY = "amount-static"

# ==================================================
# Data Preprocessing (คงเดิม)
# ==================================================
def preprocess_amount(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    df = df.copy()
    if "registration_date" in df.columns:
        df["reg_date"] = pd.to_datetime(df["registration_date"], errors="coerce")
    if {"credit_limit", "credit_limit_used_pct"}.issubset(df.columns):
        df["actual_debt"] = df["credit_limit"] * (df["credit_limit_used_pct"] / 100)
        df["available_credit"] = df["credit_limit"] * (1 - df["credit_limit_used_pct"] / 100)
    if "credit_limit_used_pct" in df.columns:
        df["risk_level"] = pd.cut(
            df["credit_limit_used_pct"],
            bins=[0, 50, 80, 100],
            labels=["ต่ำ (0-50%)", "ปานกลาง (50-80%)", "สูง (80-100%)"]
        )
    return df

@lru_cache(maxsize=1)
def load_amount_data():
    df = load_data()
    return preprocess_amount(df)

# ==================================================
# 3. Layout Helper (🔥 ปรับ Font & Margin ตามสั่ง)
# ==================================================
def apply_amount_layout(fig, height=CHART_HEIGHT, right_margin=30, compact=False):
    fig.update_layout(
        autosize=False,
        height=height,
        uirevision=UI_REVISION_KEY,
        margin=dict(
            t=40 if not compact else 20,
            b=35, # ปรับ bottom ให้เท่ากับหน้า branch
            l=45, # ปรับ left ให้เท่ากับหน้า branch
            r=right_margin, # ใช้ค่า margin ขวาที่ส่งเข้ามา
        ),
        paper_bgcolor=THEME["paper"],
        plot_bgcolor=THEME["bg_plot"],
        font=dict(
            family="Sarabun, sans-serif",
            color=THEME["text"],
            size=13, # ล็อกขนาดฟอนต์มาตรฐาน 13
        ),
        hoverlabel=dict(
            bgcolor="rgba(15,23,42,0.95)",
            font_color="white",
            bordercolor=THEME["grid"]
        ),
        transition_duration=0,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor=THEME["grid"])
    return fig

# ==================================================
# 4. Charts (คง Logic เดิม แต่ปรับ UI)
# ==================================================
def chart_mom_growth(df):
    if {"reg_date", "credit_limit"}.issubset(df.columns) is False: return go.Figure()
    df_clean = df.dropna(subset=["reg_date"]).copy()
    if df_clean.empty: return go.Figure()

    latest = df_clean["reg_date"].max()
    curr = df_clean[(df_clean["reg_date"].dt.month == latest.month) & (df_clean["reg_date"].dt.year == latest.year)]
    prev_date = latest - pd.DateOffset(months=1)
    prev = df_clean[(df_clean["reg_date"].dt.month == prev_date.month) & (df_clean["reg_date"].dt.year == prev_date.year)]

    values = [prev["credit_limit"].sum() if not prev.empty else 0, curr["credit_limit"].sum() if not curr.empty else 0]
    pct = ((values[1] - values[0]) / values[0] * 100) if values[0] > 0 else 0

    fig = go.Figure(go.Bar(
        x=["เดือนก่อนหน้า", "เดือนปัจจุบัน"],
        y=values,
        text=[f"฿{v:,.0f}" for v in values],
        textposition="outside",
        marker=dict(color=[THEME["primary"], THEME["info"]], line=dict(color="white", width=2)),
        hovertemplate="<b>%{x}</b><br>วงเงินรวม: ฿%{y:,.0f}<extra></extra>",
    ))

    fig.add_annotation(
        x=1, y=values[1], text=f"{'📈' if pct > 0 else '📉'} {pct:+.1f}%",
        showarrow=False, yshift=30,
        font=dict(size=14, color=THEME["success"] if pct > 0 else THEME["danger"])
    )

    fig.update_yaxes(title="วงเงินรวม (บาท)")
    return apply_amount_layout(fig, right_margin=40)

def chart_segment_risk_treemap(df):
    if not {"branch_no", "credit_limit", "credit_limit_used_pct"}.issubset(df.columns): return go.Figure()
    df_clean = df.dropna(subset=["branch_no", "credit_limit", "credit_limit_used_pct"]).copy()
    if df_clean.empty: return go.Figure()

    df_clean["is_high_risk"] = (df_clean["credit_limit_used_pct"] > 80).astype(int)
    summary = df_clean.groupby("branch_no", observed=False).agg(
        credit_limit=("credit_limit", "sum"),
        is_high_risk=("is_high_risk", "mean")
    ).reset_index()
    summary["Branch_Label"] = summary["branch_no"].apply(lambda x: f"สาขา {x}")

    fig = px.treemap(
        summary, path=["Branch_Label"], values="credit_limit",
        color="is_high_risk", color_continuous_scale="RdYlGn_r", range_color=[0, 0.5],
    )
    fig.update_traces(
        textfont=dict(size=14),
        hovertemplate="<b>%{label}</b><br>วงเงินรวม: ฿%{value:,.0f}<br>ความเสี่ยงสูง: %{color:.1%}<extra></extra>"
    )
    return apply_amount_layout(fig, compact=True, right_margin=15)

def chart_debt_distribution(df):
    if "actual_debt" not in df.columns: return go.Figure()
    df_clean = df[df["actual_debt"] > 0].copy()
    if df_clean.empty: return go.Figure()

    avg, med = df_clean["actual_debt"].mean(), df_clean["actual_debt"].median()

    fig = px.histogram(df_clean, x="actual_debt", nbins=25, color_discrete_sequence=[THEME["purple"]])
    fig.add_vline(x=avg, line_dash="dash", line_color=THEME["danger"], annotation_text=f"เฉลี่ย: ฿{avg:,.0f}")
    fig.add_vline(x=med, line_dash="dot", line_color=THEME["info"], annotation_text=f"กลาง: ฿{med:,.0f}")

    fig.update_traces(marker=dict(line=dict(color="white", width=1)))
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title="ยอดหนี้ปัจจุบัน (บาท)")
    fig.update_yaxes(title="จำนวนสมาชิก")

    # ขยาย Margin ขวาเป็น 60 เพราะมีป้ายกำกับ "ค่าเฉลี่ย" อยู่ขอบขวา
    return apply_amount_layout(fig, right_margin=60)

# ==================================================
# 5. Main Layout
# ==================================================
def amount_layout():
    df = load_amount_data()
    if df.empty: return dbc.Alert("ไม่พบข้อมูล", color="warning", className="mt-5")

    return dbc.Container(
        fluid=True,
        style={"padding": "20px 30px", "maxWidth": "1400px", "margin": "0 auto", "overflowX": "hidden"},
        children=[
            html.H3("ข้อมูลภาพรวมเงินกู้", className="fw-bold mb-3"),
            render_amount_kpis(df),
            dbc.Row([
                dbc.Col(chart_card(chart_debt_distribution(df), "การกระจายตัวยอดหนี้ปัจจุบัน"), lg=12)
            ], className="g-3 mb-3"),
            dbc.Row([
                dbc.Col(chart_card(chart_mom_growth(df), "แนวโน้มการเติบโตยอดปล่อยกู้ (MoM)"), lg=6),
                dbc.Col(chart_card(chart_segment_risk_treemap(df), "ความเสี่ยงแยกตามสาขา"), lg=6),
            ], className="g-3"),
        ],
    )

layout = amount_layout()