from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from ..data_manager import load_data
from ..components.kpi_cards import render_address_kpis

# ==================================================
# 1. Data Processing (Geo)
# ==================================================
def get_processed_data():
    df = load_data()
    if df.empty:
        return df

    geo_cols = ['province_name', 'district_area', 'sub_area']
    for col in geo_cols:
        if col in df.columns:
            df[col] = df[col].fillna("ไม่ระบุ")

    if "income" in df.columns:
        df["Income_Clean"] = (
            df["income"]
            .astype(str)
            .str.replace(",", "")
            .astype(float)
            .fillna(0)
        )

    return df


# ==================================================
# 2. Layout Helper (ล็อกความสูงทุกกราฟ)
# ==================================================
def apply_layout(fig, title, legend_pos="none"):
    fig.update_layout(
        title={
            'text': f"<b>{title}</b>",
            'font': {'size': 18, 'color': '#0f172a', 'family': 'Sarabun, sans-serif'},
            'x': 0.02,
            'xanchor': 'left'
        },
        plot_bgcolor="rgba(255, 255, 255, 0.02)",
        paper_bgcolor="rgba(255, 255, 255, 0)",
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
# 3. Charts (Geo)
# ==================================================

# 1) Sunburst: Province 
def chart_geo_hierarchy(df):
    top_5_prov = df['province_name'].value_counts().nlargest(5).index
    sub_df = df[df['province_name'].isin(top_5_prov)]

    fig = px.icicle(
        sub_df,
        path=[px.Constant("Top 5 จังหวัด"), 'province_name', 'district_area'],
        values=None, # หรือใส่ 'Income_Clean' ถ้าต้องการดูขนาดตามรายได้
        color='province_name',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_traces(marker_line_width=2)
    
    return apply_layout(fig, "1. โครงสร้างพื้นที่สมาชิก (Icicle Chart)")  


# 2) Top 10 Subdistricts
def chart_top_subdistricts(df):
    counts = (
        df.groupby(['sub_area', 'province_name'])
        .size()
        .reset_index(name='count')
        .sort_values('count', ascending=False)
        .head(10)
    )
    counts['label'] = counts['sub_area'] + " (" + counts['province_name'] + ")"

    fig = px.bar(
        counts,
        x='count',
        y='label',
        orientation='h',
        color='count',
        color_continuous_scale='Blues',
        text='count',
        labels={'count': 'จำนวนคน', 'label': 'ตำบล (จังหวัด)'},
    )
    fig.update_traces(textposition='outside')
    return apply_layout(fig, "2. 10 อันดับตำบลที่มีความหนาแน่นสูงสุด")


# 3) TreeMap รายได้รวม
def chart_income_treemap(df):
    fig = px.treemap(
        df,
        path=[px.Constant("ทุกจังหวัด"), 'province_name'],
        values='Income_Clean',
        color='Income_Clean',
        color_continuous_scale='RdYlGn',
        labels={'Income_Clean': 'รายได้รวม', 'province_name': 'จังหวัด'},
    )
    return apply_layout(fig, "3. มูลค่ารายได้รวมแบ่งตามพื้นที่ (TreeMap)")


# 4) Scatter: Members vs Avg Income
def chart_geo_scatter(df):
    summary = (
        df.groupby('province_name')
        .agg(
            member_count=('member_id', 'count'),
            avg_income=('Income_Clean', 'mean'),
        )
        .reset_index()
    )

    fig = px.scatter(
        summary,
        x='member_count',
        y='avg_income',
        color='province_name',
        size='member_count',
        text='province_name',
        size_max=40,
        color_discrete_sequence=px.colors.qualitative.Vivid,
        labels={
            'member_count': 'จำนวนสมาชิก',
            'avg_income': 'รายได้เฉลี่ย',
        },
    )
    fig.update_traces(textposition='top center')
    return apply_layout(fig, "4. วิเคราะห์จังหวัด: จำนวนคน vs รายได้เฉลี่ย", legend_pos="right")


# ==================================================
# 4. Main Layout
# ==================================================
def create_geographic_layout():
    df = get_processed_data()
    if df.empty:
        return dbc.Container(
            dbc.Alert("ไม่พบข้อมูลที่อยู่", color="danger", className="mt-5")
        )

    def render_card(fig):
        return dbc.Card(
            dbc.CardBody(
                dcc.Graph(
                    figure=fig,
                    config={'displayModeBar': False},
                    style={"height": "360px"},  # 🔴 Graph เท่ากัน
                )
            ),
            className="shadow-lg rounded-4 border-0 mb-4",
            style={"height": "420px"},      # 🔴 Card เท่ากัน
        )

    return dbc.Container(
        fluid=True,
        className="p-4 bg-light",
        children=[
            html.Div(
                [
                    html.H2(
                        "การวิเคราะห์เชิงพื้นที่ (Geographic Analysis)",
                        className="fw-bold text-dark",
                    ),
                    html.P(
                        "เจาะลึกการกระจายตัวของสมาชิกและรายได้ระดับ จังหวัด / อำเภอ / ตำบล",
                        className="text-muted",
                    ),
                ],
                className="mb-4",
            ),

            render_address_kpis(df),

            dbc.Row(
                [
                    dbc.Col(render_card(chart_geo_hierarchy(df)), lg=6),
                    dbc.Col(render_card(chart_top_subdistricts(df)), lg=6),
                ],
                className="g-4 align-items-stretch",
            ),

            dbc.Row(
                [
                    dbc.Col(render_card(chart_income_treemap(df)), lg=6),
                    dbc.Col(render_card(chart_geo_scatter(df)), lg=6),
                ],
                className="g-4 align-items-stretch",
            ),
        ],
    )


layout = create_geographic_layout()
    