from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from ..data_manager import load_data
from ..components.kpi_cards import render_address_kpis

CHART_HEIGHT = 340

# ==================================================
# 1. Data Processing (Geo)
# ==================================================
def get_processed_data():
    df = load_data()
    if df.empty:
        return df

    geo_cols = ["province_name", "district_area", "sub_area"]
    for col in geo_cols:
        if col in df.columns:
            df[col] = df[col].fillna("ไม่ระบุ")

    if "income" in df.columns:
        df["Income_Clean"] = (
            df["income"]
            .astype(str)
            .str.replace(",", "")
            .pipe(pd.to_numeric, errors="coerce")
            .fillna(0)
        )

    return df

# ==================================================
# 2. Layout Helper (❌ ไม่กำหนด fontSize)
# ==================================================
def apply_layout(fig, height=CHART_HEIGHT):
    fig.update_layout(
        height=height,
        margin=dict(t=0, b=40, l=50, r=30),
        plot_bgcolor="rgba(248, 250, 252, 0.3)",
        paper_bgcolor="rgba(255, 255, 255, 0)",
        font=dict(
            family="Sarabun, sans-serif",
            color="#334155"
        ),
    )
    return fig

# ==================================================
# 3. Charts
# ==================================================
def chart_province_age_distribution(df):
    top_6_prov = df["province_name"].value_counts().nlargest(6).index
    df_sub = df[df["province_name"].isin(top_6_prov)].copy()

    df_sub["Age_Group"] = df_sub["Age_Group"].astype(str)
    age_order = sorted(df_sub["Age_Group"].unique())

    summary = (
        df_sub.groupby(["province_name", "Age_Group"])
        .size()
        .reset_index(name="member_count")
    )

    fig = px.bar(
        summary,
        x="Age_Group",
        y="member_count",
        color="Age_Group",
        facet_col="province_name",
        facet_col_wrap=3,
        category_orders={"Age_Group": age_order},
    )

    fig.for_each_annotation(
        lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>")
    )

    fig.update_yaxes(showticklabels=False, showgrid=False, title="")
    fig.update_xaxes(title="")

    return apply_layout(fig)

def chart_province_career(df):
    top_5_prov = df["province_name"].value_counts().nlargest(5).index
    sub_df = df[df["province_name"].isin(top_5_prov)].copy()

    top_careers = sub_df["career_name"].value_counts().nlargest(5).index
    sub_df["career_group"] = sub_df["career_name"].apply(
        lambda x: x if x in top_careers else "อื่นๆ"
    )

    summary = (
        sub_df.groupby(["province_name", "career_group"])
        .size()
        .reset_index(name="count")
    )

    fig = px.bar(
        summary,
        x="province_name",
        y="count",
        color="career_group",
        labels={
            "province_name": "จังหวัด",
            "count": "จำนวนคน",
            "career_group": "อาชีพ",
        },
    )

    fig.update_layout(
        barmode="stack",
        barnorm="percent",
    )

    fig.update_yaxes(
        title="สัดส่วน (%)",
        tickformat=".0f"
    )

    return apply_layout(fig)

def chart_income_gap_analysis(df):
    summary = (
        df.groupby("province_name")["Income_Clean"]
        .agg(["mean", "median"])
        .nlargest(8, "mean")
        .reset_index()
    )

    fig = px.bar(
        summary,
        x="province_name",
        y=["mean", "median"],
        barmode="group",
    )

    fig.update_yaxes(
        title="จำนวนเงิน (บาท)",
        tickformat=","
    )

    return apply_layout(fig)

def chart_top_subdistricts(df):
    counts = (
        df.groupby(["sub_area", "province_name"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .head(10)
    )

    counts["label"] = counts["sub_area"] + " (" + counts["province_name"] + ")"

    fig = px.bar(
        counts,
        y="label",
        x="count",
        orientation="h",
    )

    fig.update_xaxes(title="จำนวนคน")
    fig.update_yaxes(title="ตำบล (จังหวัด)")

    return apply_layout(fig)

# ==================================================
# 4. Main Layout
# ==================================================
def create_geographic_layout():
    df = get_processed_data()
    if df.empty:
        return dbc.Container(
            dbc.Alert("ไม่พบข้อมูลที่อยู่", color="warning", className="mt-5")
        )

    def card(fig, title):
        return dbc.Card(
            dbc.CardBody(
                [
                    html.H6(title, className="fw-bold mb-2 chart-title"),
                    dcc.Graph(
                        figure=fig,
                        config={"displayModeBar": False},
                    ),
                ],
                style={"padding": "14px"},
            ),
            className="shadow-sm rounded-3 border-0 mb-3",
        )

    return dbc.Container(
        fluid=True,
        style={
            "padding": "20px 30px",
            "maxWidth": "1400px",
            "margin": "0 auto",
        },
        children=[
            html.H3(
                "การวิเคราะห์เชิงพื้นที่",
                className="page-title fw-bold mb-3"
            ),

            render_address_kpis(df),

            dbc.Row(
                [
                    dbc.Col(
                        card(
                            chart_province_age_distribution(df),
                            "สัดส่วนประชากรแยกตามช่วงอายุ (Top 6 จังหวัด)",
                        ),
                        xs=12,
                    )
                ],
                className="mb-3",
            ),

            dbc.Row(
                [
                    dbc.Col(
                        card(
                            chart_province_career(df),
                            "วิเคราะห์สัดส่วนอาชีพรายจังหวัด (100%)",
                        ),
                        xs=12,
                        lg=6,
                    ),
                    dbc.Col(
                        card(
                            chart_income_gap_analysis(df),
                            "ช่องว่างรายได้: ค่าเฉลี่ย vs ค่าคนส่วนใหญ่",
                        ),
                        xs=12,
                        lg=6,
                    ),
                ],
                className="g-3 mb-3",
            ),

            dbc.Row(
                [
                    dbc.Col(
                        card(
                            chart_top_subdistricts(df),
                            "10 อันดับตำบลที่มีความหนาแน่นสูงสุด",
                        ),
                        xs=12,
                        lg=6,
                    )
                ],
                className="g-3",
            ),
        ],
    )

layout = create_geographic_layout()
