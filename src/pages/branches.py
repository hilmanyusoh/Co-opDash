from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from ..data_manager import load_data
from ..components.kpi_cards import render_branch_kpis
from ..components.chart_card import chart_card
from ..components.theme import THEME

CHART_HEIGHT = 340

# สีสำหรับแต่ละสาขา (Modern color palette)
BRANCH_COLORS = {
    "สาขา 1": "#8B5CF6",  # Purple
    "สาขา 2": "#3B82F6",  # Blue
    "สาขา 3": "#10B981",  # Green
    "สาขา 4": "#F59E0B",  # Orange
    "สาขา 5": "#EF4444",  # Red
}

# ==================================================
# 1. Data Processing
# ==================================================
def get_processed_data():
    df = load_data()
    if df.empty:
        return df

    df["registration_date"] = pd.to_datetime(df["registration_date"], errors="coerce")
    df["approval_date"] = pd.to_datetime(df["approval_date"], errors="coerce")
    df["Days_to_Approve"] = (df["approval_date"] - df["registration_date"]).dt.days
    df.loc[df["Days_to_Approve"] < 0, "Days_to_Approve"] = 0

    if "income" in df.columns:
        df["Income_Clean"] = (
            df["income"]
            .astype(str)
            .str.replace(",", "")
            .pipe(pd.to_numeric, errors="coerce")
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
# 2. Layout Helper (สไตล์เดียวกับ Overview)
# ==================================================
def apply_layout(fig, height=CHART_HEIGHT):
    """ปรับแต่งรูปแบบกราฟให้เหมือนหน้า Overview"""
    fig.update_layout(
        height=height,
        margin=dict(t=50, b=40, l=60, r=30),
        plot_bgcolor="rgba(255, 255, 255, 0.02)",
        paper_bgcolor="rgba(255, 255, 255, 0)",
        font=dict(
            family="Sarabun, sans-serif",
            color="#334155",
            size=13
        ),
        
        hovermode="closest",
        hoverlabel=dict(
            bgcolor="rgba(15, 23, 42, 0.95)",
            font_family="Sarabun, sans-serif",
            font_color="white",
            bordercolor="rgba(148, 163, 184, 0.3)",
        ),
    )
    
    # เพิ่ม grid ที่นุ่มนวล
    fig.update_xaxes(
        gridcolor="rgba(203, 213, 225, 0.3)",
        showline=True,
        linewidth=1,
        linecolor="#E2E8F0",
        showgrid=False
    )
    fig.update_yaxes(
        gridcolor="rgba(203, 213, 225, 0.4)",
        showline=True,
        linewidth=1,
        linecolor="#E2E8F0"
    )
    
    return fig

# ==================================================
# 3. Charts
# ==================================================
def chart_member_column(df):
    """กราฟแท่ง: จำนวนสมาชิกแต่ละสาขา (แบบไม่มี Legend)"""
    counts = (
        df["branch_name"]
        .value_counts()
        .sort_index()
        .reset_index()
    )
    counts.columns = ["branch_name", "count"]

    fig = px.bar(
        counts,
        x="branch_name",
        y="count",
        text="count",
        color="branch_name",
        color_discrete_map=BRANCH_COLORS
    )
    
    fig.update_traces(
        texttemplate='%{text:,}',
        textposition='outside',
        hovertemplate="<b>%{x}</b><br>จำนวนสมาชิก: %{y:,} คน<extra></extra>",
        marker=dict(line=dict(width=2, color='white'))
    )

    fig.update_yaxes(title="จำนวนสมาชิก (คน)")
    fig.update_xaxes(title="สาขา", showgrid=False)
    
    return apply_layout(fig)

def chart_income_line(df):
    """กราฟเส้น: รายได้เฉลี่ยต่อคนรายสาขา"""
    avg_income = (
        df.groupby("branch_name")["Income_Clean"]
        .mean()
        .sort_index()
        .reset_index()
    )

    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=avg_income["branch_name"],
        y=avg_income["Income_Clean"],
        mode="lines+markers+text",
        name="รายได้เฉลี่ย",
        line=dict(color="#3B82F6", width=3),
        marker=dict(size=10, color="#3B82F6", line=dict(width=2, color='white')),
        fill="tozeroy",
        fillcolor="rgba(59, 130, 246, 0.1)",
        text=[f"฿{val:,.0f}" for val in avg_income["Income_Clean"]],
        textposition="top center",
        hovertemplate="<b>%{x}</b><br>รายได้เฉลี่ย: ฿%{y:,.0f}<extra></extra>"
    ))

    fig.update_yaxes(title="รายได้เฉลี่ย (บาท)", tickformat=",.0f")
    fig.update_xaxes(title="", showgrid=False)
    
    return apply_layout(fig)

def chart_approval_mode(df):
    """กราฟแท่งนอน: ระยะเวลาอนุมัติเฉลี่ย"""
    branch_modes = (
        df.groupby("branch_name")["Days_to_Approve"]
        .apply(lambda x: x.mode().iloc[0] if not x.mode().empty else 0)
        .sort_values(ascending=True)
        .reset_index()
    )

    fig = px.bar(
        branch_modes,
        y="branch_name",
        x="Days_to_Approve",
        orientation="h",
        text="Days_to_Approve",
        color="branch_name",
        color_discrete_map=BRANCH_COLORS
    )

    fig.update_traces(
        texttemplate='%{text} วัน',
        textposition='outside',
        hovertemplate="<b>%{y}</b><br>ระยะเวลาอนุมัติ: %{x} วัน<extra></extra>",
        marker=dict(line=dict(width=2, color='white'))
    )

    fig.update_xaxes(title="จำนวนวัน")
    fig.update_yaxes(title="", showgrid=False)
    
    return apply_layout(fig)

def chart_member_income_dual(df):
    summary = df.groupby("branch_name").agg(
        member_count=("member_id", "count"),
        total_income=("Income_Clean", "sum")
    ).reset_index()

    fig = go.Figure()

    # แท่งกราฟ: จำนวนสมาชิก (ไม่แสดง legend)
    for idx, row in summary.iterrows():
        fig.add_trace(go.Bar(
            x=[row["branch_name"]],
            y=[row["member_count"]],
            name=row["branch_name"],
            marker_color=BRANCH_COLORS.get(row["branch_name"], "#64748B"),
            text=[f'{row["member_count"]:,}'],
            texttemplate='%{text}',
            textposition='outside',
            hovertemplate=f"<b>{row['branch_name']}</b><br>จำนวนสมาชิก: %{{y:,}} คน<extra></extra>",
            showlegend=False,
            legendgroup=row["branch_name"]
        ))

    # เส้นกราฟ: รายได้รวม (แสดง legend)
    fig.add_trace(go.Scatter(
        x=summary["branch_name"],
        y=summary["total_income"],
        name="รายได้รวมทั้งหมด",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color="#F59E0B", width=3, dash="dot"),
        marker=dict(size=12, color="#F59E0B", line=dict(width=2, color='white')),
        hovertemplate="<b>%{x}</b><br>รายได้รวม: ฿%{y:,.0f}<extra></extra>",
        showlegend=True
    ))

    fig.update_layout(
        yaxis=dict(
            title="จำนวนสมาชิก (คน)",
            side="left"
        ),
        yaxis2=dict(
            title="รายได้รวม (บาท)",
            overlaying="y",
            side="right",
            tickformat=",",
            showgrid=False
        ),
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="rgba(148, 163, 184, 0.3)",
            borderwidth=1
        )
    )

    fig.update_xaxes(showgrid=False)
    
    return apply_layout(fig)

# ==================================================
# 4. Main Layout
# ==================================================
def create_branch_layout():
    df = get_processed_data()

    if df.empty:
        return dbc.Alert("ไม่พบข้อมูล", color="warning", className="mt-5")

    return dbc.Container(
        fluid=True,
        style={"padding": "20px 30px", "maxWidth": "1400px"},
        children=[
            html.H3("ข้อมูลสาขา", className="fw-bold mb-3"),
            render_branch_kpis(df),

            dbc.Row(
                [
                    dbc.Col(
                        chart_card(chart_member_column(df), "จำนวนสมาชิกแต่ละสาขา"),
                        lg=6,
                    ),
                    dbc.Col(
                        chart_card(chart_income_line(df), "รายได้เฉลี่ยต่อคน"),
                        lg=6,
                    ),
                ],
                className="g-3 mb-3",
            ),

            dbc.Row(
                [
                    dbc.Col(
                        chart_card(chart_approval_mode(df), "ระยะเวลาอนุมัติเฉลี่ย"),
                        lg=6,
                    ),
                    dbc.Col(
                        chart_card(chart_member_income_dual(df), "สมาชิก vs รายได้รวม"),
                        lg=6,
                    ),
                ],
                className="g-3",
            ),
        ],
    )

layout = create_branch_layout()