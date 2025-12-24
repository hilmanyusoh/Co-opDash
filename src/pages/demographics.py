from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from ..data_manager import load_data
from ..components.kpi_cards import render_demographic_kpis

# ==================================================
# Data Processing
# ==================================================
def process_demographics(df):
    if df.empty: return df
    
    if "gender_name" in df.columns:
        df["Gender"] = df["gender_name"].map({"นาย": "ชาย", "นาง": "หญิง", "นางสาว": "หญิง"}).fillna("อื่นๆ")
    
    if "birthday" in df.columns:
        df["birthday"] = pd.to_datetime(df["birthday"], errors="coerce")
        df["Gen"] = df["birthday"].apply(lambda x: 
            "Baby Boomer" if pd.isnull(x) or x.year <= 1964 
            else "Gen X" if x.year <= 1980 
            else "Gen Y" if x.year <= 1996 else "Gen Z")
    
    if "income" in df.columns:
        df["Income_Clean"] = pd.to_numeric(df["income"].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
        bins = [0, 15000, 30000, 50000, 100000, float('inf')]
        labels = ["< 15K", "15K - 30K", "30K - 50K", "50K - 100K", "100K+"]
        df["Income_Level"] = pd.cut(df["Income_Clean"], bins=bins, labels=labels, right=False)

    if "registration_date" in df.columns:
        df["reg_date"] = pd.to_datetime(df["registration_date"], errors="coerce")
    
    return df

# ==================================================
# Chart Helpers
# ==================================================
def chart_style(fig, title, height=400):
    fig.update_layout(
        title=f"<b>{title}</b>",
        plot_bgcolor="rgba(245, 247, 250, 0.25)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=height,
        font=dict(family="Sarabun, sans-serif")
    )
    return fig

def add_depth(fig):
    fig.update_traces(marker_line_color='rgba(255, 255, 255, 0.5)', marker_line_width=1.5, opacity=0.87)
    return fig

# ==================================================
# Charts
# ==================================================
def chart_growth_time(df):
    if "reg_date" not in df.columns: return go.Figure()
    trend = df.groupby(df["reg_date"].dt.to_period("M").astype(str)).size().reset_index(name="count")
    
    fig = go.Figure(go.Scatter(
        x=trend["reg_date"], y=trend["count"],
        mode='lines+markers', line=dict(color="#ff4d4d", width=3),
        fill='tozeroy', fillcolor="#ffe3e3",
        marker=dict(size=8, line=dict(color='white', width=2))
    ))
    return chart_style(fig, "1. แนวโน้มการเพิ่มขึ้นของสมาชิกรายเดือน")

def chart_gender_career(df):
    career_col = "career_name" if "career_name" in df.columns else "career"
    top = df[career_col].value_counts().head(10).index
    data = df[df[career_col].isin(top)]
    
    fig = px.histogram(data, y=career_col, color="Gender", barmode="group", orientation="h",
                      color_discrete_map={"ชาย": "#4a90e2", "หญิง": "#e967e7", "อื่นๆ": "#95a5a6"})
    add_depth(fig)
    return chart_style(fig, "2. สัดส่วนเพศแยกตามกลุ่มอาชีพ (Top 10)")

def chart_income_pie(df):
    if "Income_Level" not in df.columns: return go.Figure()
    counts = df["Income_Level"].value_counts().reindex(["< 15K", "15K - 30K", "30K - 50K", "50K - 100K", "100K+"])
    
    fig = go.Figure(go.Pie(
        labels=counts.index, values=counts.values,
        marker=dict(colors=["#e0f2f1", "#ff5454", "#61ffcd", "#01af9e", "#028972"],
                   line=dict(color='#fff', width=2)),
        textinfo='percent+label'
    ))
    return chart_style(fig, "3. สัดส่วนสมาชิกแยกตามระดับรายได้")

def chart_gen_area(df):
    prov_col = "province_name" if "province_name" in df.columns else "province"
    top = df[prov_col].value_counts().head(8).index
    data = df[df[prov_col].isin(top)].groupby([prov_col, "Gen"]).size().reset_index(name="count")
    
    fig = px.bar(data, x=prov_col, y="count", color="Gen", barmode="stack",
                color_discrete_sequence=["#3498db", "#e74c3c", "#f39c12", "#9b59b6"])
    add_depth(fig)
    return chart_style(fig, "4. การกระจายกลุ่ม Generation ในจังหวัดหลัก")

def chart_income_career(df):
    career_col = "career_name" if "career_name" in df.columns else "career"
    avg = df[df["Income_Clean"] > 0].groupby(career_col)["Income_Clean"].mean().sort_values(ascending=False).head(10)
    
    fig = go.Figure(go.Bar(
        y=avg.index, x=avg.values, orientation='h',
        marker=dict(color=avg.values, colorscale='YlGnBu',
                   line=dict(color='rgba(255, 255, 255, 0.5)', width=1.5), opacity=0.87, showscale=False),
        text=[f'฿{v:,.0f}' for v in avg.values], textposition='auto'
    ))
    return chart_style(fig, "5. อาชีพที่มีรายได้เฉลี่ยสูงสุด")

# ==================================================
# Layout
# ==================================================
def create_demo_layout():
    df = load_data()
    df = process_demographics(df)
    
    if df.empty:
        return dbc.Container(dbc.Alert("ไม่พบข้อมูล", color="warning", className="mt-5"))

    card = lambda fig: dbc.Card(dbc.CardBody(dcc.Graph(figure=fig, config={'displayModeBar': False})), 
                                className="shadow-lg rounded-4 border-0 mb-4")

    return dbc.Container(
        fluid=True,
        style={"backgroundColor": "transparent", "padding": "20px"},
        children=[
            html.Div([
                html.H2("Members", className="fw-bold", 
                       style={"color": "#1e293b", "letterSpacing": "0.5px"}),
            ], className="mb-4"),

            render_demographic_kpis(df),

            dbc.Row([dbc.Col(card(chart_growth_time(df)), width=12)], className="g-4"),
            
            dbc.Row([
                dbc.Col(card(chart_gender_career(df)), lg=6),
                dbc.Col(card(chart_income_pie(df)), lg=6)
            ], className="g-4"),

            dbc.Row([
                dbc.Col(card(chart_gen_area(df)), lg=6),
                dbc.Col(card(chart_income_career(df)), lg=6)
            ], className="g-4"),
        ]
    )

layout = create_demo_layout()