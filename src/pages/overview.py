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
def chart_style(fig, title, height=380):
    fig.update_layout(
        title={
            'text': f"<b>{title}</b>",
            'font': {'size': 16, 'color': '#1e293b', 'family': 'Sarabun, sans-serif'},
            'x': 0.02,
            'xanchor': 'left'
        },
        plot_bgcolor="rgba(255, 255, 255, 0)",
        paper_bgcolor="rgba(255, 255, 255, 0)",
        height=height,
        font=dict(family="Sarabun, sans-serif", size=12, color='#475569'),
        margin=dict(t=60, b=40, l=50, r=30),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Sarabun, sans-serif"
        )
    )
    return fig

# ==================================================
# Charts
# ==================================================
def chart_gender_pie(df):
    counts = df["Gender_Group"].value_counts()
    colors = ['#6366f1', '#ec4899', '#94a3b8']
    
    fig = go.Figure(go.Pie(
        labels=counts.index, 
        values=counts.values, 
        hole=0.5,
        marker=dict(
            colors=colors,
            line=dict(color='#ffffff', width=3)
        ),
        textinfo='percent+label',
        textfont=dict(size=13, family='Sarabun', color='white'),
        insidetextorientation='radial',
        pull=[0.05, 0.05, 0.05]
    ))
    
    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>จำนวน: %{value}<br>สัดส่วน: %{percent}<extra></extra>'
    )
    
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(size=12),
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#e2e8f0',
            borderwidth=1
        )
    )
    return chart_style(fig, "สัดส่วนเพศ", 400)

def chart_branch_bar(df):
    branch_col = "branch_no" if "branch_no" in df.columns else "branch_code"
    counts = df[branch_col].value_counts().sort_index()
    
    fig = go.Figure(go.Bar(
        x=["สาขา " + str(x) for x in counts.index],
        y=counts.values,
        marker=dict(
            color=counts.values,
            colorscale='Viridis',
            line=dict(color='rgba(255, 255, 255, 0.8)', width=2),
            opacity=0.9,
            colorbar=dict(thickness=15, len=0.7)
        ),
        text=counts.values,
        textposition='outside',
        textfont=dict(size=12, color='#475569', family='Sarabun'),
        hovertemplate='<b>%{x}</b><br>สมาชิก: %{y}<extra></extra>'
    ))
    
    fig.update_xaxes(
        showgrid=False,
        showline=True,
        linewidth=1,
        linecolor='#e2e8f0',
        tickfont=dict(size=11)
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(226, 232, 240, 0.5)',
        showline=False
    )
    
    return chart_style(fig, "สมาชิกรายสาขา", 400)

def chart_province_bar(df):
    prov_col = "province_name" if "province_name" in df.columns else "province"
    counts = df[prov_col].value_counts().head(8).sort_values()
    
    fig = go.Figure(go.Bar(
        x=counts.values,
        y=counts.index,
        orientation='h',
        marker=dict(
            color=counts.values,
            colorscale='Blues',
            line=dict(color='rgba(255, 255, 255, 0.8)', width=2),
            opacity=0.9,
            colorbar=dict(thickness=15, len=0.7)
        ),
        text=counts.values,
        textposition='outside',
        textfont=dict(size=12, color='#475569', family='Sarabun'),
        hovertemplate='<b>%{y}</b><br>สมาชิก: %{x}<extra></extra>'
    ))
    
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(226, 232, 240, 0.5)',
        showline=False
    )
    fig.update_yaxes(
        showgrid=False,
        showline=True,
        linewidth=1,
        linecolor='#e2e8f0',
        tickfont=dict(size=11)
    )
    
    return chart_style(fig, "Top 8 จังหวัด", 400)

def chart_income_bar(df):
    career_col = "career_name" if "career_name" in df.columns else "career"
    income_avg = df.groupby(career_col)["Income_Clean"].mean().sort_values(ascending=False).head(8)
    
    fig = go.Figure(go.Bar(
        x=income_avg.index,
        y=income_avg.values,
        marker=dict(
            color=income_avg.values,
            colorscale='Sunset',
            line=dict(color='rgba(255, 255, 255, 0.8)', width=2),
            opacity=0.9,
            colorbar=dict(thickness=15, len=0.7, title='บาท')
        ),
        text=[f'฿{v:,.0f}' for v in income_avg.values],
        textposition='outside',
        textfont=dict(size=12, color='#475569', family='Sarabun'),
        hovertemplate='<b>%{x}</b><br>รายได้เฉลี่ย: ฿%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_xaxes(
        tickangle=-35,
        showgrid=False,
        showline=True,
        linewidth=1,
        linecolor='#e2e8f0',
        tickfont=dict(size=11)
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(226, 232, 240, 0.5)',
        showline=False
    )
    
    return chart_style(fig, "Top 8 รายได้ตามอาชีพ", 400)

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
            style={"padding": "20px"}
        ),
        className="shadow-sm rounded-4 border-0 mb-4",
        style={
            "backgroundColor": "rgba(255, 255, 255, 0.95)",
            "backdropFilter": "blur(10px)",
            "border": "1px solid rgba(226, 232, 240, 0.6) !important",
            "transition": "all 0.3s ease"
        }
    )

    return dbc.Container(
        fluid=True,
        style={
            "backgroundColor": "transparent",
            "padding": "20px 30px",
            "maxWidth": "1600px",
            "margin": "0 auto"
        },
        children=[
            html.Div([
                html.H3(
                    "ข้อมูลภาพรวม",
                    className="fw-bold mb-4",
                    style={
                        "color": "#1e293b",
                        "letterSpacing": "0.3px",
                        "fontSize": "28px",
                        "fontFamily": "Sarabun, sans-serif"
                    }
                ),
            ]),
            
            render_overview_kpis(df),

            dbc.Row([
                dbc.Col(card(chart_gender_pie(df)), xs=12, lg=6),
                dbc.Col(card(chart_branch_bar(df)), xs=12, lg=6)
            ], className="g-4 mb-2"),

            dbc.Row([
                dbc.Col(card(chart_province_bar(df)), xs=12, lg=6),
                dbc.Col(card(chart_income_bar(df)), xs=12, lg=6)
            ], className="g-4")
        ]
    )

layout = create_analysis_layout()