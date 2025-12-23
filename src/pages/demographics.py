from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from ..data_manager import load_data
from ..components.kpi_cards import render_demographic_kpis      


# Data Processing Logic

def process_demographics(df):
    if df.empty:
        return df
    
    # รวมกลุ่มเพศเพื่อใช้ในกราฟ Pie
    if "gender_name" in df.columns:
        df["gender_simple"] = df["gender_name"].map({
            "นาย": "Male",
            "นาง": "Female",
            "นางสาว": "Female"
        }).fillna("Other")
    
    return df


# Visual Chart Functions

def create_age_pyramid_style(df):
    if "Age_Group" not in df.columns:
        return px.bar(title="ไม่มีข้อมูลช่วงอายุ")
    
    age_order = ["< 20", "20-29", "30-39", "40-49", "50-59", "60+"]
    age_counts = df["Age_Group"].value_counts().reindex(age_order).reset_index()
    age_counts.columns = ["ช่วงอายุ", "จำนวนสมาชิก"]

    fig = px.bar(
        age_counts, x="จำนวนสมาชิก", y="ช่วงอายุ",
        orientation="h",
        text_auto=True,
        title="<b>โครงสร้างประชากรตามช่วงอายุ</b>",
        color="จำนวนสมาชิก",
        color_continuous_scale="Purples"
    )
    fig.update_layout(
        showlegend=False, 
        coloraxis_showscale=False,
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=50, b=20, l=20, r=20)
    )
    return fig

def create_gender_donut(df):
    if "gender_simple" not in df.columns:
        return px.pie(title="ไม่มีข้อมูลเพศ")
    
    fig = px.pie(
        df, names="gender_simple",
        hole=0.6,
        title="<b>สัดส่วนเพศสมาชิก</b>",
        color="gender_simple",
        color_discrete_map={"Male": "#007bff", "Female": "#fd7e14"} # สีน้ำเงิน และ ส้ม ตาม KPI
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center")
    )
    return fig

def create_top_career_chart(df):
    career_col = "career_name" if "career_name" in df.columns else "career"
    if career_col not in df.columns:
        return px.bar(title="ไม่มีข้อมูลอาชีพ")
        
    career_counts = df[career_col].value_counts().head(10).reset_index()
    career_counts.columns = ["อาชีพ", "จำนวนคน"]
    
    fig = px.bar(
        career_counts, x="จำนวนคน", y="อาชีพ",
        orientation="h",
        text_auto=True,
        title="<b>10 อันดับอาชีพที่พบบ่อยที่สุด</b>",
        color="จำนวนคน",
        color_continuous_scale="GnBu"
    )
    fig.update_layout(
        yaxis={'categoryorder':'total ascending'},
        coloraxis_showscale=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


# Main Layout

def create_demo_layout():
    df = load_data()
    df = process_demographics(df)
    
    if df.empty:
        return dbc.Container(dbc.Alert("ไม่พบข้อมูลสำหรับการวิเคราะห์ประชากรศาสตร์", color="warning", className="mt-5"))

    return dbc.Container(
        fluid=True,
        className="p-4",
        children=[
            # Header Section
            html.Div([
                html.H2("Demographics Intelligence", className="fw-bold text-dark"),
            ], className="mb-4"),

            # KPI Cards Section (เรียกใช้ฟังก์ชันจาก kpi_cards.py)
            render_demographic_kpis(df),

            # Charts Row 1
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=create_age_pyramid_style(df), config={"displayModeBar": False})), className="shadow-sm border-0"), lg=7),
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=create_gender_donut(df), config={"displayModeBar": False})), className="shadow-sm border-0"), lg=5),
            ], className="g-4 mb-4"),

            # Charts Row 2
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=create_top_career_chart(df), config={"displayModeBar": False})), className="shadow-sm border-0"), width=12),
            ]),
        ]
    )

layout = create_demo_layout()