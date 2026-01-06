from dash import html
import dash_bootstrap_components as dbc
import pandas as pd

from ..data_manager import load_data
from ..components.kpi_cards import render_amount_kpis

# =========================
# Load data
# =========================
df = load_data()   # หรือ load JOIN members + amount

# =========================
# Page Layout (สำคัญมาก)
# =========================
layout = dbc.Container(
    [
        html.H3("ข้อมูลทางการเงินสมาชิก", className="mb-4"),


        # (optional) เพิ่มกราฟภายหลัง
        # dbc.Row([...])
    ],
    fluid=True,
)
