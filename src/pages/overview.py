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
def chart_style(fig, title, height=350):
    fig.update_layout(
        title=f"<b>{title}</b>",
        title_font_size=14,
        plot_bgcolor="rgba(245, 247, 250, 0.25)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=height,
        font=dict(family="Sarabun, sans-serif", size=11),
        margin=dict(t=50, b=20, l=20, r=20)
    )
    return fig

def add_depth(fig):
    fig.update_traces(marker_line_color='rgba(255, 255, 255, 0.5)', marker_line_width=1.5, opacity=0.87)
    return fig

# ==================================================
# Charts
# ==================================================
def chart_gender_pie(df):
    counts = df["Gender_Group"].value_counts()
    fig = go.Figure(go.Pie(
        labels=counts.index, values=counts.values, hole=0.45,
        marker=dict(colors=["#6366f1", "#ec4899", "#94a3b8"], line=dict(color='#fff', width=2)),
        textinfo='percent+label', textfont_size=11
    ))
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5, font=dict(size=10))
    )
    return chart_style(fig, "สัดส่วนเพศ")

def chart_branch_bar(df):
    branch_col = "branch_no" if "branch_no" in df.columns else "branch_code"
    counts = df[branch_col].value_counts().sort_index()
    
    fig = go.Figure(go.Bar(
        x=["สาขา " + str(x) for x in counts.index],
        y=counts.values,
        marker=dict(
            color=counts.values, colorscale='Viridis',
            line=dict(color='rgba(255, 255, 255, 0.5)', width=1.5), opacity=0.87
        ),
        text=counts.values, textposition='outside', showlegend=False
    ))
    return chart_style(fig, "สมาชิกรายสาขา")

def chart_province_bar(df):
    prov_col = "province_name" if "province_name" in df.columns else "province"
    counts = df[prov_col].value_counts().head(8).sort_values()
    
    fig = go.Figure(go.Bar(
        x=counts.values, y=counts.index, orientation='h',
        marker=dict(
            color=counts.values, colorscale='Blues',
            line=dict(color='rgba(255, 255, 255, 0.5)', width=1.5), opacity=0.87
        ),
        text=counts.values, textposition='auto', showlegend=False
    ))
    return chart_style(fig, "Top 8 จังหวัด")

def chart_income_bar(df):
    career_col = "career_name" if "career_name" in df.columns else "career"
    income_avg = df.groupby(career_col)["Income_Clean"].mean().sort_values(ascending=False).head(8)
    
    fig = go.Figure(go.Bar(
        x=income_avg.index, y=income_avg.values,
        marker=dict(
            color=income_avg.values, colorscale='Oranges',
            line=dict(color='rgba(255, 255, 255, 0.5)', width=1.5), opacity=0.87, showscale=False
        ),
        text=[f'฿{v:,.0f}' for v in income_avg.values], 
        textposition='outside', showlegend=False
    ))
    fig.update_xaxes(tickangle=-45)
    return chart_style(fig, "Top 8 รายได้ตามอาชีพ")

# ==================================================
# Layout
# ==================================================
def create_analysis_layout():
    df = load_data()
    df = preprocess_data(df)

    if df.empty:
        return dbc.Container(dbc.Alert("ไม่พบข้อมูล", color="warning", className="mt-5"))

    card = lambda fig: dbc.Card(
        dbc.CardBody(dcc.Graph(figure=fig, config={'displayModeBar': False}), 
                     style={"padding": "10px"}), 
        className="shadow-lg rounded-4 border-0 mb-3"
    )

    return dbc.Container(
        fluid=True,
        style={"backgroundColor": "transparent", "padding": "15px"},
        children=[
            html.Div([
                html.H3("ข้อมูลภาพรวม", className="fw-bold mb-3", 
                       style={"color": "#1e293b", "letterSpacing": "0.5px"}),
            ]),
            
            render_overview_kpis(df),

            dbc.Row([
                dbc.Col(card(chart_gender_pie(df)), lg=6),
                dbc.Col(card(chart_branch_bar(df)), lg=6)
            ], className="g-3"),

            dbc.Row([
                dbc.Col(card(chart_province_bar(df)), lg=6),
                dbc.Col(card(chart_income_bar(df)), lg=6)
            ], className="g-3")
        ]
    )

layout = create_analysis_layout()