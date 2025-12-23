from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from ..data_manager import load_data
from ..components.kpi_cards import render_overview_kpis

# ==================================================
# Helper Functions: Data Preprocessing
# ==================================================
def preprocess_data(df):
    if df.empty: return df
    if "income" in df.columns:
        df["Income_Clean"] = pd.to_numeric(df["income"].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
    if "gender_name" in df.columns:
        df["Gender_Group"] = df["gender_name"].map({"นาย": "ชาย", "นาง": "หญิง", "นางสาว": "หญิง"}).fillna("ไม่ระบุ")
    return df

# ==================================================
# 3.5D Charts (Modern Depth) with Fixed Height
# ==================================================

def create_gender_pie(df):
    """1. กราฟเพศแบบ Donut 3D-Look (ใช้เงาและมิติขอบ)"""
    counts = df["Gender_Group"].value_counts().reset_index()
    counts.columns = ["เพศ", "จำนวน"]
    
    fig = go.Figure(data=[go.Pie(
        labels=counts["เพศ"], 
        values=counts["จำนวน"],
        hole=.5,
        pull=[0.05, 0, 0],
        marker=dict(colors=["#6366f1", "#ec4899", "#94a3b8"], 
                    line=dict(color='#FFFFFF', width=2))
    )])
    
    fig.update_layout(
        title="<b>สัดส่วนเพศสมาชิก (Depth View)</b>",
        annotations=[dict(text='Gender', x=0.5, y=0.5, font_size=20, showarrow=False)],
        showlegend=True,
        margin=dict(t=50, b=20, l=10, r=10),
        height=400  # กำหนดความสูงคงที่
    )
    return fig

def create_branch_bar_3d(df):
    """2. กราฟแท่งรายสาขาแบบมีเงา (3D Bar Effect)"""
    branch_col = "branch_no" if "branch_no" in df.columns else "branch_code"
    counts = df[branch_col].value_counts().reset_index()
    counts.columns = ["สาขา", "จำนวน"]
    counts["สาขา"] = "สาขา " + counts["สาขา"].astype(str)
    
    fig = go.Figure(data=[go.Bar(
        x=counts["สาขา"], y=counts["จำนวน"],
        text=counts["จำนวน"],
        textposition='auto',
        marker=dict(
            color=counts["จำนวน"],
            colorscale='Viridis',
            line=dict(color='rgba(255, 255, 255, 0.5)', width=2)
        )
    )])
    
    fig.update_layout(
        title="<b>ความหนาแน่นสมาชิกรายสาขา</b>",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#e2e8f0"),
        height=400  # กำหนดความสูงคงที่
    )
    return fig

def create_province_top10_3d(df):
    """3. กราฟจังหวัด Top 10 แบบ Horizontal Depth"""
    prov_col = "province_name" if "province_name" in df.columns else "province"
    counts = df[prov_col].value_counts().head(10).reset_index()
    counts.columns = ["จังหวัด", "จำนวน"]
    counts = counts.sort_values("จำนวน", ascending=True)

    fig = go.Figure(go.Bar(
        x=counts["จำนวน"], y=counts["จังหวัด"],
        orientation='h',
        marker=dict(
            color='rgb(158,202,225)',
            line=dict(color='rgb(8,48,107)', width=1.5)
        )
    ))
    
    fig.update_layout(
        title="<b>Top 10 Provinces (Market Share)</b>",
        margin=dict(l=20, r=20, t=50, b=20),
        plot_bgcolor="rgba(240, 242, 245, 0.5)",
        height=400  # กำหนดความสูงคงที่
    )
    return fig

def create_income_ranking_3d(df):
    """4. กราฟรายได้เฉลี่ยแบบไล่สีมิติสูง (High Contrast)"""
    career_col = "career_name" if "career_name" in df.columns else "career"
    income_avg = df.groupby(career_col)["Income_Clean"].mean().sort_values(ascending=False).head(10).reset_index()
    income_avg.columns = ["อาชีพ", "รายได้"]

    fig = px.bar(
        income_avg, x="อาชีพ", y="รายได้",
        color="รายได้",
        color_continuous_scale="Reds",
        title="<b>Top 10 Career Income (Economic Power)</b>",
        template="plotly_white"
    )
    
    fig.update_traces(marker_line_color='rgb(8,48,107)', marker_line_width=1.5, opacity=0.8)
    fig.update_layout(
        coloraxis_showscale=False,
        height=400  # กำหนดความสูงคงที่
    )
    return fig

# Layout with Clean Background & Equal Chart Sizes


def create_analysis_layout():
    df = load_data()
    df = preprocess_data(df)

    if df.empty:
        return dbc.Container(dbc.Alert("ไม่พบข้อมูล", color="warning", className="mt-5 text-center"))

    return dbc.Container(
        fluid=True,
        style={"backgroundColor": "transparent", "padding": "20px"},  # ไม่มีสีพื้นหลัง
        children=[
            html.Div([
                html.H2("Executive Dashboard", className="fw-bold", style={"color": "#1e293b", "letterSpacing": "1px"}),
            ], className="mb-4"),

            # KPI Cards
            render_overview_kpis(df),

            # แถวที่ 1: กราฟขนาดเท่ากัน (50-50)
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=create_gender_pie(df))), 
                                className="shadow rounded-4 border-0 mb-4"), lg=6),
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=create_branch_bar_3d(df))), 
                                className="shadow rounded-4 border-0 mb-4"), lg=6),
            ], className="g-4"),

            # แถวที่ 2: กราฟขนาดเท่ากัน (50-50)
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=create_province_top10_3d(df))), 
                                className="shadow rounded-4 border-0 mb-4"), lg=6),
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=create_income_ranking_3d(df))), 
                                className="shadow rounded-4 border-0 mb-4"), lg=6),
            ], className="g-4"),
        ]
    )

layout = create_analysis_layout()