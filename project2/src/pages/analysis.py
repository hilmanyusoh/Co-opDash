# src/pages/analysis.py

from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from datetime import date 
from dash import dash_table 

from ..data_manager import load_data
from ..components.kpi_cards import render_kpi_cards


# ==================================================
# Helper Functions: Data Preprocessing
# ==================================================

def preprocess_data(df):
    """ทำความสะอาดและสร้างคอลัมน์สำหรับการวิเคราะห์"""
    
    # 1. ทำความสะอาด Income
    if 'income' in df.columns:
        df['Income_Clean'] = (
            df['income'].astype(str)
            .str.replace(',', '', regex=False)
            .str.strip()
        )
        df['Income_Clean'] = pd.to_numeric(df['Income_Clean'], errors='coerce').fillna(0)
    
    # 2. คำนวณ Age และ Age_Group
    if 'birthday' in df.columns:
        df['birthday'] = pd.to_datetime(df['birthday'], errors='coerce')
        today = date(2025, 12, 16) 
        
        df['Age'] = today.year - df['birthday'].dt.year - (
            (today.month < df['birthday'].dt.month) | 
            ((today.month == df['birthday'].dt.month) & (today.day < df['birthday'].dt.day))
        ).astype(int)
        
        bins = [0, 20, 30, 40, 50, 60, 100]
        labels = ['< 20', '20-29', '30-39', '40-49', '50-59', '60+']
        df['Age_Group'] = pd.cut(df['Age'], bins=bins, labels=labels, right=False, ordered=True)
        
    # 3. คำนวณ Approval Days
    if 'registration_date' in df.columns and 'approval_date' in df.columns:
        df['registration_date'] = pd.to_datetime(df['registration_date'], errors='coerce')
        df['approval_date'] = pd.to_datetime(df['approval_date'], errors='coerce')
        df['Approval_days'] = (df['approval_date'] - df['registration_date']).dt.days

    # 4. ปรับชื่อคอลัมน์
    rename_dict = {}
    if 'branch_code' in df.columns:
        rename_dict['branch_code'] = 'Branch_code'
    if 'career' in df.columns:
        rename_dict['career'] = 'Career'
        
    if rename_dict:
        df.rename(columns=rename_dict, inplace=True)
    
    return df


# ==================================================
# Helper Functions: Charts (ปรับแต่งสีและสไตล์)
# ==================================================

# สีธีมที่ทันสมัยและนุ่มนวล
COLORS = {
    'primary': '#6366f1',      # Indigo
    'secondary': '#ec4899',    # Pink
    'success': '#10b981',      # Emerald
    'info': '#06b6d4',         # Cyan
    'warning': '#f59e0b',      # Amber
    'purple': '#a855f7',       # Purple
}

def create_branch_chart(df):
    """1. แผนภูมิวงกลมแสดงสัดส่วนสมาชิกตามสาขา"""
    if "Branch_code" not in df.columns or df["Branch_code"].isnull().all():
        return px.bar(title="ไม่พบข้อมูล Branch_code")

    df['Branch_code_Str'] = df['Branch_code'].astype(str)
    df_branch = df["Branch_code_Str"].value_counts().reset_index()
    df_branch.columns = ["Branch_code", "จำนวนสมาชิก"]

    fig = px.pie(
        df_branch,
        names="Branch_code",
        values="จำนวนสมาชิก",
        title="สัดส่วนสมาชิกตามสาขา",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        textfont_size=12
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#64748b', size=12),
        title=dict(font=dict(size=16, color='#1e293b'), x=0.5),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    return fig


def create_age_distribution_chart(df):
    """2. แผนภูมิแท่งแสดงจำนวนสมาชิกตามช่วงอายุ"""
    if "Age_Group" not in df.columns or df["Age_Group"].isnull().all():
        return px.bar(title="ไม่พบข้อมูล Age_Group")

    df_age = df["Age_Group"].value_counts().reset_index()
    df_age.columns = ["Age_Group", "จำนวนสมาชิก"]
    
    age_order = ['< 20', '20-29', '30-39', '40-49', '50-59', '60+']

    fig = px.bar(
        df_age,
        x="Age_Group",
        y="จำนวนสมาชิก",
        category_orders={"Age_Group": age_order},
        title="จำนวนสมาชิกตามช่วงอายุ",
        color="Age_Group",
        color_discrete_sequence=[COLORS['primary'], COLORS['info'], COLORS['success'], 
                                COLORS['warning'], COLORS['secondary'], COLORS['purple']]
    )
    fig.update_traces(marker_line_color='white', marker_line_width=1.5)
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#64748b', size=12),
        title=dict(font=dict(size=16, color='#1e293b'), x=0.5),
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#f1f5f9')
    )
    return fig


def create_approval_time_chart(df):
    """3. แผนภูมิแสดงระยะเวลาอนุมัติ"""
    if "Approval_days" not in df.columns or df["Approval_days"].isnull().all():
        return px.bar(title="ไม่พบข้อมูล Approval_days")

    fig = px.histogram(
        df,
        x="Approval_days",
        nbins=20, 
        title="ระยะเวลาอนุมัติสมาชิก (วัน)",
        labels={"Approval_days": "จำนวนวัน"}
    )
    
    fig.update_traces(marker_color=COLORS['info'], marker_line_color='white', marker_line_width=1)
    fig.update_xaxes(dtick=1, range=[0, 10])
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#64748b', size=12),
        title=dict(font=dict(size=16, color='#1e293b'), x=0.5),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#f1f5f9')
    )
    return fig


def create_income_distribution_chart(df):
    """4. แผนภูมิรายได้ที่พบบ่อย Top 10"""
    if "Income_Clean" not in df.columns or df["Income_Clean"].isnull().all():
        return px.bar(title="ไม่พบข้อมูล Income_Clean")

    df_filtered = df[df["Income_Clean"] > 0]
    df_income_counts = df_filtered["Income_Clean"].value_counts().reset_index()
    df_income_counts.columns = ['รายได้ (บาท)', 'จำนวนสมาชิก']
    df_top_income = df_income_counts.sort_values('จำนวนสมาชิก', ascending=False).head(10)
    
    mode_income_value = "N/A"
    if not df_filtered.empty and len(df_filtered["Income_Clean"].mode()) > 0:
        mode_income_value = f"{df_filtered['Income_Clean'].mode().iloc[0]:,.0f}"

    fig = px.bar(
        df_top_income,
        x='รายได้ (บาท)',
        y='จำนวนสมาชิก',
        title=f'รายได้ที่พบบ่อย (Mode: {mode_income_value} บาท)',
        color='จำนวนสมาชิก',
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#64748b', size=12),
        title=dict(font=dict(size=16, color='#1e293b'), x=0.5),
        xaxis=dict(tickformat=",", showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#f1f5f9'),
        showlegend=False
    )
    return fig


def create_popular_career_chart(df):
    """5. แผนภูมิอาชีพยอดนิยม"""
    if "Career" not in df.columns:
        return px.bar(title="ไม่พบข้อมูล Career")

    df_career_counts = (
        df["Career"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace('', pd.NA)
        .dropna()
        .value_counts()
        .reset_index()
    )
    df_career_counts.columns = ['อาชีพ', 'จำนวนสมาชิก']
    df_top_career = df_career_counts.head(10)
    
    fig = px.bar(
        df_top_career,
        x="จำนวนสมาชิก",
        y="อาชีพ",
        orientation="h",
        title="อาชีพยอดนิยม Top 10",
        color="จำนวนสมาชิก",
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#64748b', size=12),
        title=dict(font=dict(size=16, color='#1e293b'), x=0.5),
        yaxis={"categoryorder": "total ascending"},
        xaxis=dict(showgrid=True, gridcolor='#f1f5f9'),
        yaxis_title="",
        showlegend=False
    )
    
    return fig
    
    
def create_monthly_registration_chart(df):
    """6. แผนภูมิสมาชิกใหม่รายเดือน"""
    if 'registration_date' not in df.columns:
        return px.line(title="ไม่พบข้อมูล registration_date")

    df_reg = df.dropna(subset=['registration_date']).copy()
    df_reg['MonthYear'] = df_reg['registration_date'].dt.to_period('M').astype(str)
    
    df_monthly = df_reg.groupby('MonthYear').size().reset_index(name='จำนวนสมาชิก')
    df_monthly['DateSort'] = pd.to_datetime(df_monthly['MonthYear'])
    df_monthly = df_monthly.sort_values('DateSort')
    
    fig = px.line(
        df_monthly,
        x='MonthYear',
        y='จำนวนสมาชิก',
        markers=True,
        title="สมาชิกใหม่รายเดือน",
        labels={"MonthYear": "เดือน-ปี", "จำนวนสมาชิก": "จำนวนสมาชิก"}
    )
    
    fig.update_traces(
        line_color=COLORS['primary'],
        line_width=3,
        marker=dict(size=8, color=COLORS['secondary'], line=dict(width=2, color='white'))
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#000000", size=12),
        title=dict(font=dict(size=16, color='#1e293b'), x=0.5),
        hovermode="x unified",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#f1f5f9')
    )
    
    return fig


# ==================================================
# Layout (ปรับให้เรียบง่ายและสวยงาม)
# ==================================================

def create_analysis_layout():
    df = load_data() 
    df = preprocess_data(df) 
    
    if df.empty:
        return dbc.Container(
            dbc.Alert(
                [
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    "ไม่พบข้อมูลสำหรับการวิเคราะห์ กรุณาตรวจสอบการเชื่อมต่อ",
                ],
                color="warning",
                className="mt-5 text-center",
            ),
            fluid=True,
        )

    # สร้างกราฟทั้งหมด
    fig_branch = create_branch_chart(df)
    fig_age = create_age_distribution_chart(df)
    fig_approval = create_approval_time_chart(df)
    fig_income_dist = create_income_distribution_chart(df) 
    fig_popular_career = create_popular_career_chart(df)
    fig_monthly_reg = create_monthly_registration_chart(df)

    return dbc.Container(
        fluid=True,
        className="py-4 px-3",
        style={"backgroundColor": "#f8fafc"},
        children=[
            # Header แบบเรียบง่าย
            html.Div(
                [
                    html.H2(
                        "📊 วิเคราะห์ข้อมูลสมาชิก",
                        className="mb-1",
                        style={"color": "#1e293b", "fontWeight": "600"}
                    ),
                    html.P(
                        "ภาพรวมและแนวโน้มสำคัญ",
                        className="text-muted mb-0",
                        style={"fontSize": "0.95rem"}
                    ),
                ],
                className="mb-4"
            ),

            # KPI Cards
            render_kpi_cards(df),

            # Divider เรียบง่าย
            html.Hr(style={"borderTop": "2px solid #e2e8f0", "margin": "2rem 0"}),

            # Grid ของกราฟ - ใช้ Card สีขาวพื้นฐาน
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(dcc.Graph(figure=fig_branch, config={'displayModeBar': False})),
                            className="shadow-sm border-0 mb-4"
                        ),
                        lg=6
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(dcc.Graph(figure=fig_age, config={'displayModeBar': False})),
                            className="shadow-sm border-0 mb-4"
                        ),
                        lg=6
                    ),
                ],
                className="g-3"
            ),

            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(dcc.Graph(figure=fig_approval, config={'displayModeBar': False})),
                            className="shadow-sm border-0 mb-4"
                        ),
                        lg=6
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(dcc.Graph(figure=fig_income_dist, config={'displayModeBar': False})),
                            className="shadow-sm border-0 mb-4"
                        ),
                        lg=6
                    ),
                ],
                className="g-3"
            ),
            
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(dcc.Graph(figure=fig_popular_career, config={'displayModeBar': False})),
                            className="shadow-sm border-0 mb-4"
                        ),
                        lg=6
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(dcc.Graph(figure=fig_monthly_reg, config={'displayModeBar': False})),
                            className="shadow-sm border-0 mb-4"
                        ),
                        lg=6
                    ),
                ],
                className="g-3"
            )
        ],
    )

try:
    layout = create_analysis_layout()
except Exception as e:
    print(f"Error creating analysis layout: {e}")
    layout = dbc.Container(
        dbc.Alert("เกิดข้อผิดพลาดในการโหลดข้อมูล", color="danger", className="mt-5")
    )


# ==================================================
# Callbacks
# ==================================================

def register_callbacks(app):
    pass