from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from ..data_manager import load_data
from ..components.kpi_cards import render_branch_kpis

CHART_HEIGHT = 340

# ==================================================
# 1. Data Processing
# ==================================================
def get_processed_data():
    df = load_data()
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

    branch_map = {
        1: "สาขา 1",
        2: "สาขา 2",
        3: "สาขา 3",
        4: "สาขา 4",
        5: "สาขา 5",
    }

    if "branch_no" in df.columns:
        df["branch_name"] = df["branch_no"].map(branch_map).fillna(
            df["branch_no"].astype(str).apply(lambda x: f"สาขา {x}")
        )

    return df

# ==================================================
# 2. Layout Helper (❌ ไม่กำหนด fontSize)
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
# 3. Charts
# ==================================================
def chart_member_column(df):
    counts = (
        df["branch_name"]
        .value_counts()
        .sort_index()
        .reset_index()
    )
    counts.columns = ["branch_name", "count"]

    fig = px.bar(
        counts,
        x="branch_name",
        y="count",
    )

    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>จำนวน: %{y} คน<extra></extra>",
        showlegend=False
    )

    fig.update_yaxes(title="จำนวนสมาชิก")
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
            mode="lines+markers",
            fill="tozeroy",
            hovertemplate="<b>%{x}</b><br>รายได้เฉลี่ย: ฿%{y:,.0f}<extra></extra>"
        )
    )

    fig.update_yaxes(title="รายได้เฉลี่ย (บาท)", tickformat=",.0f")
    return apply_layout(fig)

def chart_approval_mode(df):
    branch_modes = (
        df.groupby("branch_name")["Days_to_Approve"]
        .apply(lambda x: x.mode().iloc[0] if not x.mode().empty else 0)
        .sort_values()
        .reset_index()
    )

    fig = px.bar(
        branch_modes,
        y="branch_name",
        x="Days_to_Approve",
        orientation="h",
    )

    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>ระยะเวลาอนุมัติ: %{x} วัน<extra></extra>",
        showlegend=False
    )

    fig.update_xaxes(title="จำนวนวัน")
    return apply_layout(fig)

def chart_member_income_dual(df):
    summary = df.groupby("branch_name").agg(
        member_count=("member_id", "count"),
        total_income=("Income_Clean", "sum")
    ).reset_index()

    fig = go.Figure()

    fig.add_bar(
        x=summary["branch_name"],
        y=summary["member_count"],
        name="จำนวนสมาชิก",
    )

    fig.add_scatter(
        x=summary["branch_name"],
        y=summary["total_income"],
        name="รายได้รวม",
        yaxis="y2",
        mode="lines+markers",
        hovertemplate="รายได้รวม: ฿%{y:,.0f}<extra></extra>"
    )

    fig.update_layout(
        yaxis=dict(title="จำนวนสมาชิก"),
        yaxis2=dict(
            title="รายได้รวม (บาท)",
            overlaying="y",
            side="right",
            tickformat=","
        ),
        legend=dict(orientation="h", y=-0.25),
    )

    return apply_layout(fig)

# ==================================================
# 4. Main Layout
# ==================================================
def create_branch_layout():
    df = get_processed_data()

    if df.empty:
        return dbc.Container(
            dbc.Alert("ไม่พบข้อมูล", color="warning", className="mt-5")
        )

    def card(fig, title):
        return dbc.Card(
            dbc.CardBody(
                [
                    html.H6(title, className="fw-bold mb-2 chart-title"),
                    dcc.Graph(
                        figure=fig,
                        config={"displayModeBar": False}
                    ),
                ],
                style={"padding": "12px"},
            ),
            className="shadow-sm rounded-3 border-0 mb-3",
        )

    return dbc.Container(
        fluid=True,
        style={"padding": "20px 30px", "maxWidth": "1400px", "margin": "0 auto"},
        children=[
            html.H3("ข้อมูลสาขา", className="page-title fw-bold mb-3"),
            render_branch_kpis(df),

            dbc.Row(
                [
                    dbc.Col(card(chart_member_column(df), "จำนวนสมาชิกแต่ละสาขา"), lg=6),
                    dbc.Col(card(chart_income_line(df), "รายได้เฉลี่ยต่อคนรายสาขา"), lg=6),
                ],
                className="g-3 mb-3",
            ),

            dbc.Row(
                [
                    dbc.Col(card(chart_approval_mode(df), "ความเร็วการอนุมัติหลัก"), lg=6),
                    dbc.Col(card(chart_member_income_dual(df), "สมาชิก vs รายได้รวม"), lg=6),
                ],
                className="g-3",
            ),
        ],
    )

layout = create_branch_layout()
