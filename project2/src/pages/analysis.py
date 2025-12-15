# src/pages/analysis.py

from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

# Imports จากภายใน src/
from ..data_manager import load_data
from ..components.kpi_cards import render_kpi_cards



# ==================================================
# Helper Functions: Charts
# ==================================================

def create_branch_chart(df):
    if "Branch_code" not in df.columns or df["Branch_code"].isnull().all():
        return px.bar(title="1. ไม่พบข้อมูล Branch_code")

    top10 = df["Branch_code"].value_counts().nlargest(10).index
    df_top = df[df["Branch_code"].isin(top10)]

    fig = px.pie(
        df_top,
        names="Branch_code",
        title="1. สัดส่วนจำนวนสมาชิกตามสาขา (Top 10)",
        hole=0.35,
        template="plotly_dark"
    )
    fig.update_traces(textinfo="percent+label")
    fig.update_layout(title_x=0.5)
    return fig


def create_age_distribution_chart(df):
    if "Age_group" not in df.columns or df["Age_group"].isnull().all():
        return px.bar(title="2. ไม่พบข้อมูล Age_group")

    df_age = df["Age_group"].value_counts().reset_index()
    df_age.columns = ["Age_group", "จำนวนสมาชิก"]

    fig = px.bar(
        df_age,
        x="Age_group",
        y="จำนวนสมาชิก",
        color="Age_group",
        title="2. จำนวนสมาชิกแบ่งตามช่วงอายุ",
        template="plotly_dark"
    )
    fig.update_layout(title_x=0.5)
    return fig


def create_income_by_career_chart(df):

    if "Income_Clean" not in df.columns or "Career" not in df.columns:
        return px.bar(title="3. ไม่พบข้อมูล Income / Career")

    df_prof = (
        df.dropna(subset=["Income_Clean", "Career"])
        .groupby("Career", as_index=False)["Income_Clean"]
        .mean()
        .sort_values("Income_Clean", ascending=False)
        .head(10)
    )

    fig = px.bar(
        df_prof,
        x="Income_Clean",
        y="Career",
        orientation="h",
        title="3. 10 อันดับอาชีพที่มีรายได้เฉลี่ยสูงสุด",
        labels={"Income_Clean": "รายได้เฉลี่ย (บาท)"},
        template="plotly_dark"
    )

    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        xaxis_tickformat=",",
        title_x=0.5
    )

    return fig



def create_approval_time_chart(df):
    if "Approval_days" not in df.columns or df["Approval_days"].isnull().all():
        return px.bar(title="4. ไม่พบข้อมูล Approval_days")

    fig = px.histogram(
        df,
        x="Approval_days",
        nbins=20,
        title="4. การกระจายตัวของระยะเวลาอนุมัติ (วัน)",
        template="plotly_dark"
    )
    fig.update_layout(title_x=0.5)
    return fig


# ==================================================
# Layout
# ==================================================

def create_analysis_layout():
    df = load_data()

    if df.empty:
        return dbc.Container(
            dbc.Alert(
                [
                    html.H4("❌ ไม่พบข้อมูลสำหรับการวิเคราะห์", className="alert-heading"),
                    html.P("กรุณาตรวจสอบการเชื่อมต่อ PostgreSQL และตาราง members"),
                ],
                color="danger",
                className="mt-5 rounded-3",
            ),
            fluid=True,
        )

    fig_branch = create_branch_chart(df)
    fig_age = create_age_distribution_chart(df)
    fig_income = create_income_by_career_chart(df)
    fig_approval = create_approval_time_chart(df)

    return dbc.Container(
        fluid=True,
        className="py-5",
        children=[
            # Header
            html.Div(
                [
                    html.H1(
                        "Dashboard วิเคราะห์ข้อมูลสมาชิก",
                        className="text-white text-center fw-bolder mb-0",
                    ),
                    html.P(
                        "ภาพรวมและแนวโน้มที่สำคัญของข้อมูลสมาชิก",
                        className="text-white-50 text-center mb-0",
                    ),
                ],
                className="py-4 px-4 mb-5 rounded-4",
                style={
                    "background": "linear-gradient(90deg, #007bff 0%, #00bcd4 100%)",
                    "boxShadow": "0 4px 15px rgba(0,123,255,.5)",
                },
            ),

            # KPI
            render_kpi_cards(df),

            html.Hr(className="my-5"),

            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=fig_branch), lg=6),
                    dbc.Col(dcc.Graph(figure=fig_age), lg=6),
                ],
                className="g-4",
            ),

            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=fig_income), lg=6),
                    dbc.Col(dcc.Graph(figure=fig_approval), lg=6),
                ],
                className="g-4 mt-2",
            ),
        ],
    )


layout = create_analysis_layout()


# ==================================================
# Callbacks
# ==================================================

def register_callbacks(app):
    pass
