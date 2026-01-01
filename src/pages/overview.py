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
def apply_layout(fig, title, height=380):
    fig.update_layout(
        title={
            'text': f"<b>{title}</b>",
            'font': {'size': 18, 'color': '#0f172a', 'family': 'Sarabun, sans-serif'},
            'x': 0.02,
            'xanchor': 'left'
        },
        plot_bgcolor="rgba(255, 255, 255, 0.02)",
        paper_bgcolor="rgba(255, 255, 255, 0)",
        height=height,
        font=dict(family="Sarabun, sans-serif", size=12, color='#334155'),
        margin=dict(t=70, b=50, l=60, r=40),
        hoverlabel=dict(
            bgcolor="rgba(15, 23, 42, 0.95)",
            font_size=13,
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
        hole=0.5, 
        marker=dict(
            colors=colors,
            line=dict(color='#ffffff', width=3)
        ),
        pull=[0.08, 0.03, 0], 
        textinfo='percent+label',
        textfont=dict(size=15, family='Sarabun', color='white'),
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
            orientation="v",
            xanchor="left",
            yanchor="top",
            x=1.02,
            y=1,
            font=dict(size=13, family='Sarabun'),
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="rgba(148, 163, 184, 0.3)",
            borderwidth=1
        ),
    )
    
    
    return apply_layout(fig, "สัดส่วนสมาชิกแยกตามเพศ", 420)

def chart_branch_bar(df):
    branch_col = "branch_no" if "branch_no" in df.columns else "branch_code"
    counts = df[branch_col].value_counts().sort_index()
    
    # Gradient colors สำหรับแต่ละสาขา
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
            textfont=dict(size=13, color='#0f172a', family='Sarabun'),
            hovertemplate=f'<b>{branch_label}</b><br>สมาชิก: %{{y}} คน<extra></extra>',
            marker=dict(
                color=gradient_colors[color_idx][0],
                line=dict(color='#ffffff', width=2.5),
                opacity=0.9,
                pattern=dict(shape="")
            )
        ))

    fig.update_layout(
        showlegend=True,
        legend=dict(
            title="<b>รายชื่อสาขา</b>",
            orientation="v",
            y=0.5,
            x=1.1,
            xanchor="left",
            yanchor="middle",
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="rgba(148, 163, 184, 0.3)",
            borderwidth=1,
            font=dict(size=12, family='Sarabun')
        ),
        margin=dict(l=220, r=40, t=60, b=60),    
        barmode='group',
        paper_bgcolor='rgba(255, 255, 255, 0)',
        plot_bgcolor='rgba(248, 250, 252, 0.3)'
    )

    fig.update_xaxes(
        title="<b>สาขา</b>",
        showgrid=False,
        showline=True,
        linewidth=2.5,
        linecolor='#cbd5e1', 
        tickfont=dict(size=12, color='#334155', family='Sarabun')
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
        tickfont=dict(size=12, color='#334155')
    )
    
    return apply_layout(fig, "จำนวนสมาชิกแยกรายสาขา", 420)

def chart_province_bar(df):
    prov_col = "province_name" if "province_name" in df.columns else "province"
    counts = df[prov_col].value_counts().head(8).sort_values()
    
    # Gradient colors
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
                line=dict(color='#ffffff', width=2.5),
                opacity=0.9
            ),
            hovertemplate=f'<b>{province}</b><br>สมาชิก: %{{x}} คน<extra></extra>'
        ))
    

    fig.update_layout(
        showlegend=True,
        legend=dict(
            title="<b>จังหวัด</b>",
            orientation="v",
            xanchor="left",
            yanchor="top",
            x=1.0,
            y=1,
            font=dict(size=12, family='Sarabun'),
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="rgba(148, 163, 184, 0.3)",
            borderwidth=1
        ),
        margin=dict(r=180, l=140, t=60, b=60),
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
        tickfont=dict(size=12, color='#334155')
    )
    
    fig.update_yaxes(
        title="<b>จังหวัด</b>",
        showgrid=False,
        showline=True,
        linewidth=0.5,
        linecolor='#cbd5e1', 
        tickfont=dict(size=12, color='#0f172a', family='Sarabun')
    )
    
    return apply_layout(fig, "Top 8 จังหวัดที่มีสมาชิกสูงสุด", 420)

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
        marker=dict(line=dict(color='white', width=2)),
        opacity=0.9
    )

    fig.update_layout(
        margin=dict(r=50, t=80, b=50, l=150), # ขยับ l เพื่อให้ชื่ออาชีพไม่โดนตัด
        showlegend=False # ใน Funnel ชื่อจะอยู่ที่แกน Y อยู่แล้ว
    )

    return apply_layout(fig, "Top 8 อันดับรายได้เฉลี่ยตามอาชีพ", 420)

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
            style={"padding": "24px"}
        ),
        className="shadow-lg rounded-4 border-0 mb-4",
        style={
            "backgroundColor": "rgba(255, 255, 255, 0.98)",
            "backdropFilter": "blur(12px)",
            "border": "1px solid rgba(203, 213, 225, 0.5) !important",
            "transition": "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
            "boxShadow": "0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)",
            "transform": "translateZ(0)",
            "willChange": "transform"
        }
    )

    return dbc.Container(
        fluid=True,
        style={
            "backgroundColor": "transparent",
            "padding": "24px 36px",
            "maxWidth": "1600px",
            "margin": "0 auto"
        },
        children=[
            html.Div([
                html.H3(
                    "ข้อมูลภาพรวม",
                    className="fw-bold mb-4",
                    style={
                        "color": "#0f172a",
                        "letterSpacing": "0.5px",
                        "fontSize": "32px",
                        "fontFamily": "Sarabun, sans-serif",
                        "textShadow": "0 2px 4px rgba(0,0,0,0.05)",
                        "position": "relative",
                        "paddingBottom": "12px"
                    }
                ),
            ]),
            
            render_overview_kpis(df),

            dbc.Row([
                dbc.Col(card(chart_gender_pie(df)), xs=12, lg=6),
                dbc.Col(card(chart_branch_bar(df)), xs=12, lg=6)
            ], className="g-4 mb-3"),

            dbc.Row([
                dbc.Col(card(chart_province_bar(df)), xs=12, lg=6),
                dbc.Col(card(chart_income_funnel(df)), xs=12, lg=6)
            ], className="g-4")
        ]
    )

layout = create_analysis_layout()