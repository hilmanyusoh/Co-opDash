from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from ..data_manager import load_data
from ..pages import addressdash 


# Strategic Insight Functions

def render_strategic_insights(df):
    top_prov = df['province_name'].mode()[0] if "province_name" in df.columns and not df['province_name'].empty else "N/A"
    top_dist = df['district_area'].mode()[0] if "district_area" in df.columns and not df['district_area'].empty else "N/A"
    top_post = df['postal_code'].mode()[0] if "postal_code" in df.columns and not df['postal_code'].empty else "N/A"

    return dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("พื้นที่ยุทธศาสตร์หลัก", className="text-muted small"),
                html.H3(f"จ. {top_prov}", className="text-primary fw-bold"),
                html.Div("ฐานลูกค้าหนาแน่นที่สุด", className="small text-secondary")
            ])
        ], className="shadow-sm border-start border-primary border-4"), lg=4),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("อำเภอเป้าหมายขยายบริการ", className="text-muted small"),
                html.H3(top_dist, className="text-success fw-bold"),
                html.Div("พื้นที่ที่มีศักยภาพสูงสุด", className="small text-secondary")
            ])
        ], className="shadow-sm border-start border-success border-4"), lg=4),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("ศูนย์กลางการสื่อสาร", className="text-muted small"),
                html.H3(top_post, className="text-warning fw-bold"),
                html.Div("รหัสไปรษณีย์เป้าหมายการตลาด", className="small text-secondary")
            ])
        ], className="shadow-sm border-start border-warning border-4"), lg=4),
    ], className="mb-4 g-3")

# ==================================================
# Visual Chart Functions
# ==================================================

def create_strategic_map(df):
    """สร้างแผนที่จุดยุทธศาสตร์ (Bubble Map)"""
    if "province_name" not in df.columns:
        return px.scatter_mapbox(title="ไม่พบข้อมูลพิกัด")

    # สรุปข้อมูลรายจังหวัด
    df_map = df.groupby('province_name').size().reset_index(name='จำนวนสมาชิก')
    
    # พิกัดตัวแทนจังหวัดหลัก (สำหรับการแสดงผลเบื้องต้น)
    coords = {
        'กรุงเทพมหานคร': [13.7563, 100.5018], 'นนทบุรี': [13.8591, 100.4914],
        'ปทุมธานี': [14.0208, 100.5250], 'สมุทรปราการ': [13.5991, 100.5967],
        'ชลบุรี': [13.3611, 100.9847], 'เชียงใหม่': [18.7883, 98.9853],
        'ขอนแก่น': [16.4322, 102.8236], 'สงขลา': [7.1898, 100.5954]
    }
    
    df_map['lat'] = df_map['province_name'].map(lambda x: coords.get(x, [13.7367, 100.5231])[0])
    df_map['lon'] = df_map['province_name'].map(lambda x: coords.get(x, [13.7367, 100.5231])[1])

    fig = px.scatter_mapbox(
        df_map, 
        lat="lat", 
        lon="lon", 
        size="จำนวนสมาชิก", 
        color="จำนวนสมาชิก",
        hover_name="province_name", 
        size_max=40, 
        zoom=5,
        color_continuous_scale=px.colors.sequential.deep, # แก้ Deep เป็น deep
        title="<b>Market Presence Map: การกระจายตัวเชิงภูมิศาสตร์</b>"
    )
    fig.update_layout(
        mapbox_style="carto-positron", 
        margin={"r":0,"t":40,"l":0,"b":0},
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig

def create_province_chart(df):
    df_prov = df["province_name"].value_counts().reset_index()
    df_prov.columns = ["จังหวัด", "จำนวนสมาชิก"]
    fig = px.bar(
        df_prov.head(10), x="จำนวนสมาชิก", y="จังหวัด", orientation="h",
        title="<b>Top 10 จังหวัดที่มีสมาชิกสูงสุด</b>",
        color="จำนวนสมาชิก", color_continuous_scale="Blues", text_auto=True
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis={'categoryorder':'total ascending'})
    return fig

def create_district_chart(df):
    df_dist = df["district_area"].value_counts().reset_index().head(10)
    df_dist.columns = ["อำเภอ", "จำนวนสมาชิก"]
    fig = px.pie(
        df_dist, names="อำเภอ", values="จำนวนสมาชิก", hole=0.4,
        title="<b>สัดส่วนสมาชิกรายอำเภอ (Market Share)</b>",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
    return fig

# ==================================================
# Main Layout
# ==================================================

def create_address_layout():
    df = load_data()
    if df.empty:
        return dbc.Container(dbc.Alert("ไม่พบข้อมูลสำหรับการวิเคราะห์", color="warning", className="mt-5 text-center"))

    return dbc.Container(
        fluid=True,
        className="p-4",
        children=[
            html.Div([
                html.H2("Address & Geospatial Intelligence", className="fw-bold text-primary"),
                html.P("วิเคราะห์ข้อมูลเชิงพื้นที่เพื่อวางแผนยุทธศาสตร์สาขาและการตลาด", className="text-muted"),
            ], className="mb-4"),

            render_strategic_insights(df),

            # แถวของแผนที่
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            dcc.Graph(figure=create_strategic_map(df), style={"height": "450px"}, config={"displayModeBar": False})
                        ]),
                        className="shadow-sm border-0 mb-4"
                    ), width=12
                )
            ]),

            # แถวของกราฟแท่งและกราฟวงกลม
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=create_province_chart(df))), className="shadow-sm border-0 mb-4"), lg=7),
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=create_district_chart(df))), className="shadow-sm border-0 mb-4"), lg=5),
            ], className="g-4"),

            # ตารางสรุปข้อมูล
            html.Div([
                html.H5("พื้นที่ยุทธศาสตร์ระดับตำบล-อำเภอ (Top 10 Cluster)", className="mt-4 mb-3 fw-bold"),
                dbc.Table.from_dataframe(
                    df.groupby(['province_name', 'district_area', 'sub_area']).size().reset_index(name='จำนวนสมาชิก')
                    .sort_values('จำนวนสมาชิก', ascending=False).head(10),
                    striped=True, bordered=False, hover=True, className="bg-white shadow-sm align-middle text-center",
                    style={"borderRadius": "10px", "overflow": "hidden"}
                )
            ])
        ]
    )

layout = create_address_layout()