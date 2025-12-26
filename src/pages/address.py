from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from ..data_manager import load_data
from ..components.kpi_cards import render_address_kpis

# ==================================================
# 1. Data Processing (ปรับให้เน้นที่อยู่)
# ==================================================
def get_processed_data():
    df = load_data()
    if df.empty: return df
    
    # ตรวจสอบและจัดการค่าว่างในส่วนที่อยู่
    geo_cols = ['province_name', 'district_area', 'sub_area']
    for col in geo_cols:
        if col in df.columns:
            df[col] = df[col].fillna("ไม่ระบุ")
            
    # คำนวณรายได้เผื่อใช้ในแผนภูมิกระจาย
    if "income" in df.columns:
        df["Income_Clean"] = pd.to_numeric(df["income"].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
    
    return df

# ==================================================
# 2. Chart Helpers (คงเดิมเพื่อความสวยงาม)
# ==================================================
def apply_layout(fig, title, legend_pos="top"):
    fig.update_layout(
        title=f"<b>{title}</b>",
        font=dict(family="Sarabun, sans-serif"),
        plot_bgcolor="rgba(245, 247, 250, 0.4)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=50, r=50, t=100, b=50),
        hovermode="closest"
    )
    if legend_pos == "top":
        fig.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    elif legend_pos == "right":
        fig.update_layout(showlegend=True, legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02))
    
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='rgba(0,0,0,0.05)')
    return fig

# ==================================================
# 3. Visual Charts (เปลี่ยนเป็น Geo-Specific)
# ==================================================

# 1. กราฟ Sunburst แสดงลำดับชั้นพื้นที่ (Province > District)
def chart_geo_hierarchy(df):
    # เลือก 5 จังหวัดแรกที่มีสมาชิกสูงสุด
    top_5_prov = df['province_name'].value_counts().nlargest(5).index
    sub_df = df[df['province_name'].isin(top_5_prov)]
    
    fig = px.sunburst(
        sub_df, path=['province_name', 'district_area'],
        color='province_name', color_discrete_sequence=px.colors.qualitative.Pastel
    )
    return apply_layout(fig, "1. สัดส่วนพื้นที่แยกตามจังหวัดและอำเภอ (Top 5)", legend_pos="none")

# 2. กราฟแท่งแสดง 10 อันดับตำบลที่มีสมาชิกสูงสุด
def chart_top_subdistricts(df):
    counts = df.groupby(['sub_area', 'province_name']).size().reset_index(name='count')
    counts = counts.sort_values('count', ascending=False).head(10)
    counts['label'] = counts['sub_area'] + " (" + counts['province_name'] + ")"
    
    fig = px.bar(
        counts, x='count', y='label', orientation='h',
        color='count', color_continuous_scale='Blues',
        text='count', labels={'count': 'จำนวนคน', 'label': 'ตำบล (จังหวัด)'}
    )
    fig.update_traces(textposition='outside')
    return apply_layout(fig, "2. 10 อันดับตำบลที่มีความหนาแน่นสูงสุด", legend_pos="none")

# 3. กราฟ TreeMap แสดงสัดส่วนรายได้แยกตามจังหวัด
def chart_income_treemap(df):
    fig = px.treemap(
        df, path=[px.Constant("ทุกจังหวัด"), 'province_name'], 
        values='Income_Clean',
        color='Income_Clean', color_continuous_scale='RdYlGn',
        labels={'Income_Clean': 'รายได้รวม', 'province_name': 'จังหวัด'}
    )
    return apply_layout(fig, "3. มูลค่ารายได้รวมแบ่งตามพื้นที่ (TreeMap)", legend_pos="none")

# 4. กราฟ Scatter ความหนาแน่นสมาชิก vs รายได้เฉลี่ยรายจังหวัด
def chart_geo_scatter(df):
    summary = df.groupby('province_name').agg({
        'member_id': 'count',
        'Income_Clean': 'mean'
    }).reset_index()
    summary.columns = ['จังหวัด', 'จำนวนสมาชิก', 'รายได้เฉลี่ย']
    
    fig = px.scatter(
        summary, x='จำนวนสมาชิก', y='รายได้เฉลี่ย', color='จังหวัด',
        size='จำนวนสมาชิก', text='จังหวัด', size_max=40,
        color_discrete_sequence=px.colors.qualitative.Vivid
    )
    fig.update_traces(textposition='top center')
    return apply_layout(fig, "4. วิเคราะห์จังหวัด: จำนวนคน vs รายได้เฉลี่ย", legend_pos="right")

# ==================================================
# 4. Main Layout
# ==================================================
def create_geographic_layout():
    df = get_processed_data()
    if df.empty: return dbc.Container(dbc.Alert("ไม่พบข้อมูลที่อยู่", color="danger", className="mt-5"))

    render_card = lambda fig: dbc.Card(
        dbc.CardBody(dcc.Graph(figure=fig, config={'displayModeBar': False})), 
        className="shadow-sm rounded-4 border-0 mb-4 overflow-hidden"
    )

    return dbc.Container(
        fluid=True,
        className="p-4 bg-light",
        children=[
            html.Div([
                html.H2("การวิเคราะห์เชิงพื้นที่ (Geographic Analysis)", className="fw-bold", style={"color": "#1e293b"}),
                html.P("เจาะลึกการกระจายตัวของสมาชิกและรายได้ระดับ จังหวัด/อำเภอ/ตำบล", className="text-muted")
            ], className="mb-4"),

            # ใช้ KPI ที่คุณเตรียมไว้สำหรับ Address
            render_address_kpis(df),

            dbc.Row([
                dbc.Col(render_card(chart_geo_hierarchy(df)), lg=6),
                dbc.Col(render_card(chart_top_subdistricts(df)), lg=6)
            ], className="g-4"),

            dbc.Row([
                dbc.Col(render_card(chart_income_treemap(df)), lg=6),
                dbc.Col(render_card(chart_geo_scatter(df)), lg=6)
            ], className="g-4"),
        ]
    )

layout = create_geographic_layout()