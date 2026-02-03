from dash import dcc, html, Input, Output, callback
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


@lru_cache(maxsize=1)
def load_member_data():
    df = load_data()
    return process_member(df)


def apply_member_layout(fig, height=CHART_HEIGHT):
    fig.update_layout(
        height=height,
        margin=dict(t=20, b=40, l=40, r=30),
        plot_bgcolor="rgba(248,250,252,0.3)",
        paper_bgcolor="rgba(255,255,255,0)",
        font=dict(family="Sarabun, sans-serif", color="#334155"),
        transition_duration=0,
    )
    return fig


# ==================================================
# Charts (ใช้ข้อมูลที่กรองมาแล้วจาก Callback)
# ==================================================
def chart_growth_time(df):
    if "reg_date" not in df.columns or df.empty:
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

    fig = go.Figure(
        go.Scatter(
            x=trend["reg_date"],
            y=trend["count"],
            mode="lines+markers",
            line=dict(color="#3b82f6", width=3, shape='spline'),
            marker=dict(size=6, color="#1e40af"),
            fill="tozeroy",
            fillcolor="rgba(59, 130, 246, 0.1)",
            hovertemplate="<b>%{x|%b %Y}</b><br>สมาชิกใหม่: %{y:,} คน<extra></extra>",
        )
    )

    fig.update_layout(
        hovermode="x unified",
        showlegend=False,
        xaxis=dict(showgrid=False, tickformat="%b %Y"),
        yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
    )

    return apply_member_layout(fig, height=380)

def chart_gender_career(df):
    if "Gender" not in df.columns or df.empty: return go.Figure()
    career_col = "career_name" if "career_name" in df.columns else "career"
    if career_col not in df.columns: return go.Figure()

    top = df[career_col].value_counts().head(5).index
    data = df[df[career_col].isin(top)]

    fig = px.histogram(data, y=career_col, color="Gender", orientation="h", barmode="group")
    fig.update_layout(legend=dict(orientation="h", y=-0.25))
    return apply_member_layout(fig)

def chart_income_pie(df):
    if "Income_Level" not in df.columns or df.empty: return go.Figure()
    counts = df["Income_Level"].value_counts().sort_index()
    fig = go.Figure(go.Pie(labels=counts.index, values=counts.values, hole=0.45))
    fig.update_layout(legend=dict(orientation="h", y=-0.15))
    return apply_member_layout(fig)

def chart_gen_area(df):
    if "Gen" not in df.columns or df.empty: return go.Figure()
    prov_col = "province_name" if "province_name" in df.columns else "province"
    if prov_col not in df.columns: return go.Figure()

    data = df.groupby([prov_col, "Gen"]).size().reset_index(name="count")
    fig = px.bar(data, x=prov_col, y="count", color="Gen", barmode="stack")
    fig.update_layout(legend=dict(orientation="h", y=-0.45))
    return apply_member_layout(fig)

def chart_monthly_members(df, selected_year):
    if "reg_date" not in df.columns or df.empty: return go.Figure()
    
    monthly = (
        df.groupby(df["reg_date"].dt.month)
        .size()
        .reindex(range(1, 13), fill_value=0)
        .reset_index(name="total")
    )

    months = ["ม.ค.","ก.พ.","มี.ค.","เม.ย.","พ.ค.","มิ.ย.","ก.ค.","ส.ค.","ก.ย.","ต.ค.","พ.ย.","ธ.ค."]
    fig = go.Figure(go.Bar(x=months, y=monthly["total"], text=monthly["total"], textposition="outside", marker_color="#3b82f6"))
    return apply_member_layout(fig)

def chart_card(fig, title):
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="fw-bold mb-2"),
            dcc.Graph(figure=fig, config={"displayModeBar": False}),
        ], style={"padding": "12px"}),
        className="shadow-sm rounded-3 border-0 mb-3",
    )

# ==================================================
# Layout & Callback
# ==================================================
# ==================================================
# Layout & Callback
# ==================================================
def member_layout():
    df = load_member_data()
    
    # 1. เตรียมรายการปี และเพิ่มตัวเลือก "ทั้งหมด" ไว้บนสุด
    years = sorted(df["reg_date"].dt.year.unique().tolist(), reverse=True) if "reg_date" in df.columns else []
    year_options = [{"label": "ทั้งหมดทุกปี", "value": "all"}] + [{"label": f"ปี {y}", "value": y} for y in years]

    return dbc.Container(
        fluid=True,
        style={"padding": "20px 30px", "maxWidth": "1400px"},
        children=[
            dbc.Row([
                dbc.Col(html.H3("ข้อมูลสมาชิก", className="fw-bold mb-0"), width=8),
                dbc.Col([
                    html.Span("เลือกช่วงเวลา:", className="me-2 small text-muted"),
                    dcc.Dropdown(
                        id="member-year-dropdown",
                        options=year_options,
                        value="all", # ตั้งค่าเริ่มต้นเป็น "ทั้งหมด"
                        clearable=False,
                        style={"width": "160px"}
                    )
                ], width=4, className="d-flex align-items-center justify-content-end")
            ], className="mb-4 align-items-center"),

            dcc.Loading(
                id="loading-member-charts",
                children=html.Div(id="member-charts-container")
            )
        ],
    )

@callback(
    Output("member-charts-container", "children"),
    Input("member-year-dropdown", "value")
)
def update_member_dashboard(selected_year):
    df_all = load_member_data()
    
    # 2. เงื่อนไขการกรอง: ถ้าไม่ใช่ "all" ให้กรองตามปี ถ้าใช่ "all" ให้ใช้ข้อมูลทั้งหมด
    if selected_year != "all" and "reg_date" in df_all.columns:
        df = df_all[df_all["reg_date"].dt.year == selected_year]
        title_suffix = f"ปี {selected_year}"
    else:
        df = df_all
        title_suffix = "ทั้งหมดทุกปี"

    return [
        render_member_kpis(df),

        dbc.Row([
            dbc.Col(chart_card(chart_growth_time(df), f"แนวโน้มการสมัครสมาชิกรายเดือน ({title_suffix})"), lg=12),
        ]),

        dbc.Row([
            dbc.Col(chart_card(chart_monthly_members(df, selected_year), f"จำนวนสมาชิกใหม่รายเดือน ({title_suffix})"), lg=6),
            dbc.Col(chart_card(chart_gender_career(df), "สัดส่วนเพศแยกตามกลุ่มอาชีพ"), lg=6),
        ]),

        dbc.Row([
            dbc.Col(chart_card(chart_income_pie(df), "สัดส่วนสมาชิกแยกตามระดับรายได้"), lg=6),
            dbc.Col(chart_card(chart_gen_area(df), "การกระจาย Generation ตามจังหวัด"), lg=6),
        ]),
    ]

layout = member_layout()