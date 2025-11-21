# src/pages/analysis.py

from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import numpy as np

# --- Imports จากภายใน src/ ---
from ..data_manager import load_data 
from ..components.kpi_cards import render_kpi_cards 


# --- Helper Functions สำหรับสร้าง Charts (คัดลอกจาก layout_analysis.py เดิม) ---
def create_branch_chart(df):
    if 'รหัสสาขา' not in df.columns or df['รหัสสาขา'].isnull().all(): return px.bar(title="1. ไม่พบข้อมูล 'รหัสสาขา' สำหรับการวิเคราะห์")
    top_10_branches = df['รหัสสาขา'].value_counts().nlargest(10).index
    df_branch_top10 = df[df['รหัสสาขา'].isin(top_10_branches)]
    if df_branch_top10.empty: return px.bar(title="1. 'รหัสสาขา' ถูกโหลดแล้ว แต่ไม่มีค่าที่นับได้")
    fig = px.pie(df_branch_top10, names='รหัสสาขา', title='1. สัดส่วนจำนวนสมาชิกแบ่งตามรหัสสาขา (Top 10)', hole=.3, template='plotly_dark') 
    fig.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
    fig.update_layout(title_font_size=18, title_x=0.5)                      
    return fig

def create_age_distribution_chart(df):
    if 'ช่วงอายุ' not in df.columns or df['ช่วงอายุ'].isnull().all(): return px.bar(title="2. ไม่พบข้อมูล 'ช่วงอายุ' สำหรับการวิเคราะห์")
    df_age = df['ช่วงอายุ'].value_counts().reset_index()
    if df_age.empty: return px.bar(title="2. 'ช่วงอายุ' ถูกโหลดแล้ว แต่ไม่มีค่าที่นับได้")
    df_age.columns = ['ช่วงอายุ', 'จำนวนสมาชิก']
    fig = px.bar(df_age, x='ช่วงอายุ', y='จำนวนสมาชิก', title='2. จำนวนสมาชิกแบ่งตามช่วงอายุ', color='ช่วงอายุ', color_discrete_sequence=px.colors.qualitative.D3, template='plotly_dark')
    fig.update_xaxes(title_text='ช่วงอายุ'); fig.update_yaxes(title_text='จำนวนสมาชิก')
    fig.update_layout(title_font_size=18, title_x=0.5)
    return fig

def create_income_by_profession_chart(df):
    if 'รายได้_Clean' not in df.columns or 'อาชีพ' not in df.columns or df['รายได้_Clean'].isnull().all(): return px.bar(title="3. ไม่พบข้อมูล 'รายได้' หรือ 'อาชีพ' สำหรับการวิเคราะห์")
    df_prof = df.dropna(subset=['อาชีพ', 'รายได้_Clean']).groupby('อาชีพ')['รายได้_Clean'].mean().reset_index()
    if df_prof.empty: return px.bar(title="3. ไม่มีข้อมูลที่สมบูรณ์สำหรับ 'รายได้' และ 'อาชีพ' เพื่อสร้างกราฟ")
    df_prof.columns = ['อาชีพ', 'รายได้เฉลี่ย (บาท)']
    df_prof_top10 = df_prof.sort_values(by='รายได้เฉลี่ย (บาท)', ascending=False).head(10)
    fig = px.bar(df_prof_top10, x='รายได้เฉลี่ย (บาท)', y='อาชีพ', orientation='h', title='3. 10 อันดับอาชีพที่มีรายได้เฉลี่ยสูงสุด', color='รายได้เฉลี่ย (บาท)', color_continuous_scale=px.colors.sequential.Sunsetdark, template='plotly_dark')
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, title_font_size=18, title_x=0.5)
    return fig

def create_approval_time_chart(df):
    if 'ระยะเวลาอนุมัติ_วัน' not in df.columns or df['ระยะเวลาอนุมัติ_วัน'].isnull().all(): return px.bar(title="4. ไม่พบข้อมูล 'ระยะเวลาอนุมัติ_วัน' สำหรับการวิเคราะห์")
    valid_approval_time = df['ระยะเวลาอนุมัติ_วัน'].dropna()
    if valid_approval_time.empty: return px.bar(title="4. 'ระยะเวลาอนุมัติ_วัน' ถูกโหลดแล้ว แต่ไม่มีค่าที่นับได้")
    fig = px.histogram(df, x='ระยะเวลาอนุมัติ_วัน', nbins=20, title='4. การกระจายตัวของระยะเวลาอนุมัติ (วัน)', template='plotly_dark')
    fig.update_xaxes(title_text='ระยะเวลาอนุมัติ (วัน)'); fig.update_yaxes(title_text='จำนวนสมาชิก')
    fig.update_layout(title_font_size=18, title_x=0.5)
    return fig

# --- 1. Layout ของหน้า Analysis ---
def create_analysis_layout():
    """สร้าง Layout สำหรับหน้า Dashboard Analysis"""
    df = load_data() 
    
    if df.empty:
        return dbc.Container(dbc.Alert([html.H4("❌ ไม่พบข้อมูลสำหรับการวิเคราะห์", className="alert-heading"), html.P("กรุณาตรวจสอบการเชื่อมต่อ MongoDB และตรวจสอบว่าใน Collection มีเอกสารอยู่หรือไม่"),], color="danger", className="mt-5 rounded-3", dismissable=True), fluid=True)
    
    fig_branch = create_branch_chart(df) 
    fig_age = create_age_distribution_chart(df)
    fig_income = create_income_by_profession_chart(df)
    fig_approval = create_approval_time_chart(df)

    # จัด Layout (คัดลอกโค้ดเดิม)
    return dbc.Container(
        children=[
            # Header
            html.Div([html.H1(" Dashboard วิเคราะห์ข้อมูลสมาชิก", className="text-white text-center fw-bolder mb-0"), html.P("ภาพรวมและแนวโน้มที่สำคัญของข้อมูลสมาชิกทั้งหมด", className="text-white-50 text-center mb-0"),], className="py-4 px-4 mb-5 rounded-4", style={'background': 'linear-gradient(90deg, #007bff 0%, #00bcd4 100%)', 'boxShadow': '0 4px 15px rgba(0, 123, 255, 0.5)'}), 
            
            # KPI Section
            render_kpi_cards(df), 
            
            html.Hr(className="my-5"),
            
            # Charts Section
            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader([html.I(className="fas fa-chart-pie me-2 text-primary"), html.Span("1. ข้อมูลสัดส่วนจำนวนสมาชิกตามสาขา", className="fw-bold fs-5"),], className="bg-light py-3 border-bottom border-primary border-3"), dbc.CardBody(dcc.Graph(figure=fig_branch, style={'height': '450px'}))], className="shadow-xl mb-4 h-100 rounded-4 overflow-hidden"), lg=6, md=12),
                dbc.Col(dbc.Card([dbc.CardHeader([html.I(className="fas fa-chart-bar me-2 text-info"), html.Span("2. ข้อมูลจำนวนสมาชิกตามช่วงอายุ", className="fw-bold fs-5"),], className="bg-light py-3 border-bottom border-info border-3"), dbc.CardBody(dcc.Graph(figure=fig_age, style={'height': '450px'}))], className="shadow-xl mb-4 h-100 rounded-4 overflow-hidden"), lg=6, md=12),
            ], className="g-4"),
            
            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader([html.I(className="fas fa-hand-holding-usd me-2 text-warning"), html.Span("3. ข้อมูลรายได้เฉลี่ยตามอาชีพ", className="fw-bold fs-5"),], className="bg-light py-3 border-bottom border-warning border-3"), dbc.CardBody(dcc.Graph(figure=fig_income, style={'height': '450px'}))], className="shadow-xl mb-4 h-100 rounded-4 overflow-hidden"), lg=6, md=12),
                dbc.Col(dbc.Card([dbc.CardHeader([html.I(className="fas fa-hourglass-half me-2 text-success"), html.Span("4. ข้อมูลระยะเวลาอนุมัติ", className="fw-bold fs-5"),], className="bg-light py-3 border-bottom border-success border-3"), dbc.CardBody(dcc.Graph(figure=fig_approval, style={'height': '450px'}))], className="shadow-xl mb-4 h-100 rounded-4 overflow-hidden"), lg=6, md=12),
            ], className="g-4"),
            html.Br(), 
        ], fluid=True, className="py-5" 
    )

layout = create_analysis_layout()

# --- 2. Callbacks ของหน้า Analysis ---
def register_callbacks(app):
    """ลงทะเบียน Callbacks เฉพาะส่วน Analysis (ปัจจุบันไม่มี callbacks เฉพาะ)"""
    pass