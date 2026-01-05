from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from ..data_manager import load_data
from ..components.kpi_cards import render_overview_kpis

# ความสูงเท่ากันทุก dashboard
CHART_HEIGHT = 340

# ==================================================
# Data Preprocessing
# ==================================================
def preprocess_data(df):
    if df.empty:
        return df

    if "income" in df.columns:
        df["Income_Clean"] = (
            pd.to_numeric(
                df["income"].astype(str).str.replace(",", ""),
                errors="coerce"
            )
            .fillna(0)
        )

    if "gender_name" in df.columns:
        df["Gender_Group"] = (
            df["gender_name"]
            .map({"นาย": "ชาย", "นาง": "หญิง", "นางสาว": "หญิง"})
            .fillna("ไม่ระบุ")
        )

    return df

# ==================================================
# Chart Helper (ไม่กำหนด fontSize)
# ==================================================
def apply_layout(fig, title, height=CHART_HEIGHT):
    fig.update_layout(
        title={
            "text": f"<b>{title}</b>",
            "x": 0.02,
            "xanchor": "left",
        },
        height=height,
        plot_bgcolor="rgba(255, 255, 255, 0.02)",
        paper_bgcolor="rgba(255, 255, 255, 0)",
        font=dict(
            family="Sarabun, sans-serif",
            color="#334155",
        ),
        margin=dict(t=50, b=40, l=50, r=30),
        hoverlabel=dict(
            bgcolor="rgba(15, 23, 42, 0.95)",
            font_family="Sarabun, sans-serif",
            font_color="white",
            bordercolor="rgba(148, 163, 184, 0.3)",
        ),
    )
    return fig

# ==================================================
# Charts
# ==================================================
def chart_gender_pie(df):
    counts = df["Gender_Group"].value_counts()
    colors = ["#be185d", "#3730a3", "#475569"]

    fig = go.Figure(
        go.Pie(
            labels=counts.index,
            values=counts.values,
            hole=0.45,
            marker=dict(
                colors=colors,
                line=dict(color="#ffffff", width=2),
            ),
            pull=[0.05, 0.02, 0],
            textinfo="percent+label",
            textfont=dict(
                family="Sarabun",
                color="white",
            ),
            insidetextorientation="radial",
        )
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{label}</b><br>"
            "จำนวน: %{value} คน<br>"
            "สัดส่วน: %{percent}<extra></extra>"
        ),
        textposition="inside",
        rotation=45,
    )

    fig.update_layout(
        legend=dict(
            title="<b>เพศ</b>",
            orientation="h",
            xanchor="center",
            yanchor="top",
            x=0.5,
            y=-0.1,
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="rgba(148, 163, 184, 0.3)",
            borderwidth=1,
        ),
        margin=dict(t=50, b=60, l=30, r=30),
    )

    return apply_layout(fig, "สัดส่วนสมาชิกแยกตามเพศ")

def chart_branch_bar(df):
    branch_col = "branch_no" if "branch_no" in df.columns else "branch_code"
    counts = df[branch_col].value_counts().sort_index()

    fig = go.Figure()

    for branch, value in counts.items():
        label = f"สาขา {branch}"
        fig.add_trace(
            go.Bar(
                x=[label],
                y=[value],
                name=label,
                text=[value],
                textposition="outside",
                marker=dict(
                    line=dict(color="#ffffff", width=2),
                    opacity=0.9,
                ),
                hovertemplate=(
                    f"<b>{label}</b><br>"
                    "สมาชิก: %{y} คน<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        showlegend=True,
        legend=dict(
            title="<b>รายชื่อสาขา</b>",
            orientation="h",
            xanchor="center",
            yanchor="top",
            x=0.5,
            y=-0.15,
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="rgba(148, 163, 184, 0.3)",
            borderwidth=1,
        ),
        margin=dict(l=50, r=30, t=50, b=75),
        paper_bgcolor="rgba(255, 255, 255, 0)",
        plot_bgcolor="rgba(248, 250, 252, 0.3)",
    )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(
        title="<b>จำนวน</b>",
        showgrid=True,
        gridcolor="rgba(203, 213, 225, 0.4)",
    )

    return apply_layout(fig, "จำนวนสมาชิกแยกรายสาขา")

def chart_province_bar(df):
    prov_col = "province_name" if "province_name" in df.columns else "province"
    counts = df[prov_col].value_counts().head(8).sort_values()

    fig = go.Figure()

    for province, value in counts.items():
        fig.add_trace(
            go.Bar(
                y=[province],
                x=[value],
                orientation="h",
                name=province,
                text=[value],
                textposition="outside",
                marker=dict(
                    line=dict(color="#ffffff", width=2),
                    opacity=0.9,
                ),
                hovertemplate=(
                    f"<b>{province}</b><br>"
                    "สมาชิก: %{x} คน<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        showlegend=True,
        legend=dict(
            title="<b>จังหวัด</b>",
            orientation="h",
            xanchor="center",
            yanchor="top",
            x=0.5,
            y=-0.2,
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="rgba(148, 163, 184, 0.3)",
            borderwidth=1,
        ),
        margin=dict(r=30, l=100, t=50, b=85),
        paper_bgcolor="rgba(255, 255, 255, 0)",
        plot_bgcolor="rgba(248, 250, 252, 0.3)",
    )

    fig.update_xaxes(
        title="<b>จำนวนสมาชิก</b>",
        showgrid=True,
        gridcolor="rgba(203, 213, 225, 0.4)",
    )
    fig.update_yaxes(title="<b>จังหวัด</b>", showgrid=False)

    return apply_layout(fig, "Top 8 จังหวัดที่มีสมาชิกสูงสุด")

def chart_income_funnel(df):
    career_col = "career_name" if "career_name" in df.columns else "career"

    income_avg = (
        df.groupby(career_col)["Income_Clean"]
        .mean()
        .sort_values(ascending=True)
        .head(8)
        .reset_index()
    )

    fig = px.funnel(
        income_avg,
        y=career_col,
        x="Income_Clean",
        color=career_col,
        color_discrete_sequence=px.colors.qualitative.Prism,
        labels={
            "Income_Clean": "รายได้เฉลี่ย",
            career_col: "อาชีพ",
        },
    )

    fig.update_traces(
        texttemplate="฿%{value:,.0f}",
        marker=dict(line=dict(color="white", width=1.5)),
        opacity=0.9,
    )

    fig.update_layout(
        margin=dict(r=30, t=50, b=40, l=120),
        showlegend=False,
    )

    return apply_layout(fig, "Top 8 อันดับรายได้เฉลี่ยตามอาชีพ")

# ==================================================
# Layout
# ==================================================
def create_overview_layout():
    df = preprocess_data(load_data())

    if df.empty:
        return dbc.Container(
            dbc.Alert("ไม่พบข้อมูล", color="warning", className="mt-5")
        )

    card = lambda fig: dbc.Card(
        dbc.CardBody(
            dcc.Graph(
                figure=fig,
                config={"displayModeBar": False, "responsive": True},
            ),
            style={"padding": "18px"},
        ),
        className="shadow-sm rounded-3 border-0 mb-3",
    )

    return dbc.Container(
        fluid=True,
        style={
            "padding": "20px 30px",
            "maxWidth": "1400px",
            "margin": "0 auto",
        },
        children=[
            html.H3(
                "ข้อมูลภาพรวม",
                className="page-title fw-bold mb-3",
            ),

            render_overview_kpis(df),

            dbc.Row(
                [
                    dbc.Col(card(chart_gender_pie(df)), xs=12, lg=6),
                    dbc.Col(card(chart_branch_bar(df)), xs=12, lg=6),
                ],
                className="g-3 mb-3",
            ),

            dbc.Row(
                [
                    dbc.Col(card(chart_province_bar(df)), xs=12, lg=6),
                    dbc.Col(card(chart_income_funnel(df)), xs=12, lg=6),
                ],
                className="g-3",
            ),
        ],
    )

layout = create_overview_layout()
