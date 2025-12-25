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
        margin=dict(l=60, r=60, t=100, b=60),
        # Legend ด้านบนกึ่งกลาง
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.05, 
            xanchor="center", 
            x=0.5
        ),
        hovermode="x unified"
    )
    # ปรับแต่ง Grid
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.05)", zeroline=False)
    return fig

# ==================================================
# 2. กราฟพยากรณ์การเติบโต (Member Growth Forecast)
# ==================================================
def chart_growth_forecast(df):
    if df.empty or 'registration_date' not in df.columns: return go.Figure()

    # --- เตรียมข้อมูลประวัติศาสตร์ ---
    df['reg_date'] = pd.to_datetime(df['registration_date']).dt.to_period('M').dt.to_timestamp()
    monthly_df = df.groupby('reg_date').size().reset_index(name='new_members')
    monthly_df['cumulative_members'] = monthly_df['new_members'].cumsum()
    
    # --- การพยากรณ์ (Linear Forecast with Confidence Interval) ---
    last_date = monthly_df['reg_date'].iloc[-1]
    last_val = monthly_df['cumulative_members'].iloc[-1]
    
    # คำนวณอัตราการเติบโตเฉลี่ย 6 เดือนล่าสุด (ให้น้ำหนักเดือนล่าสุดมากกว่า)
    recent_growth = monthly_df['new_members'].tail(6).tolist()
    avg_growth = np.average(recent_growth, weights=[1, 2, 3, 4, 5, 6])
    
    # สร้างช่วงเวลาอนาคต 12 เดือน
    future_dates = pd.date_range(start=last_date, periods=13, freq='MS')[1:]
    forecast_vals = [last_val + (avg_growth * i) for i in range(1, 13)]
    
    # เชื่อมจุดล่าสุด
    f_x = [last_date] + list(future_dates)
    f_y = [last_val] + forecast_vals
    
    # คำนวณขอบเขตความเชื่อมั่น (Upper/Lower Bound +/- 15%)
    upper_bound = [v * (1 + 0.15 * (i/12)) for i, v in enumerate(f_y)]
    lower_bound = [v * (1 - 0.15 * (i/12)) for i, v in enumerate(f_y)]

    fig = go.Figure()

    # 1. Confidence Interval (พื้นที่คาดการณ์)
    fig.add_trace(go.Scatter(
        x=f_x + f_x[::-1],
        y=upper_bound + lower_bound[::-1],
        fill='toself',
        fillcolor='rgba(139, 92, 246, 0.1)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        name='ช่วงความเชื่อมั่น (Confidence Range)',
    ))

    # 2. เส้นข้อมูลจริง (Actual Data)
    fig.add_trace(go.Scatter(
        x=monthly_df['reg_date'], 
        y=monthly_df['cumulative_members'],
        mode='lines',
        name='ข้อมูลสมาชิกปัจจุบัน',
        line=dict(color='#3b82f6', width=4, shape='spline'),
        fill='tozeroy', 
        fillcolor='rgba(59, 130, 246, 0.05)'
    ))
    
    # 3. เส้นพยากรณ์ (Forecast Line)
    fig.add_trace(go.Scatter(
        x=f_x, 
        y=f_y,
        mode='lines', 
        name='พยากรณ์การเติบโต 12 เดือน',
        line=dict(color='#8b5cf6', width=4, dash='dash', shape='spline')
    ))

    # เพิ่มจุดแยก (Vertical Line) ระหว่างปัจจุบันกับอนาคต
    fig.add_vline(x=last_date, line_width=1, line_dash="dot", line_color="gray")
    fig.add_annotation(x=last_date, y=last_val, text="จุดเริ่มพยากรณ์", 
                       showarrow=True, arrowhead=1, yshift=10)

    return chart_style(fig, "การคาดการณ์แนวโน้มจำนวนสมาชิกสะสม (Member Growth Forecast)")

# ==================================================
# 3. Main Layout
# ==================================================
def create_performance_layout():
    df = load_data()
    if df.empty:
        return dbc.Container(dbc.Alert("ไม่พบข้อมูลสำหรับการวิเคราะห์", color="danger", className="mt-5"))

    # ล้างข้อมูลรายได้
    if "income" in df.columns:
        df["Income_Clean"] = pd.to_numeric(df["income"].astype(str).str.replace(",", ""), errors="coerce").fillna(0)

    return dbc.Container(fluid=True, className="p-4", children=[
        # ส่วนหัว Dashboard
        html.Div([
            html.H2("Performance & Growth Analysis", className="fw-bold", 
                   style={"color": "#1e293b", "letterSpacing": "0.5px"}),
            html.P("วิเคราะห์ประสิทธิภาพย้อนหลังและพยากรณ์การเติบโตด้วยโมเดลสถิติ", className="text-muted")
        ], className="mb-4"),

        # ส่วน KPI Cards (นำเข้าจากไฟล์ kpi_cards.py)
        render_performance_kpis(df),

        # กราฟพยากรณ์ขนาดใหญ่
        dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        dcc.Graph(figure=chart_growth_forecast(df), config={'displayModeBar': False})
                    ]),
                    className="shadow-lg border-0 rounded-4 overflow-hidden"
                ), width=12
            ),
        ], className="mb-4"),
    ])

# ตัวแปร layout สำหรับเรียกใช้ในหน้าหลัก
layout = create_performance_layout()