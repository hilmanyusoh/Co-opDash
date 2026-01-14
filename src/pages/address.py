from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from ..data_manager import load_data
from ..components.kpi_cards import render_address_kpis

# ==================================================
# Config
# ==================================================
CHART_HEIGHT = 340
COLOR_PALETTE = px.colors.qualitative.Set2

# ==================================================
# 1. Data Processing
# ==================================================
def get_processed_data():
    df = load_data()
    if df.empty:
        return df

    for col in ["province_name", "district_area", "sub_area"]:
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

    if "age" in df.columns and "Age_Group" not in df.columns:
        df["Age_Group"] = pd.cut(
            df["age"],
            bins=[0, 25, 35, 45, 55, 65, 120],
            labels=["0-25", "26-35", "36-45", "46-55", "56-65", "65+"]
        ).astype(str)

    return df

# ==================================================
# 2. Layout Helper
# ==================================================
def apply_layout(fig, title="", height=CHART_HEIGHT, show_legend=True):
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            x=0.02,
            xanchor="left"
        ),
        height=height,
        margin=dict(t=80, b=50, l=60, r=30),
        plot_bgcolor="rgba(255,255,255,0.02)",
        paper_bgcolor="rgba(255,255,255,0)",
        font=dict(
            family="Sarabun, sans-serif",
            size=13,
            color="#334155"
        ),
        showlegend=show_legend,
        legend=dict(
            orientation="h",
            y=-0.2,
            x=0.5,
            xanchor="center"
        ),
        hovermode="closest"
    )

    fig.update_xaxes(
        showgrid=False,
        showline=True,
        linecolor="#E2E8F0"
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(203,213,225,0.4)",
        showline=True,
        linecolor="#E2E8F0"
    )

    return fig

# ==================================================
# 3. Charts
# ==================================================
def chart_province_age_distribution(df):
    top_6 = df["province_name"].value_counts().nlargest(6).index
    sub = df[df["province_name"].isin(top_6)].copy()

    summary = (
        sub.groupby(["province_name", "Age_Group"])
        .size()
        .reset_index(name="count")
    )

    fig = px.bar(
        summary,
        x="Age_Group",
        y="count",
        color="Age_Group",
        facet_col="province_name",
        facet_col_wrap=3,
        color_discrete_sequence=COLOR_PALETTE
    )

    fig.for_each_annotation(
        lambda a: a.update(
            text=f"<b>{a.text.split('=')[-1]}</b>",
            font=dict(size=12)
        )
    )

    fig.update_traces(
        marker=dict(line=dict(width=1, color="white")),
        hovertemplate="<b>%{x}</b><br>จำนวน: %{y:,} คน<extra></extra>"
    )

    fig.update_layout(
        height=520,
        showlegend=False
    )

    return apply_layout(
        fig,
        "สัดส่วนประชากรแยกตามช่วงอายุ (Top 6 จังหวัด)",
        height=520,
        show_legend=False
    )

# def chart_province_career(df):
#     top_5 = df["province_name"].value_counts().nlargest(5).index
#     sub = df[df["province_name"].isin(top_5)].copy()

#     top_career = sub["career_name"].value_counts().nlargest(5).index
#     sub["career_group"] = sub["career_name"].apply(
#         lambda x: x if x in top_career else "อื่นๆ"
#     )

#     summary = (
#         sub.groupby(["province_name", "career_group"])
#         .size()
#         .reset_index(name="count")
#     )

#     fig = px.bar(
#         summary,
#         x="province_name",
#         y="count",
#         color="career_group",
#         color_discrete_sequence=COLOR_PALETTE
#     )

#     # ✅ ตรงนี้คือจุดที่ถูกต้อง
#     fig.update_layout(
#         barmode="stack",
#         barnorm="percent"
#     )

#     fig.update_traces(
#         hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y:.1f}%<extra></extra>",
#         marker=dict(line=dict(width=1, color="white"))
#     )

#     fig.update_yaxes(title="สัดส่วน (%)", tickformat=".0f")
#     fig.update_xaxes(title="", showgrid=False)

#     return apply_layout(fig, "วิเคราะห์สัดส่วนอาชีพรายจังหวัด (100%)")

# def chart_income_gap_analysis(df):
#     summary = (
#         df.groupby("province_name")["Income_Clean"]
#         .agg(["mean", "median"])
#         .nlargest(8, "mean")
#         .reset_index()
#     )

#     fig = px.bar(
#         summary,
#         x="province_name",
#         y=["mean", "median"],
#         barmode="group",
#         color_discrete_map={
#             "mean": "#3B82F6",
#             "median": "#10B981"
#         }
#     )

#     fig.for_each_trace(lambda t: t.update(
#         name="ค่าเฉลี่ย" if t.name == "mean" else "ค่ากลาง",
#         hovertemplate="<b>%{x}</b><br>%{y:,.0f} บาท<extra></extra>"
#     ))

#     fig.update_yaxes(title="บาท")

#     return apply_layout(fig, "ช่องว่างรายได้: ค่าเฉลี่ย vs ค่ากลาง")

# def chart_top_subdistricts(df):
#     counts = (
#         df.groupby(["sub_area", "province_name"])
#         .size()
#         .reset_index(name="count")
#         .sort_values("count", ascending=False)
#         .head(10)
#     )

#     counts["label"] = counts["sub_area"] + " (" + counts["province_name"] + ")"
#     counts = counts.sort_values("count")

#     fig = go.Figure(
#         go.Bar(
#             y=counts["label"],
#             x=counts["count"],
#             orientation="h",
#             text=[f"{v:,} คน" for v in counts["count"]],
#             textposition="inside",
#             marker=dict(
#                 color=counts["count"],
#                 colorscale="Blues",
#                 line=dict(color="white", width=2)
#             )
#         )
#     )

#     fig.update_xaxes(title="จำนวนคน")

#     return apply_layout(fig, "10 อันดับตำบลที่มีความหนาแน่นสูงสุด", show_legend=False)

# ==================================================
# 4. Card Helper
# ==================================================
def card(fig):
    return dbc.Card(
        dbc.CardBody(
            dcc.Graph(
                figure=fig,
                config={"displayModeBar": False},
                style={"height": "100%"}
            ),
            style={"padding": "18px", "overflow": "hidden"}
        ),
        className="shadow-sm rounded-3 border-0 mb-3"
    )

# ==================================================
# 5. Main Layout
# ==================================================
def create_geographic_layout():
    df = get_processed_data()
    if df.empty:
        return dbc.Alert("ไม่พบข้อมูล", color="warning")

    return dbc.Container(
        fluid=True,
        style={"padding": "20px 30px", "maxWidth": "1400px"},
        children=[
            html.H3("ข้อมูลเชิงพื้นที่", className="fw-bold mb-3"),
            render_address_kpis(df),

            dbc.Row([dbc.Col(card(chart_province_age_distribution(df)), xs=12)]),

            # dbc.Row(
            #     [
            #         dbc.Col(card(chart_province_career(df)), lg=6),
            #         dbc.Col(card(chart_income_gap_analysis(df)), lg=6),
            #     ],
            #     className="g-3"
            # ),

            # dbc.Row(
            #     [dbc.Col(card(chart_top_subdistricts(df)), lg=6)],
            #     className="g-3"
            # )
        ],
    )

layout = create_geographic_layout()
