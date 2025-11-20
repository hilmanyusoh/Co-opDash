# layout_analysis.py

from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import numpy as np
# เพิ่ม import นี้เพื่อให้มั่นใจว่าฟังก์ชัน helper รันได้สมบูรณ์หากมีการเรียกใช้ภายนอก
from data_manager import load_data 

# --- Helper Functions สำหรับสร้าง KPI Cards และ Charts (ย้ายมาจากโค้ดเดิม) ---

def render_kpi_cards(df):
    if df.empty or 'อายุ' not in df.columns: 
        return dbc.Alert("ข้อมูลไม่พร้อมสำหรับการคำนวณ KPI", color="secondary")
        
    valid_age = df['อายุ'].dropna()
    valid_income = df['รายได้_Clean'].dropna()
    valid_approval = df['ระยะเวลาอนุมัติ_วัน'].dropna()

    num_members = len(df)
    avg_age = valid_age.mean() if not valid_age.empty else np.nan
    
    if 'รหัสสาขา' in df.columns:
        mode_branch = df['รหัสสาขา'].dropna().mode()
        most_common_branch = mode_branch[0] if not mode_branch.empty else 'N/A'
    else:
        most_common_branch = 'N/A'
    
    avg_income = valid_income.mean() if not valid_income.empty else np.nan
    
    cards = [
        dbc.Col(dbc.Card([html.H3(f"{num_members:,}", className="card-title text-primary"), 
                          html.P("จำนวนสมาชิกทั้งหมด (ราย)", className="card-text text-muted")],
                         body=True, className="text-center shadow-sm border-start border-5 border-primary"), md=3),
        dbc.Col(dbc.Card([html.H3(f"{avg_age:.1f}" if pd.notna(avg_age) else "N/A", className="card-title text-info"),
                          html.P(" อายุเฉลี่ย (ปี)", className="card-text text-muted")],
                         body=True, className="text-center shadow-sm border-start border-5 border-info"), md=3),
        dbc.Col(dbc.Card([html.H3(f"{most_common_branch}", className="card-title text-success"), 
                          html.P("สาขาที่ใช้บริการมากที่สุด", className="card-text text-muted")],
                         body=True, className="text-center shadow-sm border-start border-5 border-success"), md=3),
        dbc.Col(dbc.Card([html.H3(f"{avg_income:,.0f}" if pd.notna(avg_income) else "N/A", className="card-title text-warning"),
                          html.P("รายได้เฉลี่ย (บาท)", className="card-text text-muted")],
                         body=True, className="text-center shadow-sm border-start border-5 border-warning"), md=3),
    ]
    return dbc.Row(cards, className="mb-4")

def create_branch_chart(df):
    if 'รหัสสาขา' not in df.columns or df['รหัสสาขา'].isnull().all():
        return px.bar(title="1. ไม่พบข้อมูล 'รหัสสาขา' สำหรับการวิเคราะห์")
    df_branch = df['รหัสสาขา'].value_counts().reset_index()
    df_branch.columns = ['รหัสสาขา', 'จำนวนสมาชิก']
    df_branch_top10 = df_branch.head(10)
    fig = px.bar(df_branch_top10, y='รหัสสาขา', x='จำนวนสมาชิก', orientation='h', 
                 title='1. จำนวนสมาชิกแบ่งตามรหัสสาขา (Top 10)', color='จำนวนสมาชิก',
                 color_continuous_scale=px.colors.sequential.Plasma, template='plotly_dark')
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig

def create_age_distribution_chart(df):
    if 'ช่วงอายุ' not in df.columns or df['ช่วงอายุ'].isnull().all():
        return px.bar(title="2. ไม่พบข้อมูล 'ช่วงอายุ' สำหรับการวิเคราะห์")
    df_age = df['ช่วงอายุ'].value_counts().reset_index()
    df_age.columns = ['ช่วงอายุ', 'จำนวนสมาชิก']
    fig = px.bar(df_age, x='ช่วงอายุ', y='จำนวนสมาชิก', title='2. จำนวนสมาชิกแบ่งตามช่วงอายุ',
                 color='ช่วงอายุ', color_discrete_sequence=px.colors.qualitative.D3, template='plotly_dark')
    fig.update_xaxes(title_text='ช่วงอายุ')
    fig.update_yaxes(title_text='จำนวนสมาชิก')
    return fig

def create_income_by_profession_chart(df):
    if 'รายได้_Clean' not in df.columns or 'อาชีพ' not in df.columns or df['รายได้_Clean'].isnull().all():
         return px.bar(title="3. ไม่พบข้อมูล 'รายได้' หรือ 'อาชีพ' สำหรับการวิเคราะห์")
    df_prof = df.dropna(subset=['อาชีพ', 'รายได้_Clean']).groupby('อาชีพ')['รายได้_Clean'].mean().reset_index()
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
        
    fig = px.histogram(df, x='ระยะเวลาอนุมัติ_วัน', nbins=20, 
                       title='4. การกระจายตัวของระยะเวลาอนุมัติ (วัน)', template='plotly_dark')
    fig.update_xaxes(title_text='ระยะเวลาอนุมัติ (วัน)')
    fig.update_yaxes(title_text='จำนวนสมาชิก')
    return fig

# --- Main Layout Function ---

def render_analysis_tab(df):
    """สร้างเนื้อหาสำหรับหน้า Dashboard Analysis"""

    if df.empty:
        return dbc.Alert(
            [
                html.H4("❌ ไม่พบข้อมูลสำหรับการวิเคราะห์", className="alert-heading"),
                html.P("กรุณาตรวจสอบการเชื่อมต่อ MongoDB และตรวจสอบว่าใน Collection มีเอกสารอยู่หรือไม่", className="mb-0")
            ],
            color="danger",
            className="mt-4"
        )
    
    # สร้างกราฟต่างๆ
    fig_branch = create_branch_chart(df) 
    fig_age = create_age_distribution_chart(df)
    fig_income = create_income_by_profession_chart(df)
    fig_approval = create_approval_time_chart(df)

    # จัด Layout
    return html.Div(
        children=[
            html.H2("Dashboard วิเคราะห์ข้อมูลสมาชิก", className="text-info"),
            html.Hr(className="mb-4"),
            render_kpi_cards(df), 
            html.Hr(),
            dbc.Row([
                dbc.Col(dbc.Card(dcc.Graph(figure=fig_branch), body=True, className="shadow-lg mb-4 bg-dark text-white"), md=6),
                dbc.Col(dbc.Card(dcc.Graph(figure=fig_age), body=True, className="shadow-lg mb-4 bg-dark text-white"), md=6),
            ]),
            dbc.Row([
                dbc.Col(dbc.Card(dcc.Graph(figure=fig_income), body=True, className="shadow-lg mb-4 bg-dark text-white"), md=6),
                dbc.Col(dbc.Card(dcc.Graph(figure=fig_approval), body=True, className="shadow-lg mb-4 bg-dark text-white"), md=6),
            ]),
        ]
    )