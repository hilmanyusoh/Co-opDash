from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from ..data_manager import load_data
from ..components.kpi_cards import render_overview_kpis
from ..components.chart_card import chart_card
from ..components.theme import THEME

# ==================================================
# Config
# ==================================================
CHART_HEIGHT = 340

# ==================================================
# Data Preprocessing
# ==================================================
def preprocess_overview(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    # Income
    if "income" in df.columns:
        df["Income_Clean"] = (
            df["income"]
            .astype(str)
            .str.replace(",", "")
            .pipe(pd.to_numeric, errors="coerce")
            .fillna(0)
        )

    # Gender
    if "gender_name" in df.columns:
        df["Gender_Group"] = (
            df["gender_name"]
            .map({"นาย": "ชาย", "นาง": "หญิง", "นางสาว": "หญิง"})
            .fillna("ไม่ระบุ")
        )

    return df

# ==================================================
# Chart Layout Helper (NO title here)
# ==================================================
def apply_layout(fig, height=CHART_HEIGHT):
    fig.update_layout(
        height=height,
        margin=dict(t=40, b=40, l=50, r=30),
        paper_bgcolor=THEME["paper"],
        plot_bgcolor=THEME["bg_plot"],
        font=dict(
            family="Sarabun, sans-serif",
            color=THEME["text"],
        ),
        hoverlabel=dict(
            bgcolor="rgba(15,23,42,0.95)",
            font_color="white",
            bordercolor=THEME["grid"],
        ),
    )
    return fig

# ==================================================
# Charts
# ==================================================
def chart_gender_pie(df):
    if "Gender_Group" not in df.columns:
        return go.Figure()

    counts = df["Gender_Group"].value_counts()

    fig = go.Figure(
        go.Pie(
            labels=counts.index,
            values=counts.values,
            hole=0.45,
            marker=dict(
                colors=[
                    THEME["pink"],
                    THEME["primary"],
                    THEME["muted"],
                ],
                line=dict(color="white", width=2),
            ),
            textinfo="percent+label",
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
    )

    fig.update_layout(
        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=-0.15,
        )
    )

    return apply_layout(fig)


def chart_branch_bar(df):
    branch_col = "branch_no" if "branch_no" in df.columns else "branch_code"
    if branch_col not in df.columns:
        return go.Figure()

    counts = df[branch_col].value_counts().sort_index()

    fig = go.Figure(
        go.Bar(
            x=[f"สาขา {b}" for b in counts.index],
            y=counts.values,
            text=counts.values,
            textposition="outside",
            marker=dict(
                color=THEME["primary"],
                line=dict(color="white", width=2),
            ),
            hovertemplate="<b>%{x}</b><br>สมาชิก: %{y} คน<extra></extra>",
        )
    )

    fig.update_yaxes(
        title="จำนวนสมาชิก",
        gridcolor=THEME["grid"],
    )
    fig.update_xaxes(showgrid=False)

    return apply_layout(fig)


def chart_province_bar(df):
    prov_col = "province_name" if "province_name" in df.columns else "province"
    if prov_col not in df.columns:
        return go.Figure()

    counts = df[prov_col].value_counts().head(8).sort_values()

    fig = go.Figure(
        go.Bar(
            y=counts.index,
            x=counts.values,
            orientation="h",
            text=[f"{v:,} คน" for v in counts.values],
            textposition="inside",
            marker=dict(
                color=counts.values,
                colorscale=[
                    [0.0, THEME["info"]],
                    [0.5, THEME["primary"]],
                    [1.0, THEME["purple"]],
                ],
                line=dict(color="white", width=2),
            ),
            hovertemplate="<b>%{y}</b><br>สมาชิก: %{x:,} คน<extra></extra>",
        )
    )

    fig.update_layout(showlegend=False)

    return apply_layout(fig)


def chart_income_funnel(df):
    branch_col = "branch_no" if "branch_no" in df.columns else "branch_code"
    if branch_col not in df.columns:
        return go.Figure()

    income_branch = (
        df.groupby(branch_col, observed=False)["Income_Clean"]
        .sum()
        .sort_values(ascending=False)
        .head(8)
        .reset_index()
    )

    income_branch["Branch_Label"] = income_branch[branch_col].apply(
        lambda x: f"สาขา {x}"
    )

    colors = [
        THEME["primary"],
        THEME["info"],
        THEME["success"],
        THEME["purple"],
        THEME["pink"],
        THEME["orange"],
        THEME["warning"],
        THEME["danger"],
    ]

    fig = px.funnel(
        income_branch,
        y="Branch_Label",
        x="Income_Clean",
        color="Branch_Label",
        color_discrete_sequence=colors,
    )

    fig.update_traces(
        texttemplate="฿%{value:,.0f}",
        textposition="inside",
        marker=dict(line=dict(color="white", width=2)),
        hovertemplate="<b>%{y}</b><br>รายได้รวม: ฿%{x:,.2f}<extra></extra>",
    )

    fig.update_layout(showlegend=False)

    return apply_layout(fig)

# ==================================================
# Layout
# ==================================================
def overview_layout():
    df = preprocess_overview(load_data())

    if df.empty:
        return dbc.Container(
            dbc.Alert("ไม่พบข้อมูล", color="warning", className="mt-5")
        )

    return dbc.Container(
        fluid=True,
        style={
            "padding": "20px 30px",
            "maxWidth": "1400px",
            "margin": "0 auto",
        },
        children=[
            html.H3("ข้อมูลภาพรวม", className="page-title fw-bold mb-3"),

            render_overview_kpis(df),

            dbc.Row(
                [
                    dbc.Col(
                        chart_card(chart_gender_pie(df), "สัดส่วนสมาชิกแยกตามเพศ"),
                        lg=6,
                    ),
                    dbc.Col(
                        chart_card(chart_branch_bar(df), "จำนวนสมาชิกแยกรายสาขา"),
                        lg=6,
                    ),
                ],
                className="g-3 mb-3",
            ),

            dbc.Row(
                [
                    dbc.Col(
                        chart_card(chart_province_bar(df), "Top 8 จังหวัดที่มีสมาชิกสูงสุด"),
                        lg=6,
                    ),
                    dbc.Col(
                        chart_card(chart_income_funnel(df), "รายได้รวมสูงสุดแยกตามสาขา"),
                        lg=6,
                    ),
                ],
                className="g-3",
            ),
        ],
    )

layout = overview_layout()
