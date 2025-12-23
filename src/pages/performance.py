from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from ..data_manager import load_data

# ==================================================
# Analysis Functions
# ==================================================

def create_branch_performance_bar(df):
    """เปรียบเทียบรายได้รวมแยกตามสาขา"""
    if "branch_no" not in df.columns or "Income_Clean" not in df.columns:
        return px.bar(title="ไม่พบข้อมูลรายได้รายสาขา")
    
    branch_stats = df.groupby("branch_no")["Income_Clean"].sum().reset_index()
    branch_stats.columns = ["สาขา", "รายได้รวม"]
    branch_stats["สาขา"] = "สาขาที่ " + branch_stats["สาขา"].astype(str)

    fig = px.bar(
        branch_stats, x="สาขา", y="รายได้รวม",
        text_auto='.2s',
        title="<b>ประสิทธิภาพการสร้างรายได้แยกตามสาขา (Total Income)</b>",
        color="รายได้รวม",
        color_continuous_scale="Reds"
    )
    fig.update_layout(coloraxis_showscale=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def create_member_growth_by_branch(df):
    """วิเคราะห์การเพิ่มขึ้นของสมาชิกในแต่ละสาขาแยกตามปี"""
    df['reg_year'] = pd.to_datetime(df['registration_date']).dt.year
    growth = df.groupby(['reg_year', 'branch_no']).size().reset_index(name='new_members')
    growth['branch_no'] = "สาขา " + growth['branch_no'].astype(str)

    fig = px.line(
        growth, x="reg_year", y="new_members", color="branch_no",
        title="<b>แนวโน้มการหาสมาชิกใหม่รายสาขา (Growth Trend)</b>",
        markers=True
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def create_efficiency_scatter(df):
    """วิเคราะห์ความคุ้มค่า: จำนวนสมาชิก vs รายได้เฉลี่ย"""
    eff = df.groupby("branch_no").agg({
        "member_id": "count",
        "Income_Clean": "mean"
    }).reset_index()
    eff.columns = ["สาขา", "จำนวนสมาชิก", "รายได้เฉลี่ย"]

    fig = px.scatter(
        eff, x="จำนวนสมาชิก", y="รายได้เฉลี่ย",
        size="จำนวนสมาชิก", color="สาขา",
        text="สาขา",
        title="<b>Matrix วิเคราะห์ประสิทธิภาพ (Member Density vs Avg Income)</b>",
        labels={"จำนวนสมาชิก": "ปริมาณสมาชิก (ราย)", "รายได้เฉลี่ย": "คุณภาพรายได้ (บาท)"}
    )
    fig.update_traces(textposition='top center')
    return fig

# ==================================================
# Main Layout
# ==================================================

def create_performance_layout():
    df = load_data()
    
    if df.empty:
        return dbc.Container(dbc.Alert("ไม่พบข้อมูลสำหรับการวิเคราะห์ประสิทธิภาพ", color="danger", className="mt-5 text-center"))

    # คำนวณ KPIs
    best_branch = df.groupby("branch_no")["Income_Clean"].sum().idxmax()
    avg_income_all = df["Income_Clean"].mean()
    total_revenue = df["Income_Clean"].sum()

    return dbc.Container(
        fluid=True,
        className="p-4 bg-light",
        children=[
            html.Div([
                html.H2("Branch Performance Analytics", className="fw-bold text-dark"),
                html.P("การประเมินผลการดำเนินงานและศักยภาพการสร้างรายได้รายสาขา", className="text-muted"),
            ], className="mb-4"),

            # KPI Cards
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.Small("สาขาที่ทำรายได้สูงสุด", className="text-muted"),
                        html.H4(f"สาขาที่ {best_branch}", className="text-danger fw-bold mb-0")
                    ])
                ], className="shadow-sm border-0 border-bottom border-danger border-4"), lg=4),
                
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.Small("รายได้รวมทั้งหมดในระบบ", className="text-muted"),
                        html.H4(f"฿ {total_revenue:,.0f}", className="text-dark fw-bold mb-0")
                    ])
                ], className="shadow-sm border-0 border-bottom border-dark border-4"), lg=4),
                
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.Small("ค่าเป้าหมายรายได้เฉลี่ย (Benchmark)", className="text-muted"),
                        html.H4(f"฿ {avg_income_all:,.0f}", className="text-primary fw-bold mb-0")
                    ])
                ], className="shadow-sm border-0 border-bottom border-primary border-4"), lg=4),
            ], className="mb-4 g-3"),

            # กราฟหลัก
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=create_branch_performance_bar(df))), className="shadow-sm border-0"), lg=7),
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=create_efficiency_scatter(df))), className="shadow-sm border-0"), lg=5),
            ], className="g-4 mb-4"),

            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=create_member_growth_by_branch(df))), className="shadow-sm border-0 mb-4"), width=12),
            ]),
            
            # ตารางสรุป Ranking
            dbc.Card([
                dbc.CardHeader(html.H5("ตารางเปรียบเทียบประสิทธิภาพรายสาขา (Ranking)", className="mb-0 fw-bold")),
                dbc.CardBody([
                    dbc.Table.from_dataframe(
                        df.groupby("branch_no").agg({
                            "member_id": "count",
                            "Income_Clean": ["sum", "mean"]
                        }).reset_index().sort_values(("Income_Clean", "sum"), ascending=False)
                        .rename(columns={"branch_no": "รหัสสาขา", "member_id": "สมาชิก (ราย)", "Income_Clean": "รายได้", "count": "จำนวน", "sum": "ยอดรวม (บาท)", "mean": "เฉลี่ยต่อหัว"}),
                        striped=True, hover=True, className="align-middle text-center mb-0"
                    )
                ])
            ], className="shadow-sm border-0")
        ]
    )

layout = create_performance_layout()