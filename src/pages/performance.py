from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from ..data_manager import load_data


from ..components.kpi_cards import render_performance_kpis

# ==================================================
# 1. Chart Style Helper
# ==================================================
def chart_style(fig, title):
    fig.update_layout(
        title=f"<b>{title}</b>",
        plot_bgcolor="rgba(245, 247, 250, 0.4)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Sarabun, sans-serif"),
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# ==================================================
# 2. กราฟพยากรณ์การเติบโต (Member Growth Forecast)
# ==================================================
def chart_growth_forecast(df):
    # เตรียมข้อมูลสะสมรายเดือน
    df['reg_date'] = pd.to_datetime(df['registration_date']).dt.to_period('M').dt.to_timestamp()
    monthly_df = df.groupby('reg_date').size().reset_index(name='new_members')
    monthly_df['cumulative_members'] = monthly_df['new_members'].cumsum()
    
    # คำนวณค่าพยากรณ์แบบง่าย (Linear Trend)
    last_val = monthly_df['cumulative_members'].iloc[-1]
    avg_growth = monthly_df['new_members'].tail(6).mean()
    
    # สร้างข้อมูลอนาคต 12 เดือน
    future_dates = pd.date_range(start=monthly_df['reg_date'].iloc[-1], periods=13, freq='MS')[1:]
    future_vals = [last_val + (avg_growth * i) for i in range(1, 13)]
    
    fig = go.Figure()
    
    # เส้นข้อมูลจริง
    fig.add_trace(go.Scatter(
        x=monthly_df['reg_date'], y=monthly_df['cumulative_members'],
        mode='lines+markers', name='ข้อมูลปัจจุบัน',
        line=dict(color='#007bff', width=4),
        fill='tozeroy', fillcolor='rgba(0, 123, 255, 0.1)'
    ))
    
    # เส้นพยากรณ์
    fig.add_trace(go.Scatter(
        x=future_dates, y=future_vals,
        mode='lines', name='คาดการณ์ 12 เดือนข้างหน้า',
        line=dict(color='#6f42c1', width=4, dash='dash')
    ))
    
    return chart_style(fig, "การคาดการณ์จำนวนสมาชิกสะสม (Growth Forecast)")

def create_performance_layout():
    df = load_data()
    if df.empty:
        return dbc.Container(dbc.Alert("ไม่พบข้อมูล", color="danger", className="mt-5"))

    if "income" in df.columns:
        df["Income_Clean"] = pd.to_numeric(df["income"].astype(str).str.replace(",", ""), errors="coerce").fillna(0)

    # ฟังก์ชันช่วยสร้าง Card
    def make_card(fig, width=12):
        return dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=fig, config={'displayModeBar': False})), 
                                className="shadow-sm border-0 rounded-4"), lg=width)

    return dbc.Container(fluid=True, className="p-4", children=[
        html.Div([
            html.H2("Performance & Growth Analysis", className="fw-bold", style={"color": "#1e293b"}),
            html.P("การวิเคราะห์แนวโน้มและการคาดการณ์เพื่อการตัดสินใจเชิงกลยุทธ์", className="text-muted")
        ], className="mb-4"),

        render_performance_kpis(df),

        # แถวที่ 1: การพยากรณ์ (เน้นใหญ่)
        dbc.Row([
            make_card(chart_growth_forecast(df), width=12),
        ], className="mb-4"),
    ])

layout = create_performance_layout()