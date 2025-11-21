# src/components/kpi_cards.py

import dash_bootstrap_components as dbc
from dash import html
import pandas as pd
import numpy as np

def render_kpi_cards(df):
    
    if df.empty or 'อายุ' not in df.columns: 
        return dbc.Row(dbc.Col(
            dbc.Alert("ข้อมูลไม่พร้อมสำหรับการคำนวณ KPI - กรุณาตรวจสอบข้อมูลที่โหลด", color="secondary", className="text-center rounded-3 shadow-sm"),
            width=12
        ))
        
    valid_age = df['อายุ'].dropna()
    valid_income = df['รายได้_Clean'].dropna()
    
    num_members = len(df)
    avg_age = valid_age.mean() if len(valid_age) > 0 else np.nan
    num_branches = df['รหัสสาขา'].dropna().nunique() if 'รหัสสาขา' in df.columns else 0
    avg_income = valid_income.mean() if len(valid_income) > 0 else np.nan
    
    kpi_data = [
        ("จำนวนสมาชิกทั้งหมด", f"{num_members:,}", "primary", "fas fa-users"), 
        ("อายุเฉลี่ย", f"{avg_age:.1f}" 
         
         if pd.notna(avg_age) 
         else "N/A", "info", "fas fa-birthday-cake"),
        ("จำนวนสาขา", f"{num_branches:,}", "success", "fas fa-building"),
        ("รายได้เฉลี่ย", f"{avg_income:,.0f}" 
         
         if pd.notna(avg_income) 
         else "N/A", "warning", "fas fa-dollar-sign"),
    ]

    cards = []
    for title, value, color, icon in kpi_data:
        if "สมาชิก" in title:
            trailing_text = "(ราย)"
        elif "สาขา" in title:
            trailing_text = "(แห่ง)"  
        elif "อายุ" in title:
            trailing_text = "(ปี)"
        else:
            trailing_text = "(บาท/เดือน)"
        
        card = dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader([html.I(className=f"{icon} fa-2x text-white me-2"), html.Span(title, className="text-white fw-bold"),], 
                                   className=f"bg-{color} text-center py-2 border-0 rounded-top-4"),
                    dbc.CardBody([html.Div([html.H1(value, 
                                                    className=f"card-title text-center text-{color} fw-bolder mb-0"), html.P(trailing_text, 
                                                                                                                             className="card-text text-muted small text-center mt-1"),], 
                                           className="mt-3",)], className="bg-white rounded-bottom-4"),
                ],
                className="shadow-3d mb-4 border-0 rounded-4 overflow-hidden",
                style={'--bs-card-shadow': '0 10px 30px rgba(0, 0, 0, 0.1)', 'border-top': f'5px solid var(--bs-{color})'}
            ),
            md=3
        )
        cards.append(card)
        
    return dbc.Row(cards, className="g-4")