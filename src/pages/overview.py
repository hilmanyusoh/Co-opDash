from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from ..data_manager import load_data
from ..components.kpi_cards import render_overview_kpis

# ==================================================
# Data Preprocessing
# ==================================================
def preprocess_data(df):
    if df.empty: return df
    if "income" in df.columns:
        df["Income_Clean"] = pd.to_numeric(df["income"].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
    if "gender_name" in df.columns:
        df["Gender_Group"] = df["gender_name"].map({"นาย": "ชาย", "นาง": "หญิง", "นางสาว": "หญิง"}).fillna("ไม่ระบุ")
    return df

# ==================================================
# Chart Helper
# ==================================================
def chart_style(fig, title):
    fig.update_layout(
        title=f"<b>{title}</b>",
        plot_bgcolor="rgba(245, 247, 250, 0.25)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin=dict(t=50, b=20, l=20, r=20)
    )
    return fig

# ==================================================
# Charts
# ==================================================
def chart_gender_pie(df):
    counts = df["Gender_Group"].value_counts()
    fig = go.Figure(go.Pie(
        labels=counts.index, values=counts.values, hole=0.5, pull=[0.05, 0, 0],
        marker=dict(colors=["#6366f1", "#ec4899", "#94a3b8"], line=dict(color='#fff', width=2))
    ))
    fig.update_traces(textinfo='percent+label')
    return chart_style(fig, "สัดส่วนเพศสมาชิก")

def chart_branch_bar(df):
    branch_col = "branch_no" if "branch_no" in df.columns else "branch_code"
    counts = df[branch_col].value_counts().reset_index()
    counts.columns = ["สาขา", "จำนวน"]
    
    fig = go.Figure(go.Bar(
        x=["สาขา " + str(x) for x in counts["สาขา"]], y=counts["จำนวน"],
        marker=dict(color=counts["จำนวน"], colorscale='Viridis',
                   line=dict(color='rgba(255,255,255,0.5)', width=1.5)),
        text=counts["จำนวน"], textposition='auto'
    ))
    return chart_style(fig, "ความหนาแน่นสมาชิกรายสาขา")

def chart_province_bar(df):
    prov_col = "province_name" if "province_name" in df.columns else "province"
    counts = df[prov_col].value_counts().head(10).sort_values()
    
    fig = go.Figure(go.Bar(
        x=counts.values, y=counts.index, orientation='h',
        marker=dict(color='rgb(158,202,225)', line=dict(color='rgb(8,48,107)', width=1.5))
    ))
    return chart_style(fig, "Top 10 Provinces")

def chart_income_bar(df):
    career_col = "career_name" if "career_name" in df.columns else "career"
    income_avg = df.groupby(career_col)["Income_Clean"].mean().sort_values(ascending=False).head(10)
    
    fig = go.Figure(go.Bar(
        x=income_avg.index, y=income_avg.values,
        marker=dict(color=income_avg.values, colorscale='Reds',
                   line=dict(color='rgb(8,48,107)', width=1.5), opacity=0.85, showscale=False),
        text=[f'฿{v:,.0f}' for v in income_avg.values], textposition='auto'
    ))
    return chart_style(fig, "Top 10 Career Income")

# ==================================================
# Layout
# ==================================================
def create_analysis_layout():
    df = load_data()
    df = preprocess_data(df)

    if df.empty:
        return dbc.Container(dbc.Alert("ไม่พบข้อมูล", color="warning", className="mt-5"))

    card = lambda fig: dbc.Card(dbc.CardBody(dcc.Graph(figure=fig)), className="shadow-lg rounded-4 border-0 mb-4")

    return dbc.Container(
        fluid=True,
        style={"backgroundColor": "transparent", "padding": "20px"},
        children=[
            html.H2("Overview", className="fw-bold mb-4", 
                   style={"color": "#1e293b", "letterSpacing": "0.5px"}),
            
            render_overview_kpis(df),

            dbc.Row([
                dbc.Col(card(chart_gender_pie(df)), lg=6),
                dbc.Col(card(chart_branch_bar(df)), lg=6)
            ], className="g-4"),

            dbc.Row([
                dbc.Col(card(chart_province_bar(df)), lg=6),
                dbc.Col(card(chart_income_bar(df)), lg=6)
            ], className="g-4")
        ]
    )

layout = create_analysis_layout()