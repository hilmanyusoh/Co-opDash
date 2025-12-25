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
    
    df['registration_date'] = pd.to_datetime(df['registration_date'], errors='coerce')
    df['approval_date'] = pd.to_datetime(df['approval_date'], errors='coerce')
    df['Days_to_Approve'] = (df['approval_date'] - df['registration_date']).dt.days
    df.loc[df['Days_to_Approve'] < 0, 'Days_to_Approve'] = 0
    
    if "income" in df.columns:
        df["Income_Clean"] = pd.to_numeric(df["income"].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
    
    branch_map = {1: "สาขา 1", 2: "สาขา 2", 3: "สาขา 3", 4: "สาขา 4", 5: "สาขา 5"}
    if 'branch_no' in df.columns:
        df['branch_name'] = df['branch_no'].map(branch_map).fillna(df['branch_no'].astype(str).apply(lambda x: f"สาขา {x}"))
    
    return df

# ==================================================
# 2. Chart Helpers
# ==================================================
def apply_layout(fig, title, legend_pos="top"):
    """ ฟังก์ชันช่วยตั้งค่า Layout และ Legend ให้เป็นมาตรฐานเดียวกัน """
    fig.update_layout(
        title=f"<b>{title}</b>",
        font=dict(family="Sarabun, sans-serif"),
        plot_bgcolor="rgba(245, 247, 250, 0.4)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=50, r=50, t=100, b=50),
        hovermode="x unified"
    )
    
    if legend_pos == "top":
        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
    elif legend_pos == "right":
        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02)
        )
    
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='rgba(0,0,0,0.05)')
    return fig

# ==================================================
# 3. Visual Charts
# ==================================================

# 1. กราฟคอลัมน์แสดงจำนวนสมาชิก (Legend แยกสีรายสาขา)
def chart_member_column(df):
    counts = df['branch_name'].value_counts().sort_index().reset_index()
    counts.columns = ['branch_name', 'count']
    
    fig = px.bar(
        counts, x='branch_name', y='count', color='branch_name',
        text='count', color_discrete_sequence=px.colors.qualitative.Safe,
        labels={'branch_name': 'ชื่อสาขา', 'count': 'จำนวนสมาชิก'}
    )
    fig.update_traces(textposition='outside', texttemplate='<b>%{text}</b> คน')
    return apply_layout(fig, "1. จำนวนสมาชิกแต่ละสาขา", legend_pos="right")

# 2. กราฟเส้นรายได้เฉลี่ย 
def chart_income_line(df):
    avg_income = df.groupby('branch_name')['Income_Clean'].mean().sort_index().reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=avg_income['branch_name'], y=avg_income['Income_Clean'],
        mode='lines+markers', name='รายได้เฉลี่ย (บาท)',
        line=dict(color='#10b981', width=4, shape='spline'),
        marker=dict(size=10, color='white', line=dict(color='#10b981', width=3)),
        fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.1)'
    ))
    return apply_layout(fig, "2. รายได้เฉลี่ยต่อคนรายสาขา", legend_pos="top")

# 3. กราฟความเร็วการอนุมัติ (Legend ด้านบน)
def chart_approval_mode(df):
    def get_mode_val(x):
        m = x.mode()
        return m.iloc[0] if not m.empty else 0

    branch_modes = df.groupby('branch_name')['Days_to_Approve'].apply(get_mode_val).sort_values(ascending=False).reset_index()
    
    # สร้าง List สีตามเกณฑ์
    colors = ['#ef4444' if v > 5 else '#f59e0b' if v > 2 else '#22c55e' for v in branch_modes['Days_to_Approve']]
    
    fig = go.Figure()
    # ข้อมูลหลัก (Bar)
    fig.add_trace(go.Bar(
        x=branch_modes['Days_to_Approve'], y=branch_modes['branch_name'], orientation='h',
        marker=dict(color=colors, line=dict(color='white', width=1)),
        text=[f'<b>ส่วนใหญ่ {int(v)} วัน</b>' for v in branch_modes['Days_to_Approve']],
        textposition='auto', showlegend=False
    ))
    
    # เพิ่ม Legend เทียมเพื่ออธิบายความหมายของสี
    legend_labels = [("เร็ว (≤2 วัน)", "#22c55e"), ("ปกติ (3-5 วัน)", "#f59e0b"), ("ช้า (>5 วัน)", "#ef4444")]
    for label, color in legend_labels:
        fig.add_trace(go.Bar(x=[None], y=[None], name=label, marker_color=color))

    return apply_layout(fig, "3. ความเร็วการอนุมัติหลัก (Mode)", legend_pos="top")

# 4. กราฟ Scatter (Legend ด้านขวา)
def chart_member_income_scatter(df):
    summary = df.groupby('branch_name').agg({'member_id': 'count', 'Income_Clean': 'sum'}).reset_index()
    summary.columns = ['สาขา', 'จำนวนสมาชิก', 'รายได้รวม']
    
    fig = px.scatter(
        summary, x='จำนวนสมาชิก', y='รายได้รวม', color='สาขา',
        size='จำนวนสมาชิก', text='สาขา', size_max=40,
        color_discrete_sequence=px.colors.qualitative.Prism,
        labels={'รายได้รวม': 'รายได้รวม (บาท)', 'จำนวนสมาชิก': 'จำนวนสมาชิก (คน)'}
    )
    fig.update_traces(textposition='bottom center')
    return apply_layout(fig, "4. ความสัมพันธ์: จำนวนสมาชิก vs รายได้รวม", legend_pos="right")

# ==================================================
# 4. Main Layout
# ==================================================
def create_branch_layout():
    df = get_processed_data()
    if df.empty: return dbc.Container(dbc.Alert("ไม่พบข้อมูล", color="warning", className="mt-5"))

    render_card = lambda fig: dbc.Card(
        dbc.CardBody(dcc.Graph(figure=fig, config={'displayModeBar': False})), 
        className="shadow-lg rounded-4 border-0 mb-4 overflow-hidden"
    )

    return dbc.Container(
        fluid=True,
        className="p-4 bg-light",
        children=[
            html.Div([
                html.H2("ข้อมูลสาขา", className="fw-bold", style={"color": "#1e293b"}),
                html.P("สรุปประสิทธิภาพและการเติบโตแยกตามรายสาขา", className="text-muted")
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