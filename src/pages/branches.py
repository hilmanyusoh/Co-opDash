from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from ..data_manager import load_data
from ..components.kpi_cards import render_branch_kpis

# ความสูงเท่ากันทุก dashboard
CHART_HEIGHT = 340

# ==================================================
# 1. Data Processing
# ==================================================
def get_processed_data():
    df = load_data()
    if df.empty:
        return df

    df['registration_date'] = pd.to_datetime(df['registration_date'], errors='coerce')
    df['approval_date'] = pd.to_datetime(df['approval_date'], errors='coerce')
    df['Days_to_Approve'] = (df['approval_date'] - df['registration_date']).dt.days
    df.loc[df['Days_to_Approve'] < 0, 'Days_to_Approve'] = 0

    if "income" in df.columns:
        df["Income_Clean"] = (
            df["income"]
            .astype(str)
            .str.replace(",", "")
            .astype(float)
            .fillna(0)
        )

    branch_map = {
        1: "สาขา 1",
        2: "สาขา 2",
        3: "สาขา 3",
        4: "สาขา 4",
        5: "สาขา 5",
    }

    if "branch_no" in df.columns:
        df["branch_name"] = df["branch_no"].map(branch_map).fillna(
            df["branch_no"].astype(str).apply(lambda x: f"สาขา {x}")
        )

    return df

# ==================================================
# 2. Layout Helper
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
# 3. Charts
# ==================================================

def chart_member_column(df):
    counts = (
        df["branch_name"]
        .value_counts()
        .sort_index()
        .reset_index()
    )
    counts.columns = ["branch_name", "count"]

    dark_colors = ['#1e3a8a', '#b91c1c', '#15803d', '#b45309', '#6d28d9', '#0369a1', '#be185d', '#475569']

    fig = px.bar(
        counts,
        x="branch_name",
        y="count",
        color="branch_name",
        text="count",
        color_discrete_sequence=dark_colors,
        labels={"branch_name": "ชื่อสาขา", "count": "จำนวนสมาชิก"},
    )
    
    fig.update_traces(
        textposition="outside", 
        texttemplate="<b>%{text}</b>",
        textfont=dict(size=11, family='Sarabun', color='#1e293b'),
        marker_line_color='#ffffff', 
        marker_line_width=2, 
        opacity=0.95,
        hovertemplate='<b>%{x}</b><br>จำนวน: %{y} คน<extra></extra>',
        showlegend=False
    )

    fig.update_xaxes(
        title="<b>สาขา</b>",
        showgrid=False,
        showline=True,
        linewidth=2,
        linecolor='#cbd5e1',
        tickfont=dict(size=11, color='#0f172a', family='Sarabun')
    )
    
    fig.update_yaxes(
        title="<b>จำนวนสมาชิก</b>",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(203, 213, 225, 0.4)',
        showline=False,
        zeroline=True,
        zerolinecolor='#cbd5e1',
        zerolinewidth=2,
        tickfont=dict(size=11, color='#334155', family='Sarabun')
    )

    fig.update_layout(
        margin=dict(t=50, b=40, l=50, r=30),
        paper_bgcolor='rgba(255, 255, 255, 0)',
        plot_bgcolor='rgba(248, 250, 252, 0.3)'
    )

    return apply_layout(fig, "จำนวนสมาชิกแต่ละสาขา", CHART_HEIGHT)

def chart_income_line(df):
    avg_income = (
        df.groupby("branch_name")["Income_Clean"]
        .mean()
        .sort_index()
        .reset_index()
    )

    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=avg_income["branch_name"],
            y=avg_income["Income_Clean"],
            mode="lines+markers",
            name="รายได้เฉลี่ย",
            line=dict(color="#059669", width=3, shape="spline"),
            marker=dict(
                size=10,
                color="white",
                line=dict(color="#059669", width=2.5),
            ),
            fill="tozeroy",
            fillcolor="rgba(5, 150, 105, 0.1)",
            text=[f"฿{val:,.0f}" for val in avg_income["Income_Clean"]],
            textposition="top center",
            textfont=dict(size=10, family='Sarabun', color='#0f172a'),
            hovertemplate="<b>%{x}</b><br>รายได้เฉลี่ย: ฿%{y:,.0f}<extra></extra>"
        )
    )

    fig.update_xaxes(
        title="<b>สาขา</b>",
        showgrid=False,
        showline=True,
        linewidth=2,
        linecolor='#cbd5e1',
        tickfont=dict(size=11, color='#0f172a', family='Sarabun')
    )
    
    fig.update_yaxes(
        title="<b>รายได้เฉลี่ย (บาท)</b>",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(203, 213, 225, 0.4)',
        showline=False,
        zeroline=True,
        zerolinecolor='#cbd5e1',
        zerolinewidth=2,
        tickformat=',.0f',
        tickfont=dict(size=11, color='#334155', family='Sarabun')
    )

    fig.update_layout(
        margin=dict(t=50, b=40, l=60, r=30),
        paper_bgcolor='rgba(255, 255, 255, 0)',
        plot_bgcolor='rgba(248, 250, 252, 0.3)',
        showlegend=False
    )

    return apply_layout(fig, "รายได้เฉลี่ยต่อคนรายสาขา", CHART_HEIGHT)

def chart_approval_mode(df):
    def mode_val(x):
        m = x.mode()
        return m.iloc[0] if not m.empty else 0

    branch_modes = (
        df.groupby("branch_name")["Days_to_Approve"]
        .apply(mode_val)
        .sort_values(ascending=True)
        .reset_index()
    )

    colors = [
        "#b91c1c" if v > 5 else "#b45309" if v > 2 else "#15803d"
        for v in branch_modes["Days_to_Approve"]
    ]

    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(
            y=branch_modes["branch_name"],
            x=branch_modes["Days_to_Approve"],
            orientation="h",
            marker=dict(
                color=colors,
                line=dict(color='#ffffff', width=2),
                opacity=0.9
            ),
            text=[f"<b>{int(v)}</b>" for v in branch_modes["Days_to_Approve"]],
            textposition="outside",
            textfont=dict(family="Sarabun", size=11, color="#1e293b"),
            hovertemplate="<b>%{y}</b><br>ระยะเวลาอนุมัติหลัก: %{x} วัน<extra></extra>",
            showlegend=False,
        )
    )

    # Custom Legend
    for label, color in [
        ("เร็ว (≤2 วัน)", "#15803d"),
        ("ปกติ (3–5 วัน)", "#b45309"),
        ("ช้า (>5 วัน)", "#b91c1c"),
    ]:
        fig.add_trace(go.Bar(
            x=[None], y=[None], name=label, marker_color=color,
            marker_line=dict(color='white', width=1)
        ))

    fig.update_xaxes(
        title="<b>จำนวนวัน</b>",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(203, 213, 225, 0.4)',
        range=[0, max(branch_modes["Days_to_Approve"]) + 2],
        tickfont=dict(size=11, color='#334155')
    )
    
    fig.update_yaxes(
        title="<b>สาขา</b>",
        showline=True,
        linecolor='#cbd5e1',
        linewidth=1,
        showgrid=False,
        tickfont=dict(size=11, color='#0f172a', family='Sarabun')
    )

    fig.update_layout(
        legend=dict(
            title="<b>ประสิทธิภาพ</b>",
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
        margin=dict(t=50, b=75, l=80, r=30),
        paper_bgcolor='rgba(255, 255, 255, 0)',
        plot_bgcolor='rgba(248, 250, 252, 0.3)'
    )

    return apply_layout(fig, "ความเร็วการอนุมัติหลัก (Mode)", CHART_HEIGHT)

def chart_member_income_dual(df):
    summary = df.groupby("branch_name").agg(
        member_count=("member_id", "count"),
        total_income=("Income_Clean", "sum")
    ).sort_values("member_count", ascending=False).reset_index()

    fig = go.Figure()

    # แท่งกราฟ (แกน Y หลัก)
    fig.add_trace(go.Bar(
        x=summary["branch_name"],
        y=summary["member_count"],
        name="จำนวนสมาชิก",
        marker=dict(color="#1e3a8a", opacity=0.85, line=dict(color='white', width=1.5)),
        text=[f"{int(v)}" for v in summary["member_count"]],
        textposition="outside",
        textfont=dict(size=11, family='Sarabun'),
        hovertemplate="สมาชิก: %{y:,} คน<extra></extra>"
    ))

    # เส้นกราฟ (แกน Y ที่สอง)
    fig.add_trace(go.Scatter(
        x=summary["branch_name"],
        y=summary["total_income"],
        name="รายได้รวม",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color="#b91c1c", width=3, shape='spline'),
        marker=dict(size=8, symbol="diamond", color="#b91c1c", line=dict(color='white', width=1.5)),
        hovertemplate="รายได้รวม: ฿%{y:,.0f}<extra></extra>"
    ))

    fig.update_layout(
        yaxis=dict(
            title=dict(
                text="<b>จำนวนสมาชิก</b>",
                font=dict(size=12, color="#1e3a8a", family="Sarabun")
            ),
            tickfont=dict(color="#1e3a8a", size=11),
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(203, 213, 225, 0.4)'
        ),
        yaxis2=dict(
            title=dict(
                text="<b>รายได้รวม (บาท)</b>",
                font=dict(size=12, color="#b91c1c", family="Sarabun")
            ),
            tickfont=dict(color="#b91c1c", size=11),
            anchor="x",
            overlaying="y",
            side="right",
            tickformat=",",
            showgrid=False
        ),
        legend=dict(
            title="<b>ตัวชี้วัด</b>",
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
        margin=dict(l=60, r=60, t=50, b=75),
        hovermode="x unified",
        paper_bgcolor='rgba(255, 255, 255, 0)',
        plot_bgcolor="rgba(248, 250, 252, 0.3)"
    )

    fig.update_xaxes(
        title=dict(text="<b>สาขา</b>", font=dict(family="Sarabun", size=12)),
        showline=True,
        linewidth=2,
        linecolor='#cbd5e1',
        tickfont=dict(size=11, color='#0f172a', family='Sarabun')
    )

    return apply_layout(fig, "เปรียบเทียบจำนวนสมาชิกและรายได้รวมรายสาขา", CHART_HEIGHT)

# ==================================================
# 4. Main Layout
# ==================================================
def create_branch_layout():
    df = get_processed_data()
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
                    "ข้อมูลสาขา",
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

            render_branch_kpis(df),

            dbc.Row([
                dbc.Col(card(chart_member_column(df)), xs=12, lg=6),
                dbc.Col(card(chart_income_line(df)), xs=12, lg=6),
            ], className="g-3 mb-3"),

            dbc.Row([
                dbc.Col(card(chart_approval_mode(df)), xs=12, lg=6),
                dbc.Col(card(chart_member_income_dual(df)), xs=12, lg=6),
            ], className="g-3"),
        ],
    )

layout = create_branch_layout()