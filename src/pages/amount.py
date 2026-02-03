from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from functools import lru_cache

from ..data_manager import load_data
from ..components.kpi_cards import render_amount_kpis
from ..components.chart_card import chart_card
from ..components.theme import THEME

# ==================================================
# Config
# ==================================================
CHART_HEIGHT = 340
UI_REVISION_KEY = "amount-static"

# ==================================================
# Data Preprocessing
# ==================================================
def preprocess_amount(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    df = df.copy()
    
    if "member_id" in df.columns and "customer_id" not in df.columns:
        df["customer_id"] = df["member_id"]

    if "registration_date" in df.columns:
        df["reg_date"] = pd.to_datetime(df["registration_date"], errors="coerce")
        
    if {"credit_limit", "credit_limit_used_pct"}.issubset(df.columns):
        df["actual_debt"] = df["credit_limit"] * (df["credit_limit_used_pct"] / 100)
        df["available_credit"] = df["credit_limit"] * (1 - df["credit_limit_used_pct"] / 100)
        
    if "credit_limit_used_pct" in df.columns:
        df["risk_level"] = pd.cut(
            df["credit_limit_used_pct"],
            bins=[-1, 50, 80, 100],
            labels=["ต่ำ (0-50%)", "ปานกลาง (50-80%)", "สูง (80-100%)"]
        )
    return df

@lru_cache(maxsize=1)
def load_amount_data():
    df = load_data()
    return preprocess_amount(df)

# ==================================================
# Layout Helper
# ==================================================
def apply_amount_layout(fig, height=CHART_HEIGHT, right_margin=30, compact=False):
    fig.update_layout(
        autosize=False,
        height=height,
        uirevision=UI_REVISION_KEY,
        margin=dict(t=40 if not compact else 20, b=35, l=45, r=right_margin),
        paper_bgcolor=THEME["paper"],
        plot_bgcolor=THEME["bg_plot"],
        font=dict(family="Sarabun, sans-serif", color=THEME["text"], size=13),
        hoverlabel=dict(bgcolor="rgba(15,23,42,0.95)", font_color="white"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor=THEME["grid"])
    return fig

# ==================================================
# Charts Functions
# ==================================================

def chart_debt_health_donut(df):
    if "risk_level" not in df.columns: return go.Figure()
    risk_counts = df["risk_level"].value_counts().reset_index()
    risk_counts.columns = ["Level", "Count"]
    fig = px.pie(risk_counts, names="Level", values="Count", hole=0.45, color="Level",
                 color_discrete_map={"ต่ำ (0-50%)": THEME["success"], "ปานกลาง (50-80%)": THEME["warning"], "สูง (80-100%)": THEME["danger"]})
    fig.update_traces(texttemplate="<b>%{percent:.1%}</b>", textposition='inside')
    return apply_amount_layout(fig, compact=True)

def chart_avg_loan_by_branch(df):
    branch_col = "branch_no" if "branch_no" in df.columns else "branch_id"
    if branch_col not in df.columns or "actual_debt" not in df.columns: return go.Figure()
    avg_data = df.groupby(branch_col)["actual_debt"].mean().reset_index()
    avg_data[branch_col] = avg_data[branch_col].astype(str)
    fig = px.bar(avg_data, x=branch_col, y="actual_debt", color="actual_debt", color_continuous_scale="Blues", text_auto='.2s')
    fig.update_layout(coloraxis_showscale=False, xaxis=dict(type='category'))
    return apply_amount_layout(fig)

def chart_top_npl_branches(df):
    branch_col = "branch_no" if "branch_no" in df.columns else "branch_id"
    if "credit_limit_used_pct" not in df.columns: return go.Figure()
    temp_df = df.copy()
    temp_df["is_over_limit"] = (temp_df["credit_limit_used_pct"] > 90).astype(int)
    npl_data = temp_df.groupby(branch_col)["is_over_limit"].mean().reset_index()
    npl_data["npl_pct"] = npl_data["is_over_limit"] * 100
    fig = px.bar(npl_data, y=branch_col, x="npl_pct", orientation='h', color="npl_pct", color_continuous_scale="Reds", text_auto='.1f')
    fig.update_layout(coloraxis_showscale=False)
    return apply_amount_layout(fig)

def chart_occupation_debt(df):
    col_name = "career_name" if "career_name" in df.columns else "occupation"
    if col_name not in df.columns or "actual_debt" not in df.columns: return go.Figure()
    occ_data = df[df["actual_debt"] > 0].groupby(col_name)["actual_debt"].sum().reset_index()
    occ_data = occ_data.sort_values("actual_debt", ascending=True).tail(8)
    fig = px.bar(occ_data, y=col_name, x="actual_debt", color_discrete_sequence=[THEME["primary"]], text_auto='.2s')
    return apply_amount_layout(fig)

# ==================================================
# Table Component: รายบุคคล (ล่างสุด)
# ==================================================
def render_member_table(df):
    """ตารางแสดงข้อมูลรายบุคคลเพื่อวางไว้ล่างสุด"""
    # เตรียมข้อมูล (ดึงชื่อจาก SQL หรือตั้งชื่อหลอกถ้าไม่มี)
    df_table = df.copy()
    if "first_name" in df_table.columns and "last_name" in df_table.columns:
        df_table["fullname"] = df_table["first_name"] + " " + df_table["last_name"]
    else:
        df_table["fullname"] = "สมาชิก ID: " + df_table["customer_id"].astype(str)

    return dbc.Table(
        children=[
            html.Thead(children=[
                html.Tr(children=[
                    html.Th("ID", className="text-center"),
                    html.Th("ชื่อ-นามสกุล"),
                    html.Th("อาชีพ"),
                    html.Th("ยอดหนี้รวม", className="text-end"),
                    html.Th("การใช้สิทธิ์ (%)", className="text-center"),
                    html.Th("ระดับความเสี่ยง", className="text-center"),
                ])
            ]),
            html.Tbody(children=[
                html.Tr(children=[
                    html.Td(children=[str(row["customer_id"])], className="text-center"),
                    html.Td(children=[row["fullname"]]),
                    html.Td(children=[row.get("career_name", "-")]),
                    html.Td(children=[f"{row['actual_debt']:,.2f}"], className="text-end"),
                    html.Td(children=[f"{row['credit_limit_used_pct']:.1f}%"], className="text-center"),
                    html.Td(children=[
                        dbc.Badge(row["risk_level"], color="danger" if "สูง" in str(row["risk_level"]) else "warning" if "ปานกลาง" in str(row["risk_level"]) else "success")
                    ], className="text-center"),
                ]) for _, row in df_table.iterrows()
            ])
        ],
        bordered=True, hover=True, striped=True, responsive=True, className="mt-3 bg-white"
    )

# ==================================================
# Main Layout
# ==================================================
def amount_layout():
    df = load_amount_data()
    if df.empty: return dbc.Alert(children=["ไม่พบข้อมูลสำหรับการวิเคราะห์"], color="warning", className="mt-5")

    return dbc.Container(
        fluid=True,
        style={"padding": "20px 30px", "maxWidth": "1400px", "margin": "0 auto"},
        children=[
            html.H3(children=["Dashboard วิเคราะห์พอร์ตสินเชื่อและความเสี่ยง"], className="fw-bold mb-3"),
            render_amount_kpis(df),
            
            # Row 1: Donut & Occupation
            dbc.Row(children=[
                dbc.Col(children=[chart_card(chart_debt_health_donut(df), "สัดส่วนสุขภาพหนี้ (Debt Health)")], lg=6, md=12),
                dbc.Col(children=[chart_card(chart_occupation_debt(df), "ยอดหนี้รวมแยกตามกลุ่มอาชีพ (Top 8)")], lg=6, md=12),
            ], className="g-3 mb-3"),
            
            # Row 2: Branch Analysis
            dbc.Row(children=[
                dbc.Col(children=[chart_card(chart_avg_loan_by_branch(df), "ประสิทธิภาพ: ยอดหนี้เฉลี่ยต่อคนรายสาขา")], lg=6, md=12),
                dbc.Col(children=[chart_card(chart_top_npl_branches(df), "จุดเฝ้าระวัง: % ลูกค้าเสี่ยงสูงรายสาขา")], lg=6, md=12),
            ], className="g-3 mb-4"),

            # Row 3: ตารางรายบุคคล (วางไว้ล่างสุด)
            dbc.Row(children=[
                dbc.Col(children=[
                    dbc.Card(children=[
                        dbc.CardHeader(children=[html.Strong("รายละเอียดข้อมูลรายบุคคลและความเสี่ยง")]),
                        dbc.CardBody(children=[
                            html.Div(children=[render_member_table(df)], style={"maxHeight": "400px", "overflowY": "auto"})
                        ])
                    ], className="border-0 shadow-sm")
                ], width=12)
            ], className="g-3 mb-5"),
        ],
    )

layout = amount_layout()