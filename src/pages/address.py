from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from ..data_manager import load_data
from ..components.kpi_cards import render_address_kpis

# ความสูงเท่ากันทุก dashboard
CHART_HEIGHT = 340

# ==================================================
# 1. Data Processing (Geo)
# ==================================================
def get_processed_data():
    df = load_data()
    if df.empty:
        return df

    geo_cols = ['province_name', 'district_area', 'sub_area']
    for col in geo_cols:
        if col in df.columns:
            df[col] = df[col].fillna("ไม่ระบุ")

    if "income" in df.columns:
        df["Income_Clean"] = (
            df["income"]
            .astype(str)
            .str.replace(",", "")
            .astype(float)
            .fillna(0)
        )

    return df

# ==================================================
# 2. Layout Helper
# ==================================================
def apply_layout(fig, title, height=CHART_HEIGHT):
    fig.update_layout(
        title={
            'text': f"<b>{title}</b>",
            'font': {'size': 16, 'color': '#0f172a', 'family': 'Sarabun, sans-serif'},
            'x': 0.02,
            'xanchor': 'left'
        },
        plot_bgcolor="rgba(255, 255, 255, 0.02)",
        paper_bgcolor="rgba(255, 255, 255, 0)",
        height=height,
        font=dict(family="Sarabun, sans-serif", size=11, color='#334155'),
        margin=dict(t=50, b=40, l=50, r=30),
        hoverlabel=dict(
            bgcolor="rgba(15, 23, 42, 0.95)",
            font_size=12,
            font_family="Sarabun, sans-serif",
            font_color="white",
            bordercolor="rgba(148, 163, 184, 0.3)"
        )
    )
    return fig

# ==================================================
# 3. Charts 
# ==================================================

def chart_province_age_distribution(df):
    top_6_prov = df['province_name'].value_counts().nlargest(6).index
    df_sub = df[df['province_name'].isin(top_6_prov)].copy()

    df_sub['Age_Group'] = df_sub['Age_Group'].astype(str)
    age_order = sorted(df_sub['Age_Group'].unique())

    summary = (
        df_sub.groupby(['province_name', 'Age_Group'])
        .size()
        .reset_index(name='member_count')
    )

    fig = px.bar(
        summary,
        x='Age_Group',
        y='member_count',
        color='Age_Group',
        facet_col='province_name',
        facet_col_wrap=3,
        text='member_count',
        category_orders={"Age_Group": age_order},
        labels={'Age_Group': 'ช่วงอายุ', 'member_count': 'จำนวนคน'},
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    fig.update_traces(
        textposition='outside', 
        textfont=dict(size=10, family="Sarabun"),
        marker=dict(line=dict(color='white', width=1))
    )

    fig.update_layout(
        showlegend=False,
        margin=dict(t=80, b=50, l=40, r=40),
        font=dict(family="Sarabun", size=11),
        height=CHART_HEIGHT,
        bargap=0.3,
        paper_bgcolor='rgba(255, 255, 255, 0)',
        plot_bgcolor='rgba(248, 250, 252, 0.3)'
    )

    fig.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>"))
    fig.update_yaxes(showticklabels=False, showgrid=False, title="")
    fig.update_xaxes(title="", tickfont=dict(size=10))

    return apply_layout(fig, "สัดส่วนประชากรแยกตามช่วงอายุ (Top 6 จังหวัด)", CHART_HEIGHT)

def chart_province_career(df):
    top_5_prov = df['province_name'].value_counts().nlargest(5).index
    sub_df = df[df['province_name'].isin(top_5_prov)].copy()

    top_careers = sub_df['career_name'].value_counts().nlargest(5).index
    sub_df['career_group'] = sub_df['career_name'].apply(
        lambda x: x if x in top_careers else "อื่นๆ"
    )

    summary = sub_df.groupby(['province_name', 'career_group']).size().reset_index(name='count')
    
    fig = px.bar(
        summary,
        x='province_name',
        y='count',
        color='career_group',
        color_discrete_sequence=px.colors.qualitative.T10,
        labels={'count': 'จำนวนคน', 'province_name': 'จังหวัด', 'career_group': 'อาชีพหลัก'}
    )

    fig.update_layout(
        barmode='stack',
        barnorm='percent',
        legend=dict(
            title="<b>อาชีพหลัก</b>",
            orientation="h",
            xanchor="center",
            yanchor="top",
            x=0.5,
            y=-0.20,
            font=dict(size=10, family='Sarabun'),
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="rgba(148, 163, 184, 0.3)",
            borderwidth=1
        ),
        bargap=0.3,
        margin=dict(t=50, b=75, l=50, r=30),
        paper_bgcolor='rgba(255, 255, 255, 0)',
        plot_bgcolor='rgba(248, 250, 252, 0.3)'
    )

    fig.update_traces(
        marker_line_width=1.5,
        marker_line_color="white",
        hovertemplate="<b>จังหวัด:</b> %{x}<br><b>อาชีพ:</b> %{fullData.name}<br><b>สัดส่วน:</b> %{y:.1f}%<extra></extra>"
    )

    fig.update_xaxes(
        title="<b>จังหวัด</b>",
        showgrid=False,
        tickfont=dict(size=11, color='#0f172a', family='Sarabun')
    )

    fig.update_yaxes(
        title="<b>สัดส่วน (%)</b>",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(203, 213, 225, 0.4)',
        tickfont=dict(size=11, color='#334155')
    )

    return apply_layout(fig, "วิเคราะห์สัดส่วนอาชีพรายจังหวัด (100% Stacked)", CHART_HEIGHT)

def chart_income_gap_analysis(df):
    summary = (
        df.groupby('province_name')['Income_Clean']
        .agg(['mean', 'median'])
        .nlargest(8, 'mean')
        .reset_index()
    )
    
    col_mean = 'รายได้เฉลี่ยต่อคน'
    col_median = 'รายได้คนส่วนใหญ่'
    
    summary = summary.rename(columns={
        'mean': col_mean,
        'median': col_median
    })

    fig = px.bar(
        summary, 
        x='province_name', 
        y=[col_mean, col_median],
        barmode='group', 
        color_discrete_map={
            col_mean: '#1e3a8a',
            col_median: '#94a3b8'
        },
        labels={
            'province_name': 'จังหวัด',
            'value': 'จำนวนเงิน (บาท)',
            'variable': 'กลุ่มการวัด'
        }
    )

    fig.update_traces(
        texttemplate='฿%{value:,.0f}', 
        textposition='outside',        
        textfont=dict(size=10, color='#1e293b', family='Sarabun'),
        marker_line_color='white',
        marker_line_width=1.5
    )

    fig.update_layout(
        legend=dict(
            title="<b>สถิติรายได้</b>",
            orientation="h",
            xanchor="center",
            yanchor="top",
            x=0.5,
            y=-0.30,
            font=dict(size=11, family='Sarabun'),
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="rgba(148, 163, 184, 0.3)",
            borderwidth=1
        ),
        margin=dict(l=60, r=30, t=50, b=75),
        hovermode="x unified",
        paper_bgcolor='rgba(255, 255, 255, 0)',
        plot_bgcolor='rgba(248, 250, 252, 0.3)'
    )

    fig.update_xaxes(
        title="",
        showgrid=False,
        tickfont=dict(size=11, family="Sarabun", color='#0f172a')
    )

    fig.update_yaxes(
        title="<b>จำนวนเงิน (บาท)</b>",
        tickformat=",",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(203, 213, 225, 0.4)',
        range=[0, summary[col_mean].max() * 1.2],
        tickfont=dict(size=11, color='#334155')
    )

    return apply_layout(fig, "วิเคราะห์ช่องว่างรายได้: ค่าเฉลี่ย vs ค่าคนส่วนใหญ่", CHART_HEIGHT)

def chart_top_subdistricts(df):
    counts = (
        df.groupby(['sub_area', 'province_name'])
        .size()
        .reset_index(name='count')
        .sort_values('count', ascending=False)
        .head(10)
    )
    counts['label'] = counts['sub_area'] + " (" + counts['province_name'] + ")"

    gradient_colors = ['#1e3a8a', '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd',
                       '#1e40af', '#1e3a8a', '#1d4ed8', '#2563eb', '#3b82f6']

    fig = go.Figure()

    for i, row in counts.iterrows():
        fig.add_trace(go.Bar(
            y=[row['label']],
            x=[row['count']],
            orientation='h',
            marker=dict(
                color=gradient_colors[i % len(gradient_colors)],
                line=dict(color='white', width=2)
            ),
            text=f"<b>{row['count']}</b>",
            textposition='outside',
            textfont=dict(size=11, family='Sarabun'),
            hovertemplate=f"<b>{row['label']}</b><br>จำนวน: %{{x}} คน<extra></extra>",
            showlegend=False
        ))

    fig.update_layout(
        margin=dict(t=50, b=40, l=150, r=30),
        paper_bgcolor='rgba(255, 255, 255, 0)',
        plot_bgcolor='rgba(248, 250, 252, 0.3)'
    )

    fig.update_xaxes(
        title="<b>จำนวนคน</b>",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(203, 213, 225, 0.4)',
        tickfont=dict(size=11, color='#334155')
    )

    fig.update_yaxes(
        title="<b>ตำบล (จังหวัด)</b>",
        showgrid=False,
        tickfont=dict(size=11, color='#0f172a', family='Sarabun')
    )

    return apply_layout(fig, "10 อันดับตำบลที่มีความหนาแน่นสูงสุด", CHART_HEIGHT)

# ==================================================
# 4. Main Layout
# ==================================================
def create_geographic_layout():
    df = get_processed_data()
    if df.empty:
        return dbc.Container(
            dbc.Alert("ไม่พบข้อมูลที่อยู่", color="warning", className="mt-5")
        )

    card = lambda fig: dbc.Card(
        dbc.CardBody(
            dcc.Graph(
                figure=fig,
                config={'displayModeBar': False, 'responsive': True}
            ),
            style={"padding": "18px"}
        ),
        className="shadow-sm rounded-3 border-0 mb-3",
        style={
            "backgroundColor": "rgba(255, 255, 255, 0.98)",
            "backdropFilter": "blur(10px)",
            "border": "1px solid rgba(203, 213, 225, 0.5) !important",
            "transition": "all 0.3s ease",
            "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.08)",
        }
    )

    return dbc.Container(
        fluid=True,
        style={
            "backgroundColor": "transparent",
            "padding": "20px 30px",
            "maxWidth": "1400px",
            "margin": "0 auto"
        },
        children=[
            html.Div([
                html.H3(
                    "การวิเคราะห์เชิงพื้นที่",
                    className="fw-bold mb-3",
                    style={
                        "color": "#0f172a",
                        "letterSpacing": "0.5px",
                        "fontSize": "26px",
                        "fontFamily": "Sarabun, sans-serif",
                        "textShadow": "0 2px 4px rgba(0,0,0,0.05)",
                        "position": "relative",
                        "paddingBottom": "10px"
                    }
                ),
            ]),

            render_address_kpis(df),

            dbc.Row([
                dbc.Col(card(chart_province_age_distribution(df)), xs=12)
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col(card(chart_province_career(df)), xs=12, lg=6),
                dbc.Col(card(chart_income_gap_analysis(df)), xs=12, lg=6),
            ], className="g-3 mb-3"),

            dbc.Row([
                dbc.Col(card(chart_top_subdistricts(df)), xs=12, lg=6),
            ], className="g-3"),
        ],
    )

layout = create_geographic_layout()