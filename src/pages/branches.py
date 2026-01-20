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
# สีสาขา
# ==================================================
BRANCH_COLORS = {
    "สาขา 1": THEME["purple"],
    "สาขา 2": THEME["primary"],
    "สาขา 3": THEME["success"],
    "สาขา 4": THEME["warning"],
    "สาขา 5": THEME["danger"],
}

# ==================================================
# 1. Data Processing
# ==================================================
def process_branch(df):
    if df.empty:
        return df

    df["registration_date"] = pd.to_datetime(df["registration_date"], errors="coerce")
    df["approval_date"] = pd.to_datetime(df["approval_date"], errors="coerce")
    df["Days_to_Approve"] = (df["approval_date"] - df["registration_date"]).dt.days
    df.loc[df["Days_to_Approve"] < 0, "Days_to_Approve"] = 0

    if "income" in df.columns:
        df["Income_Clean"] = (
            df["income"]
            .astype(str)
            .str.replace(",", "")
            .pipe(pd.to_numeric, errors="coerce")
            .fillna(0)
        )

    branch_map = {1: "สาขา 1", 2: "สาขา 2", 3: "สาขา 3", 4: "สาขา 4", 5: "สาขา 5"}
    if "branch_no" in df.columns:
        df["branch_name"] = df["branch_no"].map(branch_map).fillna(
            df["branch_no"].astype(str).apply(lambda x: f"สาขา {x}")
        )

    return df


# ==================================================
# 2. Cache Data
# ==================================================
@lru_cache(maxsize=1)
def load_branch_data():
    return process_branch(load_data())


# ==================================================
# 3. Layout Helper (มาตรฐานเดียวกับหน้าอื่น)
# ==================================================
def apply_layout(fig, height=CHART_HEIGHT, right_margin=30):
    fig.update_layout(
        height=height,
        margin=dict(t=40, b=35, l=45, r=right_margin),
        paper_bgcolor=THEME["paper"],
        plot_bgcolor=THEME["bg_plot"],
        font=dict(
            family="Sarabun, sans-serif",
            color=THEME["text"],
            size=13,
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
    counts = (
        df["branch_name"]
        .value_counts()
        .sort_index()
        .reset_index(name="count")
        .rename(columns={"index": "branch_name"})
    )

    fig = px.bar(
        counts,
        x="branch_name",
        y="count",
        text="count",
        color="branch_name",
        color_discrete_map=BRANCH_COLORS,
    )

    fig.update_traces(
        texttemplate="%{text:,}",
        textposition="outside",
        marker=dict(line=dict(width=2, color="white")),
        hovertemplate="<b>%{x}</b><br>จำนวนสมาชิก: %{y:,} คน<extra></extra>",
    )

    fig.update_yaxes(title="จำนวนสมาชิก (คน)")
    fig.update_xaxes(title="สาขา")

    return apply_layout(fig)


def chart_income_line(df):
    avg_income = (
        df.groupby("branch_name")["Income_Clean"]
        .mean()
        .sort_index()
        .reset_index()
    )

    fig = go.Figure(
        go.Scatter(
            x=avg_income["branch_name"],
            y=avg_income["Income_Clean"],
            mode="lines+markers+text",
            line=dict(color=THEME["primary"], width=3),
            marker=dict(size=10, line=dict(width=2, color="white")),
            fill="tozeroy",
            fillcolor="rgba(59,130,246,0.12)",
            text=[f"฿{v:,.0f}" for v in avg_income["Income_Clean"]],
            textposition="top center",
            hovertemplate="<b>%{x}</b><br>รายได้เฉลี่ย: ฿%{y:,.0f}<extra></extra>",
        )
    )

    fig.update_yaxes(title="รายได้เฉลี่ย (บาท)", tickformat=",.0f")
    return apply_layout(fig)


def chart_approval_mode(df):
    modes = (
        df.groupby("branch_name")["Days_to_Approve"]
        .apply(lambda x: x.mode().iloc[0] if not x.mode().empty else 0)
        .sort_values()
        .reset_index()
    )

    fig = px.bar(
        modes,
        y="branch_name",
        x="Days_to_Approve",
        orientation="h",
        text="Days_to_Approve",
        color="branch_name",
        color_discrete_map=BRANCH_COLORS,
    )

    fig.update_traces(
        texttemplate="%{text} วัน",
        textposition="outside",
        marker=dict(line=dict(width=2, color="white")),
        hovertemplate="<b>%{y}</b><br>ระยะเวลาอนุมัติ: %{x} วัน<extra></extra>",
    )

    fig.update_xaxes(title="จำนวนวัน")
    return apply_layout(fig)


def chart_member_income_dual(df):
    summary = df.groupby("branch_name").agg(
        member_count=("member_id", "count"),
        total_income=("Income_Clean", "sum"),
    ).reset_index()

    fig = go.Figure()

    fig.add_bar(
        x=summary["branch_name"],
        y=summary["member_count"],
        text=summary["member_count"],
        textposition="outside",
        marker_color=[BRANCH_COLORS.get(b, THEME["muted"]) for b in summary["branch_name"]],
        name="จำนวนสมาชิก",
        hovertemplate="<b>%{x}</b><br>สมาชิก: %{y:,} คน<extra></extra>",
    )

    fig.add_scatter(
        x=summary["branch_name"],
        y=summary["total_income"],
        yaxis="y2",
        mode="lines+markers",
        line=dict(color=THEME["warning"], width=3, dash="dot"),
        marker=dict(size=11, line=dict(width=2, color="white")),
        name="รายได้รวม",
        hovertemplate="<b>%{x}</b><br>รายได้รวม: ฿%{y:,.0f}<extra></extra>",
    )

    fig.update_layout(
        yaxis=dict(title="จำนวนสมาชิก (คน)"),
        yaxis2=dict(
            title="รายได้รวม (บาท)",
            overlaying="y",
            side="right",
            tickformat=",",
            showgrid=False,
        ),
        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=-0.18,
        ),
    )

    # 🔥 margin ขวาเพิ่ม เพื่อไม่ให้ y2 ชน
    return apply_layout(fig, right_margin=60)


# ==================================================
# 5. Main Layout
# ==================================================
def create_branch_layout():
    df = load_branch_data()

    if df.empty:
        return dbc.Alert("ไม่พบข้อมูล", color="warning", className="mt-5")

    return dbc.Container(
        fluid=True,
        style={"padding": "20px 30px", "maxWidth": "1400px", "margin": "0 auto"},
        children=[
            html.H3("ข้อมูลสาขา", className="fw-bold mb-3"),
            render_branch_kpis(df),

            dbc.Row(
                [
                    dbc.Col(chart_card(chart_member_column(df), "จำนวนสมาชิกแต่ละสาขา"), lg=6),
                    dbc.Col(chart_card(chart_income_line(df), "รายได้เฉลี่ยต่อคน"), lg=6),
                ],
                className="g-3 mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(chart_card(chart_approval_mode(df), "ระยะเวลาอนุมัติที่พบบ่อย"), lg=6),
                    dbc.Col(chart_card(chart_member_income_dual(df), "จำนวนสมาชิก vs รายได้รวม"), lg=6),
                ],
                className="g-3",
            ),
        ],
    )


layout = create_branch_layout()
