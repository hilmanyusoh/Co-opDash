from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from ..data_manager import load_data
from ..components.kpi_cards import render_branch_kpis

CHART_HEIGHT = 360

# สีสำหรับแต่ละสาขา
BRANCH_COLORS = {
    "สาขา 1": "#8B5CF6",
    "สาขา 2": "#3B82F6",
    "สาขา 3": "#10B981",
    "สาขา 4": "#F59E0B",
    "สาขา 5": "#EF4444",
}

# ==================================================
# 1. Data Processing (คงเดิม)
# ==================================================
def get_processed_data():
    df = load_data()
    if df.empty: return df
    df["registration_date"] = pd.to_datetime(df["registration_date"], errors="coerce")
    df["approval_date"] = pd.to_datetime(df["approval_date"], errors="coerce")
    df["Days_to_Approve"] = (df["approval_date"] - df["registration_date"]).dt.days
    df.loc[df["Days_to_Approve"] < 0, "Days_to_Approve"] = 0
    if "income" in df.columns:
        df["Income_Clean"] = df["income"].astype(str).str.replace(",", "").pipe(pd.to_numeric, errors="coerce").fillna(0)
    branch_map = {1: "สาขา 1", 2: "สาขา 2", 3: "สาขา 3", 4: "สาขา 4", 5: "สาขา 5"}
    if "branch_no" in df.columns:
        df["branch_name"] = df["branch_no"].map(branch_map).fillna(df["branch_no"].astype(str).apply(lambda x: f"สาขา {x}"))
    return df

# ==================================================
# 2. Layout Helper (ปรับเป็นขาวล้วนเหมือนหน้าอื่นๆ)
# ==================================================
def apply_layout(fig, height=CHART_HEIGHT, show_legend=True):
    fig.update_layout(
        height=height,
        margin=dict(t=40, b=40, l=60, r=30), # เพิ่ม Top margin สำหรับ Legend
        plot_bgcolor="white",               # พื้นหลังขาวล้วน
        paper_bgcolor="white",              # พื้นหลังขาวล้วน
        font=dict(family="Sarabun, sans-serif", color="#334155", size=13),
        showlegend=show_legend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,                         # ย้าย Legend ไปไว้ด้านบน
            xanchor="center",
            x=0.5
        ),
        hovermode="closest"
    )
    # เส้น Grid จางๆ สีเดียวกับหน้า Overview
    fig.update_xaxes(gridcolor="#F1F5F9", showline=True, linewidth=1, linecolor="#F1F5F9")
    fig.update_yaxes(gridcolor="#F1F5F9", showline=True, linewidth=1, linecolor="#F1F5F9")
    return fig

# ==================================================
# 3. Charts
# ==================================================
def chart_member(df):
    counts = df["branch_name"].value_counts().sort_index().reset_index()
    counts.columns = ["branch_name", "count"]
    fig = px.bar(counts, x="branch_name", y="count", text="count", color="branch_name", color_discrete_map=BRANCH_COLORS)
    fig.update_traces(texttemplate='%{text:,}', textposition='outside', marker=dict(line=dict(width=1, color='white')))
    fig.update_xaxes(title="")
    fig.update_yaxes(title="จำนวนสมาชิก (คน)")
    return apply_layout(fig)

def chart_income_line(df):
    avg_income = df.groupby("branch_name")["Income_Clean"].mean().sort_index().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=avg_income["branch_name"], y=avg_income["Income_Clean"],
        mode="lines+markers", name="รายได้เฉลี่ย",
        line=dict(color="#3B82F6", width=3),
        marker=dict(size=10, color="#3B82F6", line=dict(width=2, color='white')),
        fill="tozeroy", fillcolor="rgba(59, 130, 246, 0.05)"
    ))
    fig.update_yaxes(title="รายได้เฉลี่ย (บาท)")
    return apply_layout(fig)

def chart_approval_mode(df):
    branch_modes = df.groupby("branch_name")["Days_to_Approve"].apply(
        lambda x: x.mode().iloc[0] if not x.mode().empty else 0
    ).sort_values(ascending=True).reset_index()
    fig = px.bar(branch_modes, y="branch_name", x="Days_to_Approve", orientation="h", text="Days_to_Approve",
                 color="branch_name", color_discrete_map=BRANCH_COLORS)
    fig.update_traces(texttemplate='%{text} วัน', textposition='outside')
    fig.update_xaxes(title="จำนวนวันอนุมัติ")
    fig.update_yaxes(title="")
    return apply_layout(fig, show_legend=False)

def chart_member_income_dual(df):
    summary = df.groupby("branch_name").agg(member_count=("member_id", "count"), total_income=("Income_Clean", "sum")).reset_index()
    fig = go.Figure()
    # แท่งกราฟ
    for idx, row in summary.iterrows():
        fig.add_trace(go.Bar(
            x=[row["branch_name"]], y=[row["member_count"]], name=row["branch_name"],
            marker_color=BRANCH_COLORS.get(row["branch_name"], "#64748B"),
            text=[row["member_count"]], textposition='outside'
        ))
    # เส้นกราฟ
    fig.add_trace(go.Scatter(
        x=summary["branch_name"], y=summary["total_income"], name="รายได้รวม",
        yaxis="y2", mode="lines+markers", line=dict(color="#F59E0B", width=3, dash="dot")
    ))
    fig.update_layout(
        yaxis=dict(title="จำนวนสมาชิก (คน)"),
        yaxis2=dict(title="รายได้รวม (บาท)", overlaying="y", side="right", showgrid=False),
        barmode='group'
    )
    return apply_layout(fig)

# ==================================================
# 4. Main Layout (ปรับพื้นหลัง Container เป็นขาว)
# ==================================================
def create_branch_layout():
    df = get_processed_data()
    if df.empty:
        return dbc.Container(dbc.Alert("ไม่พบข้อมูล", color="warning", className="mt-5"))

    def card(fig, title, icon=""):
        return dbc.Card(
            dbc.CardBody([
                html.Div([
                    html.I(className=f"bi {icon} me-2", style={"fontSize": "1.2rem", "color": "#3B82F6"}),
                    html.H6(title, className="fw-bold mb-0 d-inline-block", style={"color": "#1E293B"}),
                ], className="mb-3"),
                dcc.Graph(figure=fig, config={"displayModeBar": False, "responsive": True}),
            ], style={"padding": "20px"}),
            className="shadow-sm rounded-3 border-0 mb-3",
            style={"backgroundColor": "white"} # การ์ดขาว
        )

    return dbc.Container(
        fluid=True,
        style={
            "padding": "20px 30px",
            "maxWidth": "1400px",
            "margin": "0 auto",
            "backgroundColor": "#FFFFFF", # เปลี่ยนเป็นขาวล้วน
            "minHeight": "100vh"
        },
        children=[
            html.Div([
                html.H3("ข้อมูลสาขา", className="fw-bold mb-1", style={"color": "#1E293B"}),
                html.P("วิเคราะห์ข้อมูลสมาชิกและรายได้ของแต่ละสาขา", className="text-muted mb-4")
            ]),
            render_branch_kpis(df),
            dbc.Row([
                dbc.Col(card(chart_member(df), "จำนวนสมาชิกแต่ละสาขา", "bi-people-fill"), lg=6),
                dbc.Col(card(chart_income_line(df), "รายได้เฉลี่ยต่อคนรายสาขา", "bi-graph-up-arrow"), lg=6),
            ], className="g-3 mb-3"),
            dbc.Row([
                dbc.Col(card(chart_approval_mode(df), "ระยะเวลาอนุมัติเฉลี่ยแต่ละสาขา", "bi-clock-history"), lg=6),
                dbc.Col(card(chart_member_income_dual(df), "เปรียบเทียบสมาชิกและรายได้รวม", "bi-bar-chart-line"), lg=6),
            ], className="g-3"),
        ],
    )

layout = create_branch_layout()