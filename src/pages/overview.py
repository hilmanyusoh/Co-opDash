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
# Chart Helper (พื้นฐานสไตล์กราฟ)
# ==================================================
def apply_common_style(fig, title):
    fig.update_layout(
        title=f"<b>{title}</b>",
        plot_bgcolor="rgba(245, 247, 250, 0.25)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=400,
        font=dict(family="Sarabun, sans-serif")
    )
    return fig

# ==================================================
# Charts
# ==================================================

# 1. สัดส่วนสมาชิก - Legend อยู่ด้านบน
def chart_gender_pie(df):
    counts = df["Gender_Group"].value_counts()
    fig = go.Figure(go.Pie(
        labels=counts.index, values=counts.values, hole=0.5,
        marker=dict(colors=["#6366f1", "#ec4899", "#94a3b8"], line=dict(color='#fff', width=2))
    ))
    fig.update_traces(textinfo='percent+label')
    
    apply_common_style(fig, "สัดส่วนเพศสมาชิก")
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",   # แนวนอน
            yanchor="bottom",
            y=1.02,            # วางเหนือพื้นที่กราฟ
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=80, b=20, l=20, r=20) # เพิ่ม margin บนเพื่อให้ไม่ทับ Title
    )
    return fig

# 2. ความหนาแน่นสมาชิกรายสาขา - Legend ด้านข้าง (แยก 1, 2, 3...)
def chart_branch_bar(df):
    branch_col = "branch_no" if "branch_no" in df.columns else "branch_code"
    counts = df[branch_col].value_counts().sort_index().reset_index()
    counts.columns = ["สาขา", "จำนวน"]
    counts["สาขา"] = counts["สาขา"].astype(str) # แปลงเป็น string เพื่อให้ legend แยกเป็นรายค่า
    
    fig = px.bar(
        counts, x="สาขา", y="จำนวน", 
        color="สาขา", 
        text="จำนวน",
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig.update_traces(textposition='auto')
    
    apply_common_style(fig, "ความหนาแน่นสมาชิกรายสาขา")
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
        margin=dict(t=50, b=20, l=20, r=100)
    )
    return fig

# 3. Top 10 Provinces - Legend ด้านข้าง
def chart_province_bar(df):
    prov_col = "province_name" if "province_name" in df.columns else "province"
    counts = df[prov_col].value_counts().head(10).reset_index()
    counts.columns = ["จังหวัด", "จำนวน"]
    
    fig = px.bar(
        counts, x="จำนวน", y="จังหวัด", orientation='h',
        color="จังหวัด",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    apply_common_style(fig, "Top 10 Provinces")
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
        margin=dict(t=50, b=20, l=20, r=120)
    )
    return fig

# 4. Top 10 Career Income - Legend ด้านข้าง
def chart_income_bar(df):
    career_col = "career_name" if "career_name" in df.columns else "career"
    income_avg = df.groupby(career_col)["Income_Clean"].mean().sort_values(ascending=False).head(10).reset_index()
    income_avg.columns = ["อาชีพ", "รายได้เฉลี่ย"]
    
    fig = px.bar(
        income_avg, x="อาชีพ", y="รายได้เฉลี่ย",
        color="อาชีพ",
        text_auto=',.0f',
        color_discrete_sequence=px.colors.qualitative.Vivid
    )
    
    apply_common_style(fig, "Top 10 Career Income")
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
        margin=dict(t=50, b=20, l=20, r=120)
    )
    return fig

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
            html.H2("ข้อมูลภาพรวม", className="fw-bold mb-4", 
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