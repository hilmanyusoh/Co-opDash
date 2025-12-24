from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from ..data_manager import load_data
from ..components.kpi_cards import render_branch_kpis

# ==================================================
# 1. Data Processing
# ==================================================
def get_processed_data():
    df = load_data()
    if df.empty: return df
    
    # จัดการวันที่และคำนวณวันอนุมัติ
    df['registration_date'] = pd.to_datetime(df['registration_date'], errors='coerce')
    df['approval_date'] = pd.to_datetime(df['approval_date'], errors='coerce')
    df['Days_to_Approve'] = (df['approval_date'] - df['registration_date']).dt.days
    df.loc[df['Days_to_Approve'] < 0, 'Days_to_Approve'] = 0
    
    # จัดการรายได้
    if "income" in df.columns:
        df["Income_Clean"] = pd.to_numeric(df["income"].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
    
    # Mapping ชื่อสาขา 1-5
    branch_map = {1: "สาขา 1", 2: "สาขา 2", 3: "สาขา 3", 4: "สาขา 4", 5: "สาขา 5"}
    if 'branch_no' in df.columns:
        df['branch_name'] = df['branch_no'].map(branch_map).fillna(df['branch_no'].astype(str).apply(lambda x: f"สาขา {x}"))
    
    return df

# ==================================================
# 2. Chart Helpers
# ==================================================
def chart_style(fig, title, height=400):
    fig.update_layout(
        title=f"<b>{title}</b>",
        plot_bgcolor="rgba(245, 247, 250, 0.4)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=height,
        font=dict(family="Sarabun, sans-serif"),
        margin=dict(l=40, r=40, t=80, b=40)
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='rgba(0,0,0,0.05)')
    return fig

# ==================================================
# 3. Visual Charts
# ==================================================

# 1. กราฟคอลัมน์แสดงจำนวนสมาชิก
def chart_member_column(df):
    counts = df['branch_name'].value_counts().sort_index()
    fig = go.Figure(go.Bar(
        x=counts.index, y=counts.values,
        marker=dict(color='#3b82f6', line=dict(color='white', width=2)),
        text=counts.values, textposition='outside',
        texttemplate='<b>%{text}</b> คน'
    ))
    return chart_style(fig, "1. จำนวนสมาชิกแต่ละสาขา")

# 2. กราฟเส้นแสดงรายได้เฉลี่ยต่อคน
def chart_income_line(df):
    avg_income = df.groupby('branch_name')['Income_Clean'].mean().sort_index()
    fig = go.Figure(go.Scatter(
        x=avg_income.index, y=avg_income.values,
        mode='lines+markers+text',
        line=dict(color='#10b981', width=4),
        marker=dict(size=10, color='white', line=dict(color='#10b981', width=3)),
        text=[f'฿{v/1000:.1f}k' for v in avg_income.values],
        textposition='top center',
        fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.1)'
    ))
    return chart_style(fig, "2. รายได้เฉลี่ยต่อคนรายสาขา")

# 3. กราฟความเร็วการอนุมัติ (Mode) พร้อม Legend สี
def chart_approval_mode(df):
    def get_mode_val(x):
        m = x.mode()
        return m.iloc[0] if not m.empty else 0

    branch_modes = df.groupby('branch_name')['Days_to_Approve'].apply(get_mode_val).sort_values(ascending=False)
    colors = ['#ef4444' if v > 5 else '#f59e0b' if v > 2 else '#22c55e' for v in branch_modes.values]
    
    fig = go.Figure()
    # ข้อมูลหลัก
    fig.add_trace(go.Bar(
        x=branch_modes.values, y=branch_modes.index, orientation='h',
        marker=dict(color=colors, line=dict(color='white', width=1)),
        text=[f'<b>ส่วนใหญ่ {int(v)} วัน</b>' for v in branch_modes.values],
        textposition='auto', showlegend=False
    ))
    # ส่วนของ Legend
    legend_labels = [("เร็ว (≤2 วัน)", "#22c55e"), ("ปกติ (3-5 วัน)", "#f59e0b"), ("ช้า (>5 วัน)", "#ef4444")]
    for label, color in legend_labels:
        fig.add_trace(go.Bar(x=[None], y=[None], name=label, marker_color=color))

    fig.add_vline(x=2, line_dash="dot", line_color="#22c55e", opacity=0.7)
    fig.add_vline(x=5, line_dash="dot", line_color="#ef4444", opacity=0.7)
    
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return chart_style(fig, "3. ความเร็วการอนุมัติหลัก (Mode)")

# 4. กราฟ Scatter แสดงความสัมพันธ์สมาชิกกับรายได้
def chart_member_income_scatter(df):
    summary = df.groupby('branch_name').agg({'member_id': 'count', 'Income_Clean': 'sum'}).reset_index()
    fig = go.Figure(go.Scatter(
        x=summary['member_id'], y=summary['Income_Clean'],
        mode='markers+text',
        marker=dict(size=summary['member_id']*0.8, color=summary['Income_Clean'], colorscale='Viridis', line=dict(color='white', width=2)),
        text=summary['branch_name'], textposition='bottom center'
    ))
    fig.update_xaxes(title="จำนวนสมาชิก (คน)")
    fig.update_yaxes(title="รายได้รวม (บาท)")
    return chart_style(fig, "4. ความสัมพันธ์: จำนวนสมาชิก vs รายได้รวม")

# ==================================================
# 4. Main Layout
# ==================================================
def create_branch_layout():
    df = get_processed_data()
    if df.empty: return dbc.Container(dbc.Alert("ไม่พบข้อมูล", color="warning", className="mt-5"))

    render_card = lambda fig: dbc.Card(
        dbc.CardBody(dcc.Graph(figure=fig, config={'displayModeBar': False})), 
        className="shadow-sm rounded-4 border-0 mb-4 overflow-hidden"
    )

    return dbc.Container(
        fluid=True,
        className="p-4 bg-light",
        children=[
            html.Div([
                html.H2("Branch ", className="fw-bold", style={"color": "#1e293b"}),
            ], className="mb-4"),

            render_branch_kpis(df),

            dbc.Row([
                dbc.Col(render_card(chart_member_column(df)), lg=6),
                dbc.Col(render_card(chart_income_line(df)), lg=6)
            ], className="g-4"),

            dbc.Row([
                dbc.Col(render_card(chart_approval_mode(df)), lg=6),
                dbc.Col(render_card(chart_member_income_scatter(df)), lg=6)
            ], className="g-4"),
        ]
    )

layout = create_branch_layout()