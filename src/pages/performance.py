import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from functools import lru_cache

from ..data_manager import load_data
from ..components.chart_card import chart_card
from ..components.theme import THEME
from ..components.kpi_cards import render_performance_kpis

# ==================================================
# Config
# ==================================================
CHART_HEIGHT = 450
FORECAST_HORIZON = 12   
CONF_INTERVAL = 0.10    

# ==================================================
# 1. Data Preprocessing & Cache
# ==================================================
def preprocess_performance(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    if "income" in df.columns:
        df["Income_Clean"] = (
            df["income"].astype(str).str.replace(",", "")
            .pipe(pd.to_numeric, errors="coerce").fillna(0)
        )
    if "registration_date" in df.columns:
        df["reg_date"] = pd.to_datetime(df["registration_date"], errors="coerce")
    return df

@lru_cache(maxsize=1)
def load_performance_data():
    return preprocess_performance(load_data())

# ==================================================
# 2. Chart Logic
# ==================================================
def chart_business_forecast(df, selected_year):
    if df.empty or "reg_date" not in df.columns: return go.Figure()

    dff = df.dropna(subset=["reg_date"]).copy()
    dff["month"] = dff["reg_date"].dt.to_period("M").dt.to_timestamp()

    monthly = dff.groupby("month")["Income_Clean"].sum().reset_index().sort_values("month")
    monthly["cumulative"] = monthly["Income_Clean"].cumsum()

    last_date = monthly["month"].iloc[-1]
    last_val = monthly["cumulative"].iloc[-1]

    recent_vals = monthly["Income_Clean"].tail(6).tolist()
    weights = list(range(1, len(recent_vals) + 1))
    avg_growth = np.average(recent_vals, weights=weights) if recent_vals else 0

    future_dates = pd.date_range(start=last_date, periods=FORECAST_HORIZON + 1, freq="MS")[1:]
    forecast_vals = [last_val + (avg_growth * i) for i in range(1, FORECAST_HORIZON + 1)]

    f_x, f_y = [last_date] + list(future_dates), [last_val] + forecast_vals
    upper = [v * (1 + CONF_INTERVAL * i/FORECAST_HORIZON) for i, v in enumerate(f_y)]
    lower = [v * (1 - CONF_INTERVAL * i/FORECAST_HORIZON) for i, v in enumerate(f_y)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=f_x + f_x[::-1], y=upper + lower[::-1], fill="toself", 
                             fillcolor="rgba(16,185,129,0.10)", line=dict(color="rgba(0,0,0,0)"), name="ช่วงคาดการณ์เป้าหมาย"))
    fig.add_trace(go.Scatter(x=monthly["month"], y=monthly["cumulative"], mode="lines+markers", 
                             name="มูลค่าสะสมจริง", line=dict(color=THEME["success"], width=4)))
    fig.add_trace(go.Scatter(x=f_x, y=f_y, mode="lines", name="แนวโน้ม 12 เดือนข้างหน้า", 
                             line=dict(color=THEME["success"], dash="dash", width=3)))
    
    fig.add_vline(x=last_date, line_dash="dot", line_color="#94a3b8")
    fig.update_layout(height=CHART_HEIGHT, paper_bgcolor=THEME["paper"], plot_bgcolor=THEME["bg_plot"],
                      font=dict(family="Sarabun, sans-serif", color=THEME["text"]), hovermode="x unified",
                      legend=dict(orientation="h", x=0.5, xanchor="center", y=1.1), margin=dict(t=80, b=40, l=60, r=40))
    fig.update_yaxes(gridcolor=THEME["grid"], tickformat=",.0f")
    return fig

# ==================================================
# 3. Main Layout
# ==================================================
def performance_layout():
    df = load_performance_data()
    if df.empty: return dbc.Container(dbc.Alert("ไม่พบข้อมูล", color="danger"))
    
    available_years = sorted(df['reg_date'].dt.year.unique(), reverse=True)

    return dbc.Container(fluid=True, style={"padding": "20px 30px", "maxWidth": "1400px"}, children=[
        html.Div([
            html.H3("การคาดการณ์แนวโน้มองค์กร", className="fw-bold mb-0"),
            html.P("วิเคราะห์เป้าหมายธุรกิจจากฐานข้อมูลรายปี", className="text-muted")
        ], className="mb-4"),

        # ใช้ dcc.Loading คลุมเพื่อความลื่นไหลเวลาเปลี่ยนปี
        dcc.Loading(id="loading-performance", type="circle", color=THEME["success"], children=[
            html.Div(id='performance-content')
        ]),
        
        # Dropdown ตัวแรกที่เป็นตัวจุดชนวน (Trigger) - ซ่อนไว้เพื่อรักษา State หรือใช้ร่วมกัน
        dcc.Dropdown(id='year-selector', options=[{'label': f'ปี {y}', 'value': y} for y in available_years],
                     value=available_years[0], style={'display': 'none'})
    ])

# ==================================================
# 4. Callback
# ==================================================
@callback(
    Output('performance-content', 'children'),
    Input('year-selector', 'value')
)
def update_performance_dashboard(selected_year):
    df = load_performance_data()
    filtered_df = df[df['reg_date'].dt.year >= selected_year]
    available_years = sorted(df['reg_date'].dt.year.unique(), reverse=True)

    return [
        render_performance_kpis(filtered_df), 
        
        dbc.Row([
            dbc.Col(
                html.Div([
                    # --- ปุ่มเลือกปีแบบลอยตัว (ตำแหน่งที่คุณวงไว้) ---
                    html.Div([
                        html.Span("เลือกปีวิเคราะห์ย้อนหลัง:", className="me-2 small fw-bold", style={"color": "#666"}),
                        dcc.Dropdown(
                            id='year-selector', # ใช้ ID เดิมเพื่อให้ Callback วนลูปทำงานได้
                            options=[{'label': str(y), 'value': y} for y in available_years],
                            value=selected_year,
                            clearable=False,
                            style={'width': '110px', 'fontSize': '14px'}
                        )
                    ], style={
                        "position": "absolute", "top": "20px", "right": "20px",
                        "zIndex": "1000", "display": "flex", "alignItems": "center"
                    }),

                    # ตัวกราฟ
                    chart_card(
                        chart_business_forecast(filtered_df, selected_year),
                        f"คาดการณ์แนวโน้มธุรกิจ (อ้างอิงฐานข้อมูลปี {selected_year})"
                    )
                ], style={"position": "relative"}), # ฐานสำหรับตำแหน่ง Absolute
                width=12
            )
        ]),
        html.Div([html.Small(f"* วิเคราะห์จากสถิติปี {selected_year}", className="text-muted")], className="text-end mt-2")
    ]

layout = performance_layout()