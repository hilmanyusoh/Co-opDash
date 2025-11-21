from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import numpy as np
from data_manager import load_data 

# --- Helper Functions สำหรับสร้าง KPI Cards และ Charts (ปรับปรุงการตรวจสอบข้อมูล) ---

def render_kpi_cards(df):
    # ตรวจสอบว่า DataFrame ว่างเปล่าหรือไม่
    if df.empty or 'อายุ' not in df.columns: 
        return dbc.Alert("ข้อมูลไม่พร้อมสำหรับการคำนวณ KPI", color="secondary")
        
    # ใช้ len(series) > 0 เพื่อตรวจสอบว่ามีค่าที่ไม่ใช่ NaN เหลืออยู่จริง
    valid_age = df['อายุ'].dropna()
    valid_income = df['รายได้_Clean'].dropna()
    
    num_members = len(df)
    avg_age = valid_age.mean() if len(valid_age) > 0 else np.nan
    
    # *** การปรับปรุง KPI: นับจำนวนสาขาที่ไม่ซ้ำกันทั้งหมด ***
    if 'รหัสสาขา' in df.columns:
        num_branches = df['รหัสสาขา'].dropna().nunique()
        total_branches = f"{num_branches:,}" if num_branches > 0 else "0"
    else:
        total_branches = '0'
    
    avg_income = valid_income.mean() if len(valid_income) > 0 else np.nan
    
    # KPIs Styling (ใช้ธีม SLATE)
    kpi_data = [
        ("จำนวนสมาชิกทั้งหมด (ราย)", f"{num_members:,}", "primary", "fas fa-users"), 
        ("อายุเฉลี่ย (ปี)", f"{avg_age:.1f}" if pd.notna(avg_age) else "N/A", "info", "fas fa-birthday-cake"),
        # *** KPI ใหม่: จำนวนสาขาทั้งหมด ***
        ("จำนวนสาขาทั้งหมด (แห่ง)", total_branches, "success", "fas fa-building"),
        ("รายได้เฉลี่ย (บาท)", f"{avg_income:,.0f}" if pd.notna(avg_income) else "N/A", "warning", "fas fa-dollar-sign"),
    ]

    cards = []
    for title, value, color, icon in kpi_data:
        card = dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader(html.I(className=f"{icon} me-2"), className=f"bg-{color} text-white"),
                    dbc.CardBody(
                        [
                            html.H3(value, className=f"card-title text-{color} fw-bold"), 
                            html.P(title, className="card-text text-muted small"),
                        ],
                        className="text-center"
                    ),
                ],
                className="shadow-lg mb-4 border-0 border-start border-5",
            ),
            md=3
        )
        cards.append(card)
        
    return dbc.Row(cards, className="g-4")

def create_branch_chart(df):
    if 'รหัสสาขา' not in df.columns or df['รหัสสาขา'].isnull().all():
        return px.bar(title="1. ไม่พบข้อมูล 'รหัสสาขา' สำหรับการวิเคราะห์")
    
    # ใช้ค่าที่ไม่ซ้ำกัน 10 อันดับแรก
    top_10_branches = df['รหัสสาขา'].value_counts().nlargest(10).index
    df_branch_top10 = df[df['รหัสสาขา'].isin(top_10_branches)]
    
    if df_branch_top10.empty:
        return px.bar(title="1. 'รหัสสาขา' ถูกโหลดแล้ว แต่ไม่มีค่าที่นับได้")
        
    # Pie Chart
    fig = px.pie(df_branch_top10, 
                 names='รหัสสาขา', 
                 title='1. สัดส่วนจำนวนสมาชิกแบ่งตามรหัสสาขา (Top 10)',
                 hole=.3, # ทำให้เป็น Donut Chart
                 template='plotly_dark')
                 
    fig.update_traces(textposition='inside', textinfo='percent+label', 
                      marker=dict(line=dict(color='#000000', width=1)))
                      
    return fig

def create_age_distribution_chart(df):
    if 'ช่วงอายุ' not in df.columns or df['ช่วงอายุ'].isnull().all():
        return px.bar(title="2. ไม่พบข้อมูล 'ช่วงอายุ' สำหรับการวิเคราะห์")
        
    df_age = df['ช่วงอายุ'].value_counts().reset_index()
    if df_age.empty:
         return px.bar(title="2. 'ช่วงอายุ' ถูกโหลดแล้ว แต่ไม่มีค่าที่นับได้")
         
    df_age.columns = ['ช่วงอายุ', 'จำนวนสมาชิก']
    fig = px.bar(df_age, x='ช่วงอายุ', y='จำนวนสมาชิก', title='2. จำนวนสมาชิกแบ่งตามช่วงอายุ',
                 color='ช่วงอายุ', color_discrete_sequence=px.colors.qualitative.D3, template='plotly_dark')
    fig.update_xaxes(title_text='ช่วงอายุ')
    fig.update_yaxes(title_text='จำนวนสมาชิก')
    return fig

def create_income_by_profession_chart(df):
    if 'รายได้_Clean' not in df.columns or 'อาชีพ' not in df.columns or df['รายได้_Clean'].isnull().all():
         return px.bar(title="3. ไม่พบข้อมูล 'รายได้' หรือ 'อาชีพ' สำหรับการวิเคราะห์")
         
    # กรอง NaN ก่อน groupby เพื่อป้องกันข้อผิดพลาด
    df_prof = df.dropna(subset=['อาชีพ', 'รายได้_Clean']).groupby('อาชีพ')['รายได้_Clean'].mean().reset_index()
    if df_prof.empty:
        return px.bar(title="3. ไม่มีข้อมูลที่สมบูรณ์สำหรับ 'รายได้' และ 'อาชีพ' เพื่อสร้างกราฟ")
        
    df_prof.columns = ['อาชีพ', 'รายได้เฉลี่ย (บาท)']
    df_prof_top10 = df_prof.sort_values(by='รายได้เฉลี่ย (บาท)', ascending=False).head(10)
    fig = px.bar(df_prof_top10, x='รายได้เฉลี่ย (บาท)', y='อาชีพ', orientation='h', 
                 title='3. 10 อันดับอาชีพที่มีรายได้เฉลี่ยสูงสุด', color='รายได้เฉลี่ย (บาท)',
                 color_continuous_scale=px.colors.sequential.Sunsetdark, template='plotly_dark')
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig

def create_approval_time_chart(df):
    if 'ระยะเวลาอนุมัติ_วัน' not in df.columns or df['ระยะเวลาอนุมัติ_วัน'].isnull().all():
        return px.bar(title="4. ไม่พบข้อมูล 'ระยะเวลาอนุมัติ_วัน' สำหรับการวิเคราะห์")
        
    # ตรวจสอบว่ามีค่าที่ไม่ใช่ NaN มากพอที่จะสร้าง histogram
    valid_approval_time = df['ระยะเวลาอนุมัติ_วัน'].dropna()
    if valid_approval_time.empty:
        return px.bar(title="4. 'ระยะเวลาอนุมัติ_วัน' ถูกโหลดแล้ว แต่ไม่มีค่าที่นับได้")
        
    fig = px.histogram(df, x='ระยะเวลาอนุมัติ_วัน', nbins=20, 
                       title='4. การกระจายตัวของระยะเวลาอนุมัติ (วัน)', template='plotly_dark')
    fig.update_xaxes(title_text='ระยะเวลาอนุมัติ (วัน)')
    fig.update_yaxes(title_text='จำนวนสมาชิก')
    return fig

# --- Main Layout Function ---

def render_analysis_tab(df):
    """สร้างเนื้อหาสำหรับหน้า Dashboard Analysis"""

    if df.empty:
        return dbc.Container(
            dbc.Alert(
                [
                    html.H4("❌ ไม่พบข้อมูลสำหรับการวิเคราะห์", className="alert-heading"),
                    html.P("กรุณาตรวจสอบการเชื่อมต่อ MongoDB และตรวจสอบว่าใน Collection มีเอกสารอยู่หรือไม่"),
                ],
                color="danger",
                className="mt-5",
                dismissable=True,
            ),
            fluid=True
        )
    
    # สร้างกราฟต่างๆ
    fig_branch = create_branch_chart(df) 
    fig_age = create_age_distribution_chart(df)
    fig_income = create_income_by_profession_chart(df)
    fig_approval = create_approval_time_chart(df)

    # จัด Layout
    return dbc.Container(
        children=[
            html.H1("📊 Dashboard วิเคราะห์ข้อมูลสมาชิก", className="text-primary my-4"), 
            html.Hr(className="mb-5"),
            
            # --- KPI Section ---
            render_kpi_cards(df), 
            
            html.Hr(className="mt-3 mb-5"),
            
            # --- Charts Section ---
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("ข้อมูลสัดส่วนจำนวนสมาชิกตามสาขา", className="fw-bold"),
                            # Pie Chart สำหรับสาขา (Fixed Height)
                            dbc.CardBody(dcc.Graph(figure=fig_branch, style={'height': '400px'})),
                        ], 
                        className="shadow-lg mb-4 h-100", 
                    ), 
                    lg=6, md=12
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("ข้อมูลจำนวนสมาชิกตามช่วงอายุ", className="fw-bold"),
                            # Bar Chart สำหรับอายุ (Fixed Height)
                            dbc.CardBody(dcc.Graph(figure=fig_age, style={'height': '400px'})),
                        ], 
                        className="shadow-lg mb-4 h-100", 
                    ), 
                    lg=6, md=12
                ),
            ], className="g-4"),
            
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("ข้อมูลรายได้เฉลี่ยตามอาชีพ", className="fw-bold"),
                            # Bar Chart สำหรับรายได้เฉลี่ยตามอาชีพ (Fixed Height)
                            dbc.CardBody(dcc.Graph(figure=fig_income, style={'height': '400px'})),
                        ], 
                        className="shadow-lg mb-4 h-100",
                    ), 
                    lg=6, md=12
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("ข้อมูลระยะเวลาอนุมัติ", className="fw-bold"),
                            # Histogram สำหรับระยะเวลาอนุมัติ (Fixed Height)
                            dbc.CardBody(dcc.Graph(figure=fig_approval, style={'height': '400px'})),
                        ], 
                        className="shadow-lg mb-4 h-100",
                    ), 
                    lg=6, md=12
                ),
            ], className="g-4"),
        ],
        fluid=True 
    )