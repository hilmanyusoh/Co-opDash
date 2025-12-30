from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from ..data_manager import load_data
from ..components.kpi_cards import render_member_kpis

# ==================================================
# Data Processing
# ==================================================
def process_member(df):
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
def legend_style(fig, title, height=420):
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

def add_depth(fig):
    fig.update_traces(
        marker_line_color='rgba(255, 255, 255, 0.8)', 
        marker_line_width=2.5, 
        opacity=0.9
    )
    return fig

# ==================================================
# Charts
# ==================================================

def chart_growth_time(df):
    if "reg_date" not in df.columns: return go.Figure()
    
    trend = df.groupby(df["reg_date"].dt.to_period("M")).size().reset_index(name="count")
    trend["reg_date"] = trend["reg_date"].dt.to_timestamp()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend["reg_date"], 
        y=trend["count"],
        mode='lines',
        name='จำนวนสมาชิกใหม่',
        line=dict(color='#3b82f6', width=4, shape='spline'),
        fill='tozeroy', 
        fillcolor='rgba(59, 130, 246, 0.15)',
        hovertemplate='<b>%{x|%B %Y}</b><br>สมาชิกใหม่: %{y} คน<extra></extra>'
    ))

    fig.update_layout(
        title={
            'text': "<b>1. แนวโน้มการเพิ่มขึ้นของสมาชิกรายเดือน</b>",
            'font': {'size': 18, 'color': '#0f172a', 'family': 'Sarabun, sans-serif'},
            'x': 0.02,
            'xanchor': 'left'
        },
        hovermode="x unified",
        xaxis=dict(
            title="<b>เดือน-ปี</b>",
            showgrid=False, 
            tickformat="%b %Y",
            showline=True,
            linewidth=2.5,
            linecolor='#cbd5e1',
            tickfont=dict(size=12, color='#334155')
        ),
        yaxis=dict(
            title="<b>จำนวนสมาชิก</b>",
            range=[0, 10], 
            gridcolor='rgba(203, 213, 225, 0.4)',
            gridwidth=1.5,
            dtick=2,
            showline=False,
            zeroline=True,
            zerolinecolor='#cbd5e1',
            zerolinewidth=2,
            tickfont=dict(size=12, color='#334155')
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="right",
            x=1,
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="rgba(148, 163, 184, 0.3)",
            borderwidth=1,
            font=dict(size=12, family='Sarabun')
        ),
        margin=dict(t=100, b=60, l=60, r=50),
        plot_bgcolor="rgba(248, 250, 252, 0.3)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=420,
        hoverlabel=dict(
            bgcolor="rgba(15, 23, 42, 0.95)",
            font_size=13,
            font_family="Sarabun, sans-serif",
            font_color="white"
        )
    )
    return fig

def chart_gender_career(df):
    career_col = "career_name" if "career_name" in df.columns else "career"
    # ดึง Top 10 อาชีพ
    top = df[career_col].value_counts().head(10).index
    data = df[df[career_col].isin(top)]
    
    # ปรับสีให้เข้มขึ้น (ชาย: Deep Navy, หญิง: Deep Pink, อื่นๆ: Slate)
    fig = px.histogram(
        data, 
        y=career_col, 
        color="Gender", 
        barmode="group", 
        orientation="h",
        color_discrete_map={
            "ชาย": "#1e3a8a", 
            "หญิง": "#be185d", 
            "อื่นๆ": "#475569"
        },
        category_orders={career_col: top.tolist()},
        text_auto=True # แสดงตัวเลขจำนวนคนอัตโนมัติที่แท่งกราฟ
    )
    
    # เพิ่มมิตินูนด้วยขอบสีขาวหนา
    fig.update_traces(
        marker_line_color='#ffffff', 
        marker_line_width=2, 
        opacity=0.95,
        textposition='outside' # วางตัวเลขไว้ข้างนอกแท่งกราฟ
    )
    
    # ปรับแต่งแกนให้คมชัด
    fig.update_xaxes(
        title="<b>จำนวนสมาชิก (คน)</b>",
        showgrid=True,
        gridwidth=1,
        gridcolor='#e2e8f0',
        showline=False,
        tickfont=dict(size=12, color='#334155')
    )
    
    fig.update_yaxes(
        title="<b>กลุ่มอาชีพ</b>",
        showgrid=False,
        showline=True,
        linewidth=2.5,
        linecolor='#94a3b8', # เส้นแกนแนวตั้งสีเข้ม
        tickfont=dict(size=12, color='#0f172a')
    )
    
    # เรียกใช้ Style หลักที่คุม Legend ขวาและ Title
    return legend_style(fig, "2. สัดส่วนเพศแยกตามกลุ่มอาชีพ (Top 10)")

def chart_income_pie(df):
    if "Income_Level" not in df.columns: return go.Figure()
    counts = df["Income_Level"].value_counts().reindex(["< 15K", "15K - 30K", "30K - 50K", "50K - 100K", "100K+"])
    
    colors = ["#cbd5e1", "#94a3b8", "#64748b", "#475569", "#1e293b"]
    
    fig = go.Figure(go.Pie(
        labels=counts.index, 
        values=counts.values,
        marker=dict(
            colors=colors,
            line=dict(color='#ffffff', width=3)
        ),
        textinfo='percent+label',
        textfont=dict(size=15, family='Sarabun', color='white'),
        hole=0.5,
        pull=[0.05, 0.03, 0, 0, 0],
        hovertemplate='<b>%{label}</b><br>จำนวน: %{value} คน<br>สัดส่วน: %{percent}<extra></extra>'
    ))
    
    # เพิ่ม annotation ตรงกลาง
    total = counts.sum()
    fig.add_annotation(
        text=f'<b>ทั้งหมด</b><br>{total:,}<br><span style="font-size:12px">คน</span>',
        x=0.5, y=0.5,
        font=dict(size=16, color='#0f172a', family='Sarabun'),
        showarrow=False,
        xref="paper", yref="paper"
    )
    
    return legend_style(fig, "3. สัดส่วนสมาชิกแยกตามระดับรายได้")

def chart_gen_area(df):
    prov_col = "province_name" if "province_name" in df.columns else "province"
    top = df[prov_col].value_counts().head(8).index
    data = df[df[prov_col].isin(top)].groupby([prov_col, "Gen"]).size().reset_index(name="count")
    
    fig = px.bar(
        data, x=prov_col, y="count", color="Gen", barmode="stack",
        color_discrete_sequence=['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b']
    )
    
    fig.update_traces(
        marker_line_color='rgba(255, 255, 255, 0.8)', 
        marker_line_width=2.5, 
        opacity=0.9
    )
    
    fig.update_xaxes(
        title="<b>จังหวัด</b>",
        showgrid=False,
        showline=True,
        linewidth=2.5,
        linecolor='#cbd5e1',
        tickfont=dict(size=12, color='#0f172a'),
        tickangle=-35
    )
    
    fig.update_yaxes(
        title="<b>จำนวนสมาชิก</b>",
        showgrid=True,
        gridwidth=1.5,
        gridcolor='rgba(203, 213, 225, 0.4)',
        showline=False,
        zeroline=True,
        zerolinecolor='#cbd5e1',
        zerolinewidth=2,
        tickfont=dict(size=12, color='#334155')
    )
    
    return legend_style(fig, "4. การกระจายกลุ่ม Generation ในจังหวัดหลัก", 450)

def chart_income_career(df):
    career_col = "career_name" if "career_name" in df.columns else "career"
    avg = df[df["Income_Clean"] > 0].groupby(career_col)["Income_Clean"].mean().sort_values(ascending=False).head(10).reset_index()
    avg.columns = [career_col, "รายได้เฉลี่ย"]

    # สร้างสีไล่ระดับจากสูงไปต่ำ
    gradient_colors = ['#1e3a8a', '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', 
                      '#bfdbfe', '#dbeafe', '#eff6ff', '#f1f5f9', '#f8fafc']
    
    fig = go.Figure()
    
    for i, row in avg.iterrows():
        fig.add_trace(go.Bar(
            x=[row["รายได้เฉลี่ย"]],
            y=[row[career_col]],
            orientation='h',
            name=row[career_col],
            text=[f'<b>฿{row["รายได้เฉลี่ย"]:,.0f}</b>'],
            textposition='outside',
            marker=dict(
                color=gradient_colors[i % len(gradient_colors)],
                line=dict(color='#ffffff', width=2.5),
                opacity=0.9
            ),
            hovertemplate=f'<b>{row[career_col]}</b><br>รายได้เฉลี่ย: ฿{row["รายได้เฉลี่ย"]:,.2f}<extra></extra>'
        ))
    
    fig.update_xaxes(
        title="<b>รายได้เฉลี่ย (บาท)</b>",
        showgrid=True,
        gridwidth=1.5,
        gridcolor='rgba(203, 213, 225, 0.4)',
        showline=False,
        tickformat=',.0f',
        tickfont=dict(size=12, color='#334155')
    )
    
    fig.update_yaxes(
        title="<b>อาชีพ</b>",
        showgrid=False,
        showline=True,
        linewidth=2.5,
        linecolor='#cbd5e1',
        tickfont=dict(size=12, color='#0f172a')
    )
    
    return legend_style(fig, "5. อาชีพที่มีรายได้เฉลี่ยสูงสุด", 450)

# ==================================================
# Layout
# ==================================================
def create_demo_layout():
    df = load_data()
    df = process_member(df)
    
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
                html.H2(
                    "ข้อมูลสมาชิก", 
                    className="fw-bold", 
                    style={
                        "color": "#0f172a", 
                        "letterSpacing": "0.5px",
                        "fontSize": "32px",
                        "fontFamily": "Sarabun, sans-serif",
                        "textShadow": "0 2px 4px rgba(0,0,0,0.05)",
                        "paddingBottom": "12px"
                    }
                ),
            ], className="mb-4"),

            render_member_kpis(df),

            dbc.Row([dbc.Col(card(chart_growth_time(df)), width=12)], className="g-4 mb-3"),
            
            dbc.Row([
                dbc.Col(card(chart_gender_career(df)), lg=6),
                dbc.Col(card(chart_income_pie(df)), lg=6)
            ], className="g-4 mb-3"),

            dbc.Row([
                dbc.Col(card(chart_gen_area(df)), lg=6),
                dbc.Col(card(chart_income_career(df)), lg=6)
            ], className="g-4"),
        ]
    )

layout = create_demo_layout()