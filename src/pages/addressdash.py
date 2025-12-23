from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from ..data_manager import load_data

# ==================================================
# Visual Chart Functions
# ==================================================

def create_province_chart(df):
    """วิเคราะห์ 10 อันดับจังหวัดที่มีสมาชิกสูงสุด"""
    if "province_name" not in df.columns:
        return px.bar(title="ไม่พบข้อมูลจังหวัด")
    
    prov_counts = df["province_name"].value_counts().head(10).reset_index()
    prov_counts.columns = ["จังหวัด", "จำนวนสมาชิก"]
    
    fig = px.bar(
        prov_counts.sort_values("จำนวนสมาชิก", ascending=True),
        x="จำนวนสมาชิก", y="จังหวัด",
        orientation="h",
        text_auto=True,
        title="<b>Top 10 จังหวัดยุทธศาสตร์</b>",
        color="จำนวนสมาชิก",
        color_continuous_scale="Blues"
    )
    fig.update_layout(coloraxis_showscale=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def create_district_pie(df):
    """วิเคราะห์สัดส่วนสมาชิกรายอำเภอ (Top 10)"""
    if "district_area" not in df.columns:
        return px.pie(title="ไม่พบข้อมูลอำเภอ/เขต")
    
    dist_counts = df["district_area"].value_counts().head(10).reset_index()
    dist_counts.columns = ["อำเภอ_เขต", "จำนวน"]
    
    fig = px.pie(
        dist_counts, names="อำเภอ_เขต", values="จำนวน",
        hole=0.5,
        title="<b>สัดส่วนสมาชิก 10 อันดับอำเภอ/เขต</b>",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"))
    return fig

def create_income_by_province(df):
    """วิเคราะห์รายได้เฉลี่ยสมาชิกแยกตามจังหวัด (Top 10)"""
    if "province_name" not in df.columns or "Income_Clean" not in df.columns:
        return px.bar(title="ข้อมูลไม่เพียงพอ")
        
    prov_income = df.groupby("province_name")["Income_Clean"].mean().sort_values(ascending=False).head(10).reset_index()
    prov_income.columns = ["จังหวัด", "รายได้เฉลี่ย"]
    
    fig = px.bar(
        prov_income, x="จังหวัด", y="รายได้เฉลี่ย",
        title="<b>10 จังหวัดที่มีสมาชิกรายได้เฉลี่ยสูงสุด</b>",
        color="รายได้เฉลี่ย",
        color_continuous_scale="Tropic"
    )
    fig.update_layout(coloraxis_showscale=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

# ==================================================
# Main Layout
# ==================================================

def create_address_layout():
    df = load_data()
    
    if df.empty:
        return dbc.Container(dbc.Alert("ไม่พบข้อมูลที่อยู่สมาชิก", color="warning", className="mt-5 text-center"))

    # สถิติสรุป (Insights)
    total_provinces = df["province_name"].nunique() if "province_name" in df.columns else 0
    top_province = df["province_name"].mode()[0] if "province_name" in df.columns else "N/A"
    top_postal = df["postal_code"].mode()[0] if "postal_code" in df.columns else "N/A"

    return dbc.Container(
        fluid=True,
        className="p-4 bg-light",
        children=[
            html.Div([
                html.H2("Geospatial Member Intelligence", className="fw-bold text-dark"),
                html.P("วิเคราะห์การกระจายตัวของสมาชิกเชิงพื้นที่เพื่อวางแผนขยายจุดบริการ", className="text-muted"),
            ], className="mb-4"),

            # แถว KPI
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.Small("จำนวนจังหวัดที่ครอบคลุม", className="text-muted"),
                        html.H4(f"{total_provinces} จังหวัด", className="text-primary fw-bold mb-0")
                    ])
                ], className="shadow-sm border-0 border-top border-primary border-4"), lg=4),
                
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.Small("จังหวัดที่มีสมาชิกมากที่สุด", className="text-muted"),
                        html.H4(top_province, className="text-success fw-bold mb-0")
                    ])
                ], className="shadow-sm border-0 border-top border-success border-4"), lg=4),
                
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.Small("รหัสไปรษณีย์ที่มีความหนาแน่นสูง", className="text-muted"),
                        html.H4(top_postal, className="text-info fw-bold mb-0")
                    ])
                ], className="shadow-sm border-0 border-top border-info border-4"), lg=4),
            ], className="mb-4 g-3"),

            # ส่วนกราฟ
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=create_province_chart(df), config={"displayModeBar": False})), className="shadow-sm border-0"), lg=7),
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=create_district_pie(df), config={"displayModeBar": False})), className="shadow-sm border-0"), lg=5),
            ], className="g-4 mb-4"),

            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=create_income_by_province(df), config={"displayModeBar": False})), className="shadow-sm border-0"), width=12),
            ]),

            # ตารางรายละเอียดพื้นที่แยกตามสาขา
            dbc.Card([
                dbc.CardHeader(html.H5("สรุปจำนวนสมาชิกแยกตามสาขาและจังหวัด", className="mb-0 fw-bold")),
                dbc.CardBody([
                    dbc.Table.from_dataframe(
                        df.groupby(["branch_no", "province_name"]).size().reset_index(name="จำนวนสมาชิก")
                        .sort_values(["branch_no", "จำนวนสมาชิก"], ascending=[True, False]).head(10),
                        striped=True, hover=True, borderless=True, className="align-middle text-center mb-0"
                    )
                ])
            ], className="shadow-sm border-0 mb-4")
        ]
    )

layout = create_address_layout()