import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from functools import lru_cache

from ..data_manager import load_data
from ..components.kpi_cards import render_address_kpis
from ..components.chart_card import chart_card
from ..components.theme import THEME

# ==================================================
# Config
# ==================================================
CHART_HEIGHT = 500 
UI_REVISION_KEY = "geo-static" # ล็อกสถานะกราฟข้ามการรีเฟรช

# ==================================================
# Data Processing & Cache (Logic เดิม)
# ==================================================
def preprocess_geographic(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    cols = ["province_name", "district_area", "sub_area", "village_name"]
    for col in cols:
        if col in df.columns:
            df[col] = df[col].fillna("ไม่ระบุ")
    return df

@lru_cache(maxsize=1)
def load_address_data():
    return preprocess_geographic(load_data())

# ==================================================
# 3. Layout Helper (Standardized Font & Margins)
# ==================================================
def apply_address_layout(fig, height=CHART_HEIGHT, right_margin=30):
    fig.update_layout(
        autosize=True,
        height=height,
        uirevision=UI_REVISION_KEY,
        # ปรับ Margin ให้เท่ากับหน้า Branch (t=40, b=35, l=45, r=30)
        margin=dict(t=40, b=35, l=10, r=right_margin), 
        paper_bgcolor=THEME["paper"],
        plot_bgcolor=THEME["bg_plot"],
        font=dict(
            family="Sarabun, sans-serif", 
            size=13, # ขนาดฟอนต์มาตรฐาน 13
            color=THEME["text"]
        ),
        transition={'duration': 0}
    )
    fig.update_coloraxes(showscale=False)
    return fig

def get_drilldown_chart(df, level="province"):
    col_map = {
        "province": "province_name",
        "district": "district_area",
        "sub_district": "sub_area",
        "village": "village_name"
    }
    target_col = col_map.get(level, "province_name")
    
    if target_col not in df.columns or df.empty:
        fig = go.Figure()
        fig.add_annotation(text="ไม่พบข้อมูลในระดับนี้", showarrow=False)
        return apply_address_layout(fig)

    counts = df[target_col].value_counts().reset_index()
    counts.columns = [target_col, "count"]
    
    # Coloring: ใช้ชุดสีตามลำดับความลึก
    color_scales = {
        "province": px.colors.sequential.Purples_r,
        "district": px.colors.sequential.Blues_r,
        "sub_district": px.colors.sequential.Teal_r, 
        "village": px.colors.sequential.Greens_r
    }

    fig = px.treemap(
        counts,
        path=[target_col], 
        values='count',
        color='count',
        color_continuous_scale=color_scales.get(level, "Purples")
    )
    
    fig.update_traces(
        textinfo="label+value",
        # ปรับแต่ง Text และขนาด Font ภายในกล่อง Treemap
        texttemplate="<span style='font-size: 15px'>%{label}</span><br><span style='font-size: 22px'><b>%{value:,}</b></span>",
        hovertemplate="<b>%{label}</b><br>จำนวน: %{value:,} คน<extra></extra>",
        marker=dict(line=dict(width=1, color='white')),
        textposition="middle center"
    )
    
    return apply_address_layout(fig)

# ==================================================
# Layout (Logic โครงสร้างเดิม)
# ==================================================
def address_layout():
    df = load_address_data()
    initial_fig = get_drilldown_chart(df, "province")
    
    return dbc.Container(
        fluid=True,
        style={"padding": "20px 30px", "maxWidth": "1400px", "margin": "0 auto"},
        children=[
            dcc.Store(id='drill-path', data={'level': 'province', 'filters': {}}),
            
            html.Div([
                html.Div([
                    html.H3("วิเคราะห์สัดส่วนข้อมูลพื้นที่", className="fw-bold mb-0"),
                    html.P("คลิกที่กล่องเพื่อเจาะลึก หรือกดไอคอนย้อนกลับมุมขวา", className="text-muted mb-0")
                ]),
            ], className="d-flex justify-content-between align-items-end mb-4"),

            render_address_kpis(df),

            dbc.Row([
                dbc.Col([
                    html.Div([
                        dbc.Button(
                            html.Div([
                                html.I(className="bi bi-arrow-left", style={"marginRight": "8px", "color": THEME["primary"], "fontSize": "1.1rem"}),
                                html.Span("ย้อนกลับ")
                            ], className="d-flex align-items-center"),
                            id="btn-icon-reset",
                            color="light",
                            style={
                                "position": "absolute", "top": "15px", "right": "15px", "zIndex": "100",
                                "borderRadius": "20px", "display": "none", "boxShadow": "0 2px 5px rgba(0,0,0,0.1)"
                            },
                        ),
                        html.Div(id="drill-card-wrapper", children=[
                            chart_card(
                                dcc.Graph(
                                    id='drill-graph', figure=initial_fig, 
                                    config={"displayModeBar": False},
                                    style={"height": f"{CHART_HEIGHT}px"} 
                                ),
                                title="จำนวนสมาชิกตามจังหวัด"
                            )
                        ])
                    ], style={"position": "relative"}) 
                ], width=12)
            ], className="g-3")
        ]
    )

# Callback (ยังคง Logic การทำงานเดิมทั้งหมด)
@callback(
    [Output('drill-card-wrapper', 'children'),
     Output('drill-path', 'data'),
     Output('btn-icon-reset', 'style')],
    [Input('drill-graph', 'clickData'),
     Input('btn-icon-reset', 'n_clicks')],
    [State('drill-path', 'data'),
     State('btn-icon-reset', 'style')],
    prevent_initial_call=True
)
def handle_geo_drilldown(clickData, btn_clicks, current_state, current_btn_style):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    df = load_address_data()
    level = current_state.get('level', 'province')
    filters = current_state.get('filters', {})

    if triggered_id == 'btn-icon-reset':
        level = 'province'; filters = {}
    elif clickData:
        try:
            selected_loc = clickData['points'][0]['label']
            if level == 'province':
                level = 'district'; filters['province_name'] = selected_loc
            elif level == 'district':
                level = 'sub_district'; filters['district_area'] = selected_loc
            elif level == 'sub_district':
                level = 'village'; filters['sub_area'] = selected_loc
        except: pass

    dff = df.copy()
    for col, val in filters.items():
        if col in dff.columns: dff = dff[dff[col] == val]

    fig = get_drilldown_chart(dff, level)
    
    titles = {
        "province": "สัดส่วนสมาชิกแยกตามจังหวัด",
        "district": f"อำเภอใน {filters.get('province_name', '')}",
        "sub_district": f"ตำบลใน {filters.get('district_area', '')}",
        "village": f"หมู่บ้านใน {filters.get('sub_area', '')}"
    }
    
    new_card = chart_card(
        dcc.Graph(id='drill-graph', figure=fig, config={"displayModeBar": False}, style={"height": f"{CHART_HEIGHT}px"}),
        title=titles.get(level, "ข้อมูลพื้นที่")
    )

    new_btn_style = current_btn_style.copy()
    new_btn_style["display"] = "none" if level == 'province' else "block"
    
    return new_card, {'level': level, 'filters': filters}, new_btn_style

layout = address_layout()