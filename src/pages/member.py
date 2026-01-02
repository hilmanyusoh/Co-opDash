from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from ..data_manager import load_data
from ..components.kpi_cards import render_member_kpis

# ความสูงเท่ากันทุก dashboard
CHART_HEIGHT = 340

# ==================================================
# Data Processing
# ==================================================
def process_member(df):
    if df.empty:
        return df

    # ---------- Gender ----------
    if "gender_name" in df.columns:
        df["Gender"] = (
            df["gender_name"]
            .map({"นาย": "ชาย", "นาง": "หญิง", "นางสาว": "หญิง"})
            .fillna("อื่นๆ")
        )

    # ---------- Generation ----------
    if "birthday" in df.columns:
        df["birthday"] = pd.to_datetime(df["birthday"], errors="coerce")

        def gen_map(x):
            if pd.isnull(x):
                return "Unknown"
            elif x.year <= 1964:
                return "Baby Boomer"
            elif x.year <= 1980:
                return "Gen X"
            elif x.year <= 1996:
                return "Gen Y"
            else:
                return "Gen Z"

        df["Gen"] = df["birthday"].apply(gen_map)

    # ---------- Income ----------
    if "income" in df.columns:
        df["Income_Clean"] = (
            df["income"]
            .astype(str)
            .str.replace(",", "")
            .pipe(pd.to_numeric, errors="coerce")
            .fillna(0)
        )

        bins = [0, 15000, 30000, 50000, 100000, float("inf")]
        labels = ["< 15K", "15K - 30K", "30K - 50K", "50K - 100K", "100K+"]
        df["Income_Level"] = pd.cut(
            df["Income_Clean"], bins=bins, labels=labels, right=False
        )

    # ---------- Registration Date ----------
    if "registration_date" in df.columns:
        df["reg_date"] = pd.to_datetime(df["registration_date"], errors="coerce")

    return df

# ==================================================
# Chart Style Helper
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
def chart_growth_time(df):
    if "reg_date" not in df.columns:
        return go.Figure()

    trend = (
        df.dropna(subset=["reg_date"])
        .groupby(df["reg_date"].dt.to_period("M"))
        .size()
        .reset_index(name="count")
    )

    if trend.empty:
        return go.Figure()

    trend["reg_date"] = trend["reg_date"].dt.to_timestamp()
    y_max = trend["count"].max()

    fig = go.Figure(
        go.Scatter(
            x=trend["reg_date"],
            y=trend["count"],
            mode="lines+markers",
            name="จำนวนสมาชิกใหม่",
            line=dict(color="#3b82f6", width=3, shape='spline'),
            marker=dict(size=6, color='#3b82f6', line=dict(color='white', width=1.5)),
            fill="tozeroy",
            fillcolor="rgba(59, 130, 246, 0.1)",
            hovertemplate='<b>%{x|%b %Y}</b><br>สมาชิกใหม่: %{y} คน<extra></extra>'
        )
    )

    fig.update_yaxes(
        range=[0, y_max * 1.15],
        title="<b>จำนวนสมาชิก</b>",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(203, 213, 225, 0.4)',
        tickfont=dict(size=11, color='#334155')
    )
    
    fig.update_xaxes(
        tickformat="%b %Y",
        title="<b>เดือน/ปี</b>",
        showgrid=False,
        showline=True,
        linewidth=1.5,
        linecolor='#cbd5e1',
        tickfont=dict(size=11, color='#334155', family='Sarabun')
    )

    fig.update_layout(
        margin=dict(t=50, b=40, l=60, r=30),
        paper_bgcolor='rgba(255, 255, 255, 0)',
        plot_bgcolor='rgba(248, 250, 252, 0.3)'
    )

    return apply_layout(fig, "แนวโน้มการเพิ่มขึ้นของสมาชิกรายเดือน", CHART_HEIGHT)

def chart_gender_career(df):
    if "Gender" not in df.columns:
        return go.Figure()

    career_col = "career_name" if "career_name" in df.columns else "career"
    if career_col not in df.columns:
        return go.Figure()

    top = df[career_col].value_counts().head(5).index
    data = df[df[career_col].isin(top)]

    fig = px.histogram(
        data,
        y=career_col,
        color="Gender",
        orientation="h",
        barmode="group",
        text_auto=True,
        color_discrete_map={"ชาย": "#3b82f6", "หญิง": "#ec4899", "อื่นๆ": "#64748b"}
    )

    fig.update_traces(
        marker=dict(line=dict(color='white', width=1.5)),
        textfont=dict(size=11, family='Sarabun'),
        hovertemplate='<b>%{y}</b><br>จำนวน: %{x} คน<extra></extra>'
    )

    fig.update_layout(
        legend=dict(
            title="<b>เพศ</b>",
            orientation="h",
            xanchor="center",
            yanchor="top",
            x=0.5,
            y=-0.20,
            font=dict(size=11, family='Sarabun'),
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="rgba(148, 163, 184, 0.3)",
            borderwidth=1
        ),
        margin=dict(t=50, b=75, l=100, r=30),
        paper_bgcolor='rgba(255, 255, 255, 0)',
        plot_bgcolor='rgba(248, 250, 252, 0.3)'
    )

    fig.update_xaxes(
        title="<b>จำนวนสมาชิก</b>",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(203, 213, 225, 0.4)',
        tickfont=dict(size=11, color='#334155')
    )

    fig.update_yaxes(
        title="<b>อาชีพ</b>",
        showgrid=False,
        tickfont=dict(size=11, color='#0f172a', family='Sarabun')
    )

    return apply_layout(fig, "สัดส่วนเพศแยกตามกลุ่มอาชีพ", CHART_HEIGHT)

def chart_income_pie(df):
    if "Income_Level" not in df.columns:
        return go.Figure()

    counts = (
        df["Income_Level"]
        .value_counts()
        .reindex(["< 15K", "15K - 30K", "30K - 50K", "50K - 100K", "100K+"])
        .fillna(0)
    )

    colors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6']

    fig = go.Figure(
        go.Pie(
            labels=counts.index,
            values=counts.values,
            hole=0.45,
            marker=dict(
                colors=colors,
                line=dict(color='#ffffff', width=2)
            ),
            textinfo="percent+label",
            textfont=dict(size=13, family='Sarabun', color='white'),
            hovertemplate='<b>%{label}</b><br>จำนวน: %{value} คน<br>สัดส่วน: %{percent}<extra></extra>'
        )
    )

    fig.update_layout(
        legend=dict(
            title="<b>ระดับรายได้</b>",
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

    return apply_layout(fig, "สัดส่วนสมาชิกแยกตามระดับรายได้", CHART_HEIGHT)

def chart_gen_area(df):
    if "Gen" not in df.columns:
        return go.Figure()

    prov_col = "province_name" if "province_name" in df.columns else "province"
    if prov_col not in df.columns:
        return go.Figure()

    top = df[prov_col].value_counts().head(8).index
    data = (
        df[df[prov_col].isin(top)]
        .groupby([prov_col, "Gen"])
        .size()
        .reset_index(name="count")
    )

    fig = px.bar(
        data,
        x=prov_col,
        y="count",
        color="Gen",
        barmode="stack",
        color_discrete_sequence=px.colors.qualitative.Set2,
        text_auto=True
    )

    fig.update_traces(
        marker=dict(line=dict(color='white', width=1.5)),
        textfont=dict(size=10, family='Sarabun'),
        hovertemplate='<b>%{x}</b><br>%{fullData.name}: %{y} คน<extra></extra>'
    )

    fig.update_layout(
        legend=dict(
            title="<b></b>",
            orientation="h",
            xanchor="center",
            yanchor="top",
            x=0.5,
            y=-0.3,
            font=dict(size=11, family='Sarabun'),
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="rgba(148, 163, 184, 0.3)",
            borderwidth=1
        ),
        margin=dict(t=50, b=75, l=50, r=30),
        paper_bgcolor='rgba(255, 255, 255, 0)',
        plot_bgcolor='rgba(248, 250, 252, 0.3)'
    )

    fig.update_xaxes(
        title="",
        showgrid=False,
        tickfont=dict(size=11, color='#334155', family='Sarabun')
    )

    fig.update_yaxes(
        title="<b>จำนวนสมาชิก</b>",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(203, 213, 225, 0.4)',
        tickfont=dict(size=11, color='#334155')
    )

    return apply_layout(fig, "การกระจายกลุ่ม Generation ในจังหวัดหลัก", CHART_HEIGHT)

def chart_income_career(df):
    if "Income_Clean" not in df.columns:
        return go.Figure()

    career_col = "career_name" if "career_name" in df.columns else "career"
    if career_col not in df.columns:
        return go.Figure()

    avg = (
        df[df["Income_Clean"] > 0]
        .groupby(career_col)["Income_Clean"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    gradient_colors = ['#3b82f6', '#8b5cf6', '#ec4899', '#f97316', '#eab308', 
                       '#22c55e', '#14b8a6', '#06b6d4', '#0ea5e9', '#6366f1']

    fig = go.Figure()

    for i, row in avg.iterrows():
        fig.add_trace(go.Bar(
            y=[row[career_col]],
            x=[row["Income_Clean"]],
            orientation='h',
            name=row[career_col],
            marker=dict(
                color=gradient_colors[i % len(gradient_colors)],
                line=dict(color='white', width=2)
            ),
            text=f"฿{row['Income_Clean']:,.0f}",
            textposition='outside',
            textfont=dict(size=11, family='Sarabun'),
            hovertemplate=f'<b>{row[career_col]}</b><br>รายได้เฉลี่ย: ฿%{{x:,.0f}}<extra></extra>',
            showlegend=False
        ))

    fig.update_layout(
        margin=dict(t=50, b=40, l=100, r=30),
        paper_bgcolor='rgba(255, 255, 255, 0)',
        plot_bgcolor='rgba(248, 250, 252, 0.3)'
    )

    fig.update_xaxes(
        title="<b>รายได้เฉลี่ย (บาท)</b>",
        tickformat=",.0f",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(203, 213, 225, 0.4)',
        tickfont=dict(size=11, color='#334155')
    )

    fig.update_yaxes(
        title="<b>อาชีพ</b>",
        showgrid=False,
        tickfont=dict(size=11, color='#0f172a', family='Sarabun')
    )

    return apply_layout(fig, "อาชีพที่มีรายได้เฉลี่ยสูงสุด (Top 10)", CHART_HEIGHT)

# ==================================================
# Layout
# ==================================================
def create_demo_layout():
    df = process_member(load_data())

    if df.empty:
        return dbc.Container(
            dbc.Alert("ไม่พบข้อมูล", color="warning", className="mt-5")
        )

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
                    "ข้อมูลสมาชิก",
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

            render_member_kpis(df),

            dbc.Row([
                dbc.Col(card(chart_growth_time(df)), xs=12)
            ], className="mb-3"),

            dbc.Row([
                dbc.Col(card(chart_gender_career(df)), xs=12, lg=6),
                dbc.Col(card(chart_income_pie(df)), xs=12, lg=6),
            ], className="g-3 mb-3"),

            dbc.Row([
                dbc.Col(card(chart_gen_area(df)), xs=12, lg=6),
                dbc.Col(card(chart_income_career(df)), xs=12, lg=6),
            ], className="g-3"),
        ],
    )

layout = create_demo_layout()