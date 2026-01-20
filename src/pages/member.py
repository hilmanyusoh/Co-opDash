from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from functools import lru_cache

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
            if pd.isnull(x): return "Unknown"
            if x.year <= 1964: return "Baby Boomer"
            if x.year <= 1980: return "Gen X"
            if x.year <= 1996: return "Gen Y"
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
# Cache Data (🔥 สำคัญมาก)
# ==================================================
@lru_cache(maxsize=1)
def load_member_data():
    df = load_data()
    return process_member(df)


# ==================================================
# Layout Helper
# ==================================================
def apply_layout(fig, height=CHART_HEIGHT):
    fig.update_layout(
        height=height,
        margin=dict(t=20, b=40, l=40, r=30),
        plot_bgcolor="rgba(248,250,252,0.3)",
        paper_bgcolor="rgba(255,255,255,0)",
        font=dict(family="Sarabun, sans-serif", color="#334155"),
        transition_duration=0,  # 🔥 ปิด animation
    )
    return fig


# ==================================================
# Charts
# ==================================================
def chart_growth_time(df):
    if "reg_date" not in df.columns:
        return go.Figure()

    trend = (
        df.dropna(subset=["reg_date"])
        .groupby(df["reg_date"].dt.to_period("M"))
        .size()
        .reset_index(name="count")
    )

    if trend.empty:
        return go.Figure()

    trend["reg_date"] = trend["reg_date"].dt.to_timestamp()
    trend["cumulative"] = trend["count"].cumsum()

    fig = go.Figure(
        go.Scatter(
            x=trend["reg_date"],
            y=trend["cumulative"],
            mode="lines",
            line=dict(color="#3b82f6", width=3),
            fill="tozeroy",
            fillcolor="rgba(59,130,246,0.1)",
            hovertemplate="<b>%{x|%b %Y}</b><br>สมาชิกสะสม: %{y:,} คน<extra></extra>",
        )
    )

    fig.update_layout(
        hovermode="x unified",
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True),
    )

    return apply_layout(fig, height=380)


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
        go.Pie(labels=counts.index, values=counts.values, hole=0.45)
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
    )

    fig.update_layout(
        legend=dict(orientation="h", y=-0.45),
        xaxis=dict(title=None),
        yaxis=dict(title="จำนวน (คน)"),
    )

    return apply_layout(fig)


def chart_monthly_members(df):
    if "reg_date" not in df.columns:
        return go.Figure()

    df_2025 = df[df["reg_date"].dt.year == 2025]

    monthly = (
        df_2025
        .groupby(df_2025["reg_date"].dt.month)
        .size()
        .reindex(range(1, 13), fill_value=0)
        .reset_index(name="total")
    )

    months = ["ม.ค.","ก.พ.","มี.ค.","เม.ย.","พ.ค.","มิ.ย.",
              "ก.ค.","ส.ค.","ก.ย.","ต.ค.","พ.ย.","ธ.ค."]

    fig = go.Figure(
        go.Bar(
            x=months,
            y=monthly["total"],
            text=monthly["total"],
            textposition="outside",
        )
    )

    fig.update_layout(showlegend=False)
    return apply_layout(fig)


# ==================================================
# Card Component
# ==================================================
def chart_card(fig, title):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H6(title, className="fw-bold mb-2"),
                dcc.Graph(figure=fig, config={"displayModeBar": False}),
            ],
            style={"padding": "12px"},
        ),
        className="shadow-sm rounded-3 border-0 mb-3",
    )


# ==================================================
# Layout
# ==================================================
def member_layout():
    df = load_member_data()

    return dbc.Container(
        fluid=True,
        style={"padding": "20px 30px", "maxWidth": "1400px"},
        children=[
            html.H3("ข้อมูลสมาชิก", className="fw-bold mb-3"),
            render_member_kpis(df),

            dbc.Row([
                dbc.Col(chart_card(chart_growth_time(df), "แนวโน้มการเพิ่มขึ้นของสมาชิกรายเดือน"), lg=12),
            ]),

            dbc.Row([
                dbc.Col(chart_card(chart_monthly_members(df), "จำนวนสมาชิกใหม่รายเดือน"), lg=6),
                dbc.Col(chart_card(chart_gender_career(df), "สัดส่วนเพศแยกตามกลุ่มอาชีพ"), lg=6),
            ]),

            dbc.Row([
                dbc.Col(chart_card(chart_income_pie(df), "สัดส่วนสมาชิกแยกตามระดับรายได้"), lg=6),
                dbc.Col(chart_card(chart_gen_area(df), "การกระจาย Generation ตามจังหวัด"), lg=6),
            ]),
        ],
    )


layout = member_layout()
