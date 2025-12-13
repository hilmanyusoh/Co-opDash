# src/components/kpi_cards.py

from dash import html
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np


def render_kpi_card(title, value, unit, icon_class, color_class):
    
    # กำหนดสีตามคลาสที่ให้มา (ใช้สำหรับ icon และ border)
    color_map = {
        'primary': '#007bff', 'purple': '#6f42c1', 'success': '#28a745', 'warning': '#ffc107', 'orange': '#fd7e14'
    }
    card_color = color_map.get(color_class, '#007bff')

    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.I(className=f"fas {icon_class} fa-3x me-3 text-white"),
                        html.Div(
                            [
                                html.H3(title, className="card-title text-white-50 mb-0 fw-light"),
                                html.H2(value, className="card-text text-white fw-bolder mb-0"),
                                html.P(unit, className="text-white-50 mb-0 small"),
                            ],
                            className="text-end"
                        ),
                    ],
                    className="d-flex justify-content-between align-items-center"
                )
            ]
        ),
        className=f"shadow-lg rounded-4 border-start border-5",
        style={
            'background': f'linear-gradient(90deg, {card_color} 0%, {card_color}b0 100%)',
            'border-left-color': card_color,
            'border-left-width': '5px'
        }
    )


# --- Main Function: จัดกลุ่ม KPI Cards ---
def render_kpi_cards(df: pd.DataFrame):
    
    # 1. จำนวนสมาชิกทั้งหมด
    total_members = len(df)

    
    # 2. ช่วงอายุที่มีสมาชิกมากที่สุด (KPI ที่ถูกแก้ไขตามความต้องการ)
    if 'ช่วงอายุ' in df.columns and not df['ช่วงอายุ'].isnull().all():
        # Logic การคำนวณฐานนิยม 
        most_common_age_group = df['ช่วงอายุ'].mode().iloc[0]
        age_value = str(most_common_age_group).split(' ')[0] 
        age_unit = "" 
    else:
        age_value = 'N/A'
        age_unit = 'ไม่พบข้อมูล'
        
    # 3. จำนวนสาขาที่ไม่ซ้ำกัน
    if 'รหัสสาขา' in df.columns and not df['รหัสสาขา'].isnull().all():
        num_branches = df['รหัสสาขา'].nunique()
        branch_unit = ""
    else:
        num_branches = 'N/A'
        branch_unit = 'ไม่พบข้อมูล'
        
    # 4. รายได้เฉลี่ย
    if 'รายได้_Clean' in df.columns and not df['รายได้_Clean'].isnull().all():
        avg_income = df['รายได้_Clean'].mean()
        income_value = "{:,.0f}".format(avg_income) 
        income_unit = ""
    else:
        income_value = 'N/A'
        income_unit = 'ไม่พบข้อมูล'

    # สร้าง Cards 
    card_members = render_kpi_card("สมาชิก", 
                                   f"{total_members}", 
                                   "", 
                                   'fa-users', 
                                   'primary')
                                   
    card_age = render_kpi_card("ช่วงอายุ", 
                               f"{age_value}", 
                               age_unit, 
                               'fa-birthday-cake', 
                               'purple')
                               
    card_branches = render_kpi_card("สาขา", 
                                    f"{num_branches}", 
                                    branch_unit, 
                                    'fa-building', 
                                    'success')
                                    
    card_income = render_kpi_card("รายได้", 
                                  f"{income_value}", 
                                  income_unit, 
                                  'fa-dollar-sign', 
                                  'orange')
    
    # จัด Layout ใน Row
    return dbc.Row(
        [
            dbc.Col(card_members, lg=3, md=6, className="mb-4"),
            dbc.Col(card_age, lg=3, md=6, className="mb-4"),
            dbc.Col(card_branches, lg=3, md=6, className="mb-4"),
            dbc.Col(card_income, lg=3, md=6, className="mb-4"),
        ],
        className="g-4"
    )