from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, Tuple

from ..data_manager import load_data 
from ..components.kpi_cards import render_amount_kpis

# ==================================================
# Constants & Configuration
# ==================================================
FONT_FAMILY = "Sarabun, sans-serif"
CHART_HEIGHT = 340
CHART_BG = "rgba(255, 255, 255, 0.5)"
HOVER_BG = "rgba(30, 41, 59, 0.95)"

COLOR_SCHEME = {
    'risk_low': '#10b981',
    'risk_medium': '#f59e0b', 
    'risk_high': '#ef4444',
    'primary': '#334155',
    'disposable': '#06b6d4',
    'credit': '#8b5cf6',
    'income': '#10b981',
    'debt': '#f43f5e',
}

# ==================================================
# Data Processing
# ==================================================
def calculate_financial_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate derived financial metrics."""
    df = df.copy()
    df["disposable"] = df["net_yearly_income"] - df["yearly_debt_payments"]
    df["available_credit"] = df["credit_limit"] * (1 - (df["credit_limit_used_pct"] / 100))
    df["ind_dti"] = (df["yearly_debt_payments"] / df["net_yearly_income"] * 100).fillna(0)
    df["debt_ratio"] = (df["yearly_debt_payments"] / df["net_yearly_income"] * 100).fillna(0)
    return df

def get_risk_category(debt_ratio: float) -> str:
    """Categorize risk level based on debt ratio."""
    if debt_ratio < 35:
        return "ต่ำ"
    elif debt_ratio < 45:
        return "ปานกลาง"
    else:
        return "สูง"

# ==================================================
# Chart Helper
# ==================================================
def apply_chart_layout(fig, title, height=CHART_HEIGHT):
    """Apply consistent layout to charts."""
    fig.update_layout(
        title={
            "text": f"<b>{title}</b>",
            "x": 0.02,
            "xanchor": "left",
            "font": {"size": 16, "color": "#1e293b"}
        },
        height=height,
        plot_bgcolor="rgba(248, 250, 252, 0.5)",
        paper_bgcolor=CHART_BG,
        font=dict(
            family=FONT_FAMILY,
            color="#334155",
        ),
        margin=dict(t=50, b=40, l=50, r=30),
        hoverlabel=dict(
            bgcolor=HOVER_BG,
            font_family=FONT_FAMILY,
            font_color="white",
            bordercolor="rgba(148, 163, 184, 0.3)",
        ),
    )
    return fig

# ==================================================
# Enhanced Charts
# ==================================================

def chart_financial_risk_gauge(df: pd.DataFrame) -> go.Figure:
    """Financial risk gauge chart."""
    total_debt = df["yearly_debt_payments"].sum()
    total_income = df["net_yearly_income"].sum()
    risk_index = (total_debt / total_income * 100) if total_income > 0 else 0
    
    if risk_index < 35:
        risk_color = COLOR_SCHEME['risk_low']
    elif risk_index < 45:
        risk_color = COLOR_SCHEME['risk_medium']
    else:
        risk_color = COLOR_SCHEME['risk_high']
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=risk_index,
        number={
            'suffix': "%",
            'font': {'size': 48, 'color': '#1e293b', 'family': FONT_FAMILY, 'weight': 'bold'}
        },
        delta={
            'reference': 35,
            'increasing': {'color': COLOR_SCHEME['risk_high']},
            'decreasing': {'color': COLOR_SCHEME['risk_low']},
            'font': {'size': 16, 'family': FONT_FAMILY}
        },
        gauge={
            'axis': {
                'range': [0, 100],
                'tickwidth': 2,
                'tickcolor': "#cbd5e1",
                'tickfont': {'size': 12, 'color': '#64748b', 'family': FONT_FAMILY}
            },
            'bar': {'color': risk_color, 'thickness': 0.8},
            'bgcolor': "white",
            'borderwidth': 3,
            'bordercolor': "#e2e8f0",
            'steps': [
                {'range': [0, 35], 'color': "rgba(16, 185, 129, 0.12)"},
                {'range': [35, 45], 'color': "rgba(245, 158, 11, 0.12)"},
                {'range': [45, 100], 'color': "rgba(239, 68, 68, 0.12)"},
            ],
            'threshold': {
                'line': {'color': "#334155", 'width': 5},
                'thickness': 0.85,
                'value': risk_index
            }
        },
    ))

    legend_html = (
        f"<span style='color:{COLOR_SCHEME['risk_low']}; font-size:14px'>●</span> <span style='color:#64748b'>ความเสี่ยงต่ำ</span> &nbsp;&nbsp; "
        f"<span style='color:{COLOR_SCHEME['risk_medium']}; font-size:14px'>●</span> <span style='color:#64748b'>ความเสี่ยงกลาง</span> &nbsp;&nbsp; "
        f"<span style='color:{COLOR_SCHEME['risk_high']}; font-size:14px'>●</span> <span style='color:#64748b'>ความเสี่ยงสูง</span>"
    )

    fig.add_annotation(
        text=legend_html,
        x=0.5, y=1.35,
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=13, color="#475569", family=FONT_FAMILY),
        align="center"
    )

    fig.update_layout(
        height=280,
        margin=dict(t=60, b=30, l=40, r=40), 
        paper_bgcolor=CHART_BG,
        font=dict(family=FONT_FAMILY),
    )
    return fig

def chart_liquidity_by_gen(df: pd.DataFrame) -> go.Figure:
    df_plot = calculate_financial_metrics(df)

    summary = (
        df_plot
        .groupby("Age_Group")[["disposable", "available_credit"]]
        .mean()
        .reset_index()
    )

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='เงินคงเหลือหลังหนี้',
        x=summary["Age_Group"],
        y=summary["disposable"],
        marker=dict(
            color=COLOR_SCHEME['disposable'],
            line=dict(color='white', width=2.5),
        ),
        text=[f"฿{v:,.0f}" for v in summary["disposable"]],
        textposition='outside',
        textfont=dict(size=11, family=FONT_FAMILY, color='#334155'),
        hovertemplate="<b>%{x}</b><br>เงินคงเหลือ: ฿%{y:,.0f}<extra></extra>",
        opacity=0.9
    ))

    fig.add_trace(go.Bar(
        name='วงเงินสินเชื่อคงเหลือ',
        x=summary["Age_Group"],
        y=summary["available_credit"],
        marker=dict(
            color=COLOR_SCHEME['credit'],
            line=dict(color='white', width=2.5),
        ),
        text=[f"฿{v:,.0f}" for v in summary["available_credit"]],
        textposition='outside',
        textfont=dict(size=11, family=FONT_FAMILY, color='#334155'),
        hovertemplate="<b>%{x}</b><br>วงเงินคงเหลือ: ฿%{y:,.0f}<extra></extra>",
        opacity=0.9
    ))

    fig.update_layout(
        barmode='group',
        height=CHART_HEIGHT,
        margin=dict(t=50, b=60, l=70, r=40),
        legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.12,
        xanchor="center",
        x=0.5,
        bgcolor="rgba(255, 255, 255, 0.7)",
        bordercolor="rgba(148, 163, 184, 0.3)",
        borderwidth=1,
        font=dict(size=12, family=FONT_FAMILY, color='#475569')
    ),
        font=dict(family=FONT_FAMILY, size=12),
        paper_bgcolor=CHART_BG,
        plot_bgcolor="rgba(248, 250, 252, 0.5)",
        xaxis=dict(
            title="<b>ช่วงอายุ</b>",
            showgrid=False,
        ),
        yaxis=dict(
            title="<b>จำนวนเงินเฉลี่ย (บาท)</b>",
            showgrid=True,
            gridcolor="rgba(203, 213, 225, 0.4)",
        ),
        hoverlabel=dict(
            bgcolor=HOVER_BG,
            font_family=FONT_FAMILY,
            font_color="white",
            bordercolor="rgba(148, 163, 184, 0.3)"
        )
    )
    
# def chart_premium_segment_treemap(df: pd.DataFrame) -> go.Figure:
#     """Enhanced treemap with better colors and interactivity."""
#     df_temp = calculate_financial_metrics(df)

#     premium_df = df_temp[
#         (df_temp["credit_limit_used_pct"] < 30) &
#         (df_temp["ind_dti"] < 25)
#     ]

#     summary = (
#         premium_df
#         .groupby(["province_name", "career_name"])
#         .size()
#         .reset_index(name="count")
#     )

#     # Add percentage
#     total = summary["count"].sum()
#     summary["percentage"] = (summary["count"] / total * 100).round(2)

#     fig = px.treemap(
#         summary,
#         path=[px.Constant("Premium Segment"), "province_name", "career_name"],
#         values="count",
#         color="count",
#         color_continuous_scale=[
#             [0, "#fce7f3"],
#             [0.25, "#fbcfe8"],
#             [0.5, "#f472b6"],
#             [0.75, "#ec4899"],
#             [1, "#be185d"]
#         ],
#         hover_data={"percentage": ":.1f"},
#     )

#     fig.update_traces(
#         textinfo="label+value+percent parent",
#         textfont=dict(size=13, family=FONT_FAMILY),
#         marker=dict(
#             line=dict(color="white", width=2),
#             cornerradius=5
#         ),
#         hovertemplate=(
#             "<b>%{label}</b><br>"
#             "จำนวน: %{value} คน<br>"
#             "สัดส่วน: %{percentParent}<br>"
#             "<extra></extra>"
#         )
#     )

#     fig.update_layout(
#         height=450,
#         margin=dict(t=30, b=10, l=10, r=10),
#         font=dict(family=FONT_FAMILY, size=12),
#         paper_bgcolor=CHART_BG,
#     )
    
#     return fig


# def chart_debt_income_scatter(df: pd.DataFrame) -> go.Figure:
#     """New: Debt-to-Income scatter plot with risk zones."""
#     df_plot = calculate_financial_metrics(df)
    
#     # Sample if too many points
#     if len(df_plot) > 1000:
#         df_plot = df_plot.sample(1000, random_state=42)
    
#     fig = go.Figure()

#     # Add risk zone shapes
#     fig.add_shape(
#         type="rect",
#         x0=0, y0=0, x1=100, y1=35,
#         fillcolor=COLOR_SCHEME['risk_low'],
#         opacity=0.1,
#         layer="below",
#         line_width=0,
#     )
#     fig.add_shape(
#         type="rect",
#         x0=0, y0=35, x1=100, y1=45,
#         fillcolor=COLOR_SCHEME['risk_medium'],
#         opacity=0.1,
#         layer="below",
#         line_width=0,
#     )
#     fig.add_shape(
#         type="rect",
#         x0=0, y0=45, x1=100, y1=100,
#         fillcolor=COLOR_SCHEME['risk_high'],
#         opacity=0.1,
#         layer="below",
#         line_width=0,
#     )

#     # Add scatter points by age group
#     for age_group in df_plot["Age_Group"].unique():
#         group_data = df_plot[df_plot["Age_Group"] == age_group]
        
#         fig.add_trace(go.Scatter(
#             x=group_data["credit_limit_used_pct"],
#             y=group_data["debt_ratio"],
#             mode='markers',
#             name=age_group,
#             marker=dict(
#                 size=8,
#                 opacity=0.7,
#                 line=dict(width=1, color='white')
#             ),
#             hovertemplate=(
#                 "<b>%{fullData.name}</b><br>"
#                 "ใช้วงเงิน: %{x:.1f}%<br>"
#                 "อัตราหนี้: %{y:.1f}%<br>"
#                 "<extra></extra>"
#             )
#         ))

#     # Add reference lines
#     fig.add_hline(
#         y=35, line_dash="dash",
#         line_color=COLOR_SCHEME['risk_medium'],
#         annotation_text="เกณฑ์ความเสี่ยงปานกลาง (35%)",
#         annotation_position="right"
#     )
#     fig.add_vline(
#         x=30, line_dash="dash",
#         line_color=COLOR_SCHEME['risk_medium'],
#         annotation_text="วงเงินใช้ 30%",
#         annotation_position="top"
#     )

#     fig.update_layout(
#         height=400,
#         margin=dict(t=50, b=50, l=60, r=30),
#         xaxis=dict(
#             title="<b>% การใช้วงเงินสินเชื่อ</b>",
#             range=[0, 100],
#             showgrid=True,
#             gridcolor="rgba(203, 213, 225, 0.3)",
#         ),
#         yaxis=dict(
#             title="<b>อัตราส่วนหนี้ต่อรายได้ (%)</b>",
#             range=[0, 100],
#             showgrid=True,
#             gridcolor="rgba(203, 213, 225, 0.3)",
#         ),
#         legend=dict(
#             orientation="h",
#             yanchor="bottom",
#             y=-0.25,
#             xanchor="center",
#             x=0.5,
#             bgcolor="rgba(255, 255, 255, 0.9)",
#             bordercolor="#e2e8f0",
#             borderwidth=1
#         ),
#         font=dict(family=FONT_FAMILY),
#         paper_bgcolor=CHART_BG,
#         plot_bgcolor="white",
#         hoverlabel=dict(bgcolor=HOVER_BG, font_family=FONT_FAMILY)
#     )
    
#     return fig


# def chart_income_debt_comparison(df: pd.DataFrame) -> go.Figure:
#     """New: Income vs Debt comparison by career."""
#     df_plot = calculate_financial_metrics(df)
    
#     summary = (
#         df_plot
#         .groupby("career_name")[["net_yearly_income", "yearly_debt_payments"]]
#         .mean()
#         .sort_values("net_yearly_income", ascending=True)
#         .tail(10)
#         .reset_index()
#     )

#     fig = go.Figure()

#     fig.add_trace(go.Bar(
#         name='รายได้สุทธิต่อปี',
#         y=summary["career_name"],
#         x=summary["net_yearly_income"],
#         orientation='h',
#         marker=dict(
#             color=COLOR_SCHEME['income'],
#             line=dict(color='white', width=2)
#         ),
#         text=[f"฿{v:,.0f}" for v in summary["net_yearly_income"]],
#         textposition='outside',
#         hovertemplate="<b>%{y}</b><br>รายได้: ฿%{x:,.0f}<extra></extra>"
#     ))

#     fig.add_trace(go.Bar(
#         name='ภาระหนี้ต่อปี',
#         y=summary["career_name"],
#         x=summary["yearly_debt_payments"],
#         orientation='h',
#         marker=dict(
#             color=COLOR_SCHEME['debt'],
#             line=dict(color='white', width=2)
#         ),
#         text=[f"฿{v:,.0f}" for v in summary["yearly_debt_payments"]],
#         textposition='outside',
#         hovertemplate="<b>%{y}</b><br>หนี้: ฿%{x:,.0f}<extra></extra>"
#     ))

#     fig.update_layout(
#         barmode='group',
#         height=420,
#         margin=dict(t=50, b=50, l=150, r=100),
#         xaxis=dict(
#             title="<b>จำนวนเงิน (บาท)</b>",
#             showgrid=True,
#             gridcolor="rgba(203, 213, 225, 0.3)",
#         ),
#         yaxis=dict(
#             title="<b>อาชีพ</b>",
#             showgrid=False,
#         ),
#         legend=dict(
#             orientation="h",
#             yanchor="bottom",
#             y=1.02,
#             xanchor="center",
#             x=0.5,
#             bgcolor="rgba(255, 255, 255, 0.9)",
#             bordercolor="#e2e8f0",
#             borderwidth=1
#         ),
#         font=dict(family=FONT_FAMILY, size=12),
#         paper_bgcolor=CHART_BG,
#         plot_bgcolor="rgba(248, 250, 252, 0.5)",
#         hoverlabel=dict(bgcolor=HOVER_BG, font_family=FONT_FAMILY)
#     )
    
#     return fig

    return apply_chart_layout(fig, "สภาพคล่องตามช่วงอายุ")


# ==================================================
# Layout
# ==================================================
def create_amount_layout():
    df = load_data()
    if df.empty:
        return dbc.Container(
            dbc.Alert("ไม่พบข้อมูล", color="warning", className="mt-5")
        )
    
    df_metrics = calculate_financial_metrics(df)

    card = lambda content, title=None: dbc.Card(
    dbc.CardBody(
        [
            html.H6(
                title,
                className="fw-bold mb-3",
                style={"color": "#1e293b", "fontSize": "15px"}
            ) if title else None,

            content
        ],
        style={"padding": "18px"},
    ),
    className="shadow-sm rounded-3 border-0 mb-3",
    style={"height": "100%"},
)

    return dbc.Container(
        fluid=True,
        style={
            "padding": "20px 30px",
            "maxWidth": "1400px",
            "margin": "0 auto",
        },

        children=[
            html.H3(
                "วิเคราะห์สุขภาพทางการเงิน",
                className="page-title fw-bold mb-3",
            ),

            render_amount_kpis(df),

            dbc.Row([
                dbc.Col(
                    card(
                        dcc.Graph(
                            figure=chart_financial_risk_gauge(df),
                            config={"displayModeBar": False, "responsive": True},
                            style={"height": "280px"},
                        ),
                        "ประเมินความเสี่ยงทางการเงิน"
                    ),
                    xs=12, lg=4
                ),
                dbc.Col(
                    card(
                        dcc.Graph(
                            figure=chart_liquidity_by_gen(df),
                            config={"displayModeBar": False, "responsive": True},
                        )
                    ),
                    xs=12, lg=8
                ),
                
            ], className="g-3"),
            # # ===== Row 2 =====
            # dbc.Row([
            #     dbc.Col(
            #         card(
            #             dcc.Graph(
            #                 figure=chart_debt_income_scatter(df),
            #                 config={"displayModeBar": False},
            #                 style={"height": "400px"},
            #             ),
            #             "Risk Distribution"
            #         ),
            #         lg=6, md=12,
            #     ),
            #     dbc.Col(
            #         card(
            #             dcc.Graph(
            #                 figure=chart_income_debt_comparison(df),
            #                 config={"displayModeBar": False},
            #                 style={"height": "420px"},
            #             ),
            #             "Income vs Debt (Top 10 Career)"
            #         ),
            #         lg=6, md=12,
            #     ),
            # ], className="g-3 mb-3"),

            # ===== Row 3 =====
            # dbc.Row([
            #     dbc.Col(
            #         card(
            #             dcc.Graph(
            #                 figure=chart_premium_segment_treemap(df),
            #                 config={"displayModeBar": False},
            #                 style={"height": "450px"},
            #             ),
            #             "Premium Segment"
            #         ),
            #         width=12,
            #     )
            # ], className="g-3"),
        ],
    )


layout = create_amount_layout()