from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from ..data_manager import load_data
from ..components.kpi_cards import render_overview_kpis

# ความสูงเท่ากันทุก dashboard
CHART_HEIGHT = 340

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
# Chart Helper - ความสูงเท่ากันทุกกราฟ
# ==================================================
def apply_layout(fig, title, height=CHART_HEIGHT):
    fig.update_layout(
        title={
            'text': f"<b>{title}</b>",
            'font': {'size': 16, 'color': '#0f172a', 'family': 'Sarabun, sans-serif'},
            'x': 0.02,
            'xanchor': 'left'
        },
        plot_bgcolor="rgba(255, 255, 255, 0.02)",
        paper_bgcolor="rgba(255, 255, 255, 0)",
        height=height,
        font=dict(family="Sarabun, sans-serif", size=11, color='#334155'),
        margin=dict(t=50, b=40, l=50, r=30),
        hoverlabel=dict(
            bgcolor="rgba(15, 23, 42, 0.95)",
            font_size=12,
            font_family="Sarabun, sans-serif",
            font_color="white",
            bordercolor="rgba(148, 163, 184, 0.3)"
        )
    )
    return fig

# ==================================================
# Charts
# ==================================================
def chart_gender_pie(df):
    counts = df["Gender_Group"].value_counts()
    colors = ['#be185d', '#3730a3', '#475569'] 
    
    fig = go.Figure(go.Pie(
        labels=counts.index, 
        values=counts.values, 
        hole=0.45,
        marker=dict(
            colors=colors,
            line=dict(color='#ffffff', width=2)
        ),
        pull=[0.05, 0.02, 0], 
        textinfo='percent+label',
        textfont=dict(size=13, family='Sarabun', color='white'),
        insidetextorientation='radial'
    ))
    
    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>จำนวน: %{value} คน<br>สัดส่วน: %{percent}<extra></extra>',
        textposition='inside',
        rotation=45
    )
    
    fig.update_layout(
        legend=dict(
            title="<b>เพศ</b>",
            orientation="h",
            xanchor="center",
            yanchor="top",
            x=0.5,
            y=-0.1,
            font=dict(size=11, family='Sarabun'),
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="rgba(148, 163, 184, 0.3)",
            borderwidth=1
        ),
        margin=dict(t=50, b=60, l=30, r=30)
    )
    
    return apply_layout(fig, "สัดส่วนสมาชิกแยกตามเพศ", CHART_HEIGHT)

def chart_branch_bar(df):
    branch_col = "branch_no" if "branch_no" in df.columns else "branch_code"
    counts = df[branch_col].value_counts().sort_index()
    
    gradient_colors = [
        ['#1e3a8a', '#3b82f6'],
        ['#b91c1c', '#ef4444'],
        ['#15803d', '#22c55e'],
        ['#b45309', '#f97316'],
        ['#6d28d9', '#a855f7'],
        ['#0369a1', '#0ea5e9'],
        ['#be185d', '#ec4899'],
        ['#475569', '#64748b']
    ]
    
    fig = go.Figure()

    for i, (branch, value) in enumerate(counts.items()):
        branch_label = f"สาขา {branch}"
        color_idx = i % len(gradient_colors)
        
        fig.add_trace(go.Bar(
            x=[branch_label],
            y=[value],
            name=branch_label,  
            text=[f'<b>{value}</b>'],
            textposition='outside',
            textfont=dict(size=11, color='#0f172a', family='Sarabun'),
            hovertemplate=f'<b>{branch_label}</b><br>สมาชิก: %{{y}} คน<extra></extra>',
            marker=dict(
                color=gradient_colors[color_idx][0],
                line=dict(color='#ffffff', width=2),
                opacity=0.9
            )
        ))

    fig.update_layout(
        showlegend=True,
        legend=dict(
            title="<b>รายชื่อสาขา</b>",
            orientation="h",
            xanchor="center",
            yanchor="top",
            x=0.5,
            y=-0.15,
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="rgba(148, 163, 184, 0.3)",
            borderwidth=1,
            font=dict(size=10, family='Sarabun')
        ),
        margin=dict(l=50, r=30, t=50, b=75),
        barmode='group',
        paper_bgcolor='rgba(255, 255, 255, 0)',
        plot_bgcolor='rgba(248, 250, 252, 0.3)'
    )

    fig.update_xaxes(
        title="",
        showgrid=False,
        showline=True,
        linewidth=2,
        linecolor='#cbd5e1', 
        tickfont=dict(size=11, color='#334155', family='Sarabun')
    )
    
    fig.update_yaxes(
        title="<b>จำนวน</b>",
        showgrid=True,
        gridwidth=1.5,
        gridcolor='rgba(203, 213, 225, 0.4)',
        showline=False,
        zeroline=True,
        zerolinecolor='#cbd5e1',
        zerolinewidth=2,
        tickfont=dict(size=11, color='#334155')
    )
    
    return apply_layout(fig, "จำนวนสมาชิกแยกรายสาขา", CHART_HEIGHT)

def chart_province_bar(df):
    prov_col = "province_name" if "province_name" in df.columns else "province"
    counts = df[prov_col].value_counts().head(8).sort_values()
    
    gradient_colors = [
        ['#1e3a8a', '#3b82f6'],
        ['#b91c1c', '#ef4444'],
        ['#15803d', '#22c55e'],
        ['#b45309', '#f97316'],
        ['#6d28d9', '#a855f7'],
        ['#0369a1', '#0ea5e9'],
        ['#be185d', '#ec4899'],
        ['#475569', '#64748b']
    ]
    
    fig = go.Figure()

    for i, (province, value) in enumerate(counts.items()):
        color_idx = i % len(gradient_colors)
        
        fig.add_trace(go.Bar(
            y=[province],
            x=[value],
            name=province,       
            orientation='h',
            text=[f'<b>{value}</b>'],
            textposition='outside',
            marker=dict(
                color=gradient_colors[color_idx][0],
                line=dict(color='#ffffff', width=2),
                opacity=0.9
            ),
            hovertemplate=f'<b>{province}</b><br>สมาชิก: %{{x}} คน<extra></extra>'
        ))
    
    fig.update_layout(
        showlegend=True,
        legend=dict(
            title="<b>จังหวัด</b>",
            orientation="h",
            xanchor="center",
            yanchor="top",
            x=0.5,
            y=-0.2,
            font=dict(size=10, family='Sarabun'),
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="rgba(148, 163, 184, 0.3)",
            borderwidth=1
        ),
        margin=dict(r=30, l=100, t=50, b=85),
        barmode='group',
        paper_bgcolor='rgba(255, 255, 255, 0)',
        plot_bgcolor='rgba(248, 250, 252, 0.3)'
    )
    
    fig.update_xaxes(
        title="<b>จำนวนสมาชิก</b>",
        showgrid=True,
        gridwidth=1.5,
        gridcolor='rgba(203, 213, 225, 0.4)',
        showline=False,
        tickfont=dict(size=11, color='#334155')
    )
    
    fig.update_yaxes(
        title="<b>จังหวัด</b>",
        showgrid=False,
        showline=True,
        linewidth=1,
        linecolor='#cbd5e1', 
        tickfont=dict(size=11, color='#0f172a', family='Sarabun')
    )
    
    return apply_layout(fig, "Top 8 จังหวัดที่มีสมาชิกสูงสุด", CHART_HEIGHT)

def chart_income_funnel(df):
    career_col = "career_name" if "career_name" in df.columns else "career"
    income_avg = df.groupby(career_col)["Income_Clean"].mean().sort_values(ascending=True).head(8).reset_index()
    
    fig = px.funnel(
        income_avg, 
        y=career_col, 
        x='Income_Clean',
        color=career_col,
        color_discrete_sequence=px.colors.qualitative.Prism,
        labels={'Income_Clean': 'รายได้เฉลี่ย', career_col: 'อาชีพ'}
    )

    fig.update_traces(
        textinfo="value",
        texttemplate="฿%{value:,.0f}",
        marker=dict(line=dict(color='white', width=1.5)),
        opacity=0.9,
        textfont=dict(size=11)
    )

    fig.update_layout(
        margin=dict(r=30, t=50, b=40, l=120),
        showlegend=False
    )

    return apply_layout(fig, "Top 8 อันดับรายได้เฉลี่ยตามอาชีพ", CHART_HEIGHT)

# ==================================================
# Layout
# ==================================================
def create_analysis_layout():
    df = load_data()
    df = preprocess_data(df)

    if df.empty:
        return dbc.Container(dbc.Alert("ไม่พบข้อมูล", color="warning", className="mt-5"))

    card = lambda fig: dbc.Card(
        dbc.CardBody(
            dcc.Graph(
                figure=fig,
                config={'displayModeBar': False, 'responsive': True}
            ),
            style={"padding": "18px"}
        ),
        className="shadow-sm rounded-3 border-0 mb-3",
        style={
            "backgroundColor": "rgba(255, 255, 255, 0.98)",
            "backdropFilter": "blur(10px)",
            "border": "1px solid rgba(203, 213, 225, 0.5) !important",
            "transition": "all 0.3s ease",
            "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.08)",
        }
    )

    return dbc.Container(
        fluid=True,
        style={
            "backgroundColor": "transparent",
            "padding": "20px 30px",
            "maxWidth": "1400px",
            "margin": "0 auto"
        },
        children=[
            html.Div([
                html.H3(
                    "ข้อมูลภาพรวม",
                    className="fw-bold mb-3",
                    style={
                        "color": "#0f172a",
                        "letterSpacing": "0.5px",
                        "fontSize": "26px",
                        "fontFamily": "Sarabun, sans-serif",
                        "textShadow": "0 2px 4px rgba(0,0,0,0.05)",
                        "position": "relative",
                        "paddingBottom": "10px"
                    }
                ),
            ]),
            
            render_overview_kpis(df),

            dbc.Row([
                dbc.Col(card(chart_gender_pie(df)), xs=12, lg=6),
                dbc.Col(card(chart_branch_bar(df)), xs=12, lg=6)
            ], className="g-3 mb-3"),

            dbc.Row([
                dbc.Col(card(chart_province_bar(df)), xs=12, lg=6),
                dbc.Col(card(chart_income_funnel(df)), xs=12, lg=6)
            ], className="g-3")
        ]
    )

layout = create_analysis_layout()