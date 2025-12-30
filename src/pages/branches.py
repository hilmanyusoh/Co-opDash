from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from ..data_manager import load_data
from ..components.kpi_cards import render_branch_kpis

# ==================================================
# 1. Data Processing
# ==================================================
def get_processed_data():
    df = load_data()
    if df.empty:
        return df

    df['registration_date'] = pd.to_datetime(df['registration_date'], errors='coerce')
    df['approval_date'] = pd.to_datetime(df['approval_date'], errors='coerce')
    df['Days_to_Approve'] = (df['approval_date'] - df['registration_date']).dt.days
    df.loc[df['Days_to_Approve'] < 0, 'Days_to_Approve'] = 0

    if "income" in df.columns:
        df["Income_Clean"] = (
            df["income"]
            .astype(str)
            .str.replace(",", "")
            .astype(float)
            .fillna(0)
        )

    branch_map = {
        1: "สาขา 1",
        2: "สาขา 2",
        3: "สาขา 3",
        4: "สาขา 4",
        5: "สาขา 5",
    }

    if "branch_no" in df.columns:
        df["branch_name"] = df["branch_no"].map(branch_map).fillna(
            df["branch_no"].astype(str).apply(lambda x: f"สาขา {x}")
        )

    return df


# ==================================================
# 2. Layout Helper (มาตรฐานเดียวกันทุกกราฟ)
# ==================================================
def apply_layout(fig, title, legend_pos="top"):
    fig.update_layout(
        title=f"<b>{title}</b>",
        height=340,  # 🔴 ล็อกความสูงกราฟ
        font=dict(family="Sarabun, sans-serif"),
        plot_bgcolor="rgba(245, 247, 250, 0.4)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=50, r=50, t=80, b=50),
        hovermode="x unified",
    )

    if legend_pos == "top":
        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.05,
                xanchor="center",
                x=0.5,
            ),
        )
    elif legend_pos == "right":
        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.02,
            ),
        )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.05)")
    return fig


# ==================================================
# 3. Charts
# ==================================================

# 1) จำนวนสมาชิกต่อสาขา
def chart_member_column(df):
    # เตรียมข้อมูล
    counts = (
        df["branch_name"]
        .value_counts()
        .sort_index()
        .reset_index()
    )
    counts.columns = ["branch_name", "count"]

    # ชุดสีเข้มพรีเมียม
    dark_colors = ['#1e3a8a', '#b91c1c', '#15803d', '#b45309', '#6d28d9', '#0369a1', '#be185d', '#475569']

    fig = px.bar(
        counts,
        x="branch_name",
        y="count",
        color="branch_name",
        text="count",
        color_discrete_sequence=dark_colors,
        labels={"branch_name": "ชื่อสาขา", "count": "จำนวนสมาชิก"},
    )
    
    # เพิ่มมิตินูนด้วยขอบขาวหนาและลดความโปร่งแสงเล็กน้อย
    fig.update_traces(
        textposition="outside", 
        texttemplate="<b>%{text}</b> คน",
        textfont=dict(size=12, family='Sarabun', color='#1e293b'),
        marker_line_color='#ffffff', 
        marker_line_width=2, 
        opacity=0.95
    )

    fig.update_xaxes(
        title="<b>รายชื่อสาขา</b>",
        showgrid=False, # กราฟแนวตั้ง (Column) มักจะไม่โชว์ Grid แนวตั้งเพื่อให้ดูสะอาด
        showline=True,
        linewidth=2.5,
        linecolor='#94a3b8',
        tickfont=dict(size=12, color='#0f172a', family='Sarabun')
    )
    
    fig.update_yaxes(
        title="<b>จำนวนสมาชิก (คน)</b>",
        showgrid=True,
        gridwidth=1,
        gridcolor='#e2e8f0', 
        showline=False,
        zeroline=True,
        zerolinecolor='#94a3b8',
        zerolinewidth=2,
        tickfont=dict(size=12, color='#334155', family='Sarabun')
    )

    # เรียกใช้ฟังก์ชันจัดการ Layout หลัก (ปรับชื่อให้ตรงกับที่คุณใช้ในโปรเจกต์)
    # ในที่นี้ผมใช้สไตล์ Legend ขวาตามที่คุณแจ้งไว้ก่อนหน้า
    return apply_layout(fig, "1. จำนวนสมาชิกแต่ละสาขา", 420)

def chart_income_line(df):
    # คำนวณรายได้เฉลี่ยรายสาขา
    avg_income = (
        df.groupby("branch_name")["Income_Clean"]
        .mean()
        .sort_index()
        .reset_index()
    )

    fig = go.Figure()
    
    # เพิ่มเส้นกราฟรายได้
    fig.add_trace(
        go.Scatter(
            x=avg_income["branch_name"],
            y=avg_income["Income_Clean"],
            mode="lines+markers+text",
            name="รายได้เฉลี่ย",
            # เส้น Spline หนา สีเขียวมรกตเข้ม
            line=dict(color="#059669", width=4, shape="spline"),
            # Marker จุดตัดข้อมูล
            marker=dict(
                size=12,
                color="white",
                line=dict(color="#059669", width=3),
            ),
            # เติมสีจางๆ ใต้กราฟเพื่อให้ดูมีมิตินูน
            fill="tozeroy",
            fillcolor="rgba(5, 150, 105, 0.08)",
            # แสดงตัวเลขรายได้บนจุด (เฉพาะตัวเลขที่สำคัญ)
            text=[f"฿{val:,.0f}" for val in avg_income["Income_Clean"]],
            textposition="top center",
            # ปรับ Hover ให้สวยงาม
            hovertemplate="<b>สาขา: %{x}</b><br>รายได้เฉลี่ย: ฿%{y:,.2f}<extra></extra>"
        )
    )

    # ปรับแต่งแกน X (รายชื่อสาขา)
    fig.update_xaxes(
        title="<b>รายชื่อสาขา</b>",
        showgrid=False,
        showline=True,
        linewidth=2.5,
        linecolor='#94a3b8',
        tickfont=dict(size=12, color='#0f172a', family='Sarabun')
    )
    
    # ปรับแต่งแกน Y (รายได้)
    fig.update_yaxes(
        title="<b>รายได้เฉลี่ย (บาท)</b>",
        showgrid=True,
        gridwidth=1,
        gridcolor='#e2e8f0', 
        showline=False,
        zeroline=True,
        zerolinecolor='#94a3b8',
        zerolinewidth=2,
        tickformat=',.0f', # ใส่คอมม่าในแกน
        tickfont=dict(size=12, color='#334155', family='Sarabun')
    )

    # เรียกใช้สไตล์หลัก (Legend ขวา ตามมาตรฐาน Dashboard ของคุณ)
    return apply_layout(fig, "2. รายได้เฉลี่ยต่อคนรายสาขา", 420)


# 3) ความเร็วการอนุมัติ (Mode)
def chart_approval_mode(df):
    def mode_val(x):
        m = x.mode()
        return m.iloc[0] if not m.empty else 0

    # ดึงค่าฐานนิยม (Mode) ของจำนวนวันที่ใช้ในการอนุมัติ
    branch_modes = (
        df.groupby("branch_name")["Days_to_Approve"]
        .apply(mode_val)
        .sort_values(ascending=True) # เรียงเพื่อให้ตัวที่ช้าที่สุดอยู่ด้านบน
        .reset_index()
    )

    # กำหนดสีตามเกณฑ์ประสิทธิภาพ (Threshold)
    colors = [
        "#b91c1c" if v > 5 else "#b45309" if v > 2 else "#15803d"
        for v in branch_modes["Days_to_Approve"]
    ]

    fig = go.Figure()
    
    # กราฟแท่งแนวนอน
    fig.add_trace(
        go.Bar(
            y=branch_modes["branch_name"],
            x=branch_modes["Days_to_Approve"],
            orientation="h",
            marker=dict(
                color=colors,
                line=dict(color='#ffffff', width=2), # มิตินูนด้วยขอบขาว
                opacity=0.9
            ),
            text=[f"<b>{int(v)} วัน</b>" for v in branch_modes["Days_to_Approve"]],
            textposition="outside",
            textfont=dict(family="Sarabun", size=12, color="#1e293b"),
            hovertemplate="<b>สาขา: %{y}</b><br>ระยะเวลาอนุมัติหลัก: %{x} วัน<extra></extra>",
            showlegend=False,
        )
    )

    # สร้าง Legend จำลอง (Custom Legend) เพื่ออธิบายความหมายของสี
    for label, color in [
        ("เร็ว (≤2 วัน)", "#15803d"),
        ("ปกติ (3–5 วัน)", "#b45309"),
        ("ช้า (>5 วัน)", "#b91c1c"),
    ]:
        fig.add_trace(go.Bar(
            x=[None], y=[None], name=label, marker_color=color,
            marker_line=dict(color='white', width=1)
        ))

    # ปรับแต่งแกน
    fig.update_xaxes(title="<b>จำนวนวัน</b>", showgrid=True, gridcolor='#e2e8f0', range=[0, max(branch_modes["Days_to_Approve"]) + 2])
    fig.update_yaxes(title="<b>สาขา</b>", showline=True, linecolor='#94a3b8', linewidth=2)

    return apply_layout(fig, "3. ความเร็วการอนุมัติหลัก (Mode)", 420)


def chart_member_income_dual(df):
    summary = df.groupby("branch_name").agg(
        member_count=("member_id", "count"),
        total_income=("Income_Clean", "sum")
    ).sort_values("member_count", ascending=False).reset_index()

    fig = go.Figure()

    # 1. แท่งกราฟ (แกน Y หลัก)
    fig.add_trace(go.Bar(
        x=summary["branch_name"],
        y=summary["member_count"],
        name="จำนวนสมาชิก (คน)",
        marker=dict(color="#1e3a8a", opacity=0.85, line=dict(color='white', width=1)),
        text=summary["member_count"],
        textposition="outside",
        hovertemplate="สมาชิก: %{y:,} คน<extra></extra>"
    ))

    # 2. เส้นกราฟ (แกน Y ที่สอง)
    fig.add_trace(go.Scatter(
        x=summary["branch_name"],
        y=summary["total_income"],
        name="รายได้รวม (บาท)",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color="#b91c1c", width=4, shape='spline'),
        marker=dict(size=10, symbol="diamond", color="#b91c1c", line=dict(color='white', width=2)),
        hovertemplate="รายได้รวม: ฿%{y:,.0f}<extra></extra>"
    ))

    # 3. การตั้งค่า Layout (แก้ไขจุดที่ Error)
    fig.update_layout(
        # แกน Y ฝั่งซ้าย
        yaxis=dict(
            title=dict(
                text="<b>จำนวนสมาชิก (คน)</b>",
                font=dict(size=14, color="#1e3a8a", family="Sarabun") #
            ),
            tickfont=dict(color="#1e3a8a", size=12),
            showgrid=True,
            gridcolor='rgba(226, 232, 240, 0.6)'
        ),
        # แกน Y ฝั่งขวา
        yaxis2=dict(
            title=dict(
                text="<b>รายได้รวม (บาท)</b>",
                font=dict(size=14, color="#b91c1c", family="Sarabun")
            ),
            tickfont=dict(color="#b91c1c", size=12),
            anchor="x",
            overlaying="y",
            side="right",
            tickformat=",",
            showgrid=False
        ),
        # จัดการ Legend ให้สมดุล
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.0,
            xanchor="center", x=0.5
        ),
        margin=dict(l=70, r=70, t=100, b=70),
        hovermode="x unified",
        plot_bgcolor="rgba(248, 250, 252, 0.5)"
    )

    # ปรับแต่งแกน X
    fig.update_xaxes(
        title=dict(text="<b>รายชื่อสาขา</b>", font=dict(family="Sarabun", size=14)),
        showline=True,
        linewidth=2,
        linecolor='#94a3b8'
    )

    return apply_layout(fig, "4. เปรียบเทียบจำนวนสมาชิกและรายได้รวมรายสาขา", 450)
# ==================================================
# 4. Main Layout
# ==================================================
def create_branch_layout():
    df = get_processed_data()
    if df.empty:
        return dbc.Container(
            dbc.Alert("ไม่พบข้อมูล", color="warning", className="mt-5")
        )

    def render_card(fig):
        return dbc.Card(
            dbc.CardBody(
                dcc.Graph(
                    figure=fig,
                    config={"displayModeBar": False},
                    style={"height": "360px"},  # 🔴 Graph เท่ากัน
                )
            ),
            className="shadow-lg rounded-4 border-0 mb-4",
            style={"height": "420px"},      # 🔴 Card เท่ากัน
        )

    return dbc.Container(
        fluid=True,
        className="p-4 bg-light",
        children=[
            html.Div(
                [
                    html.H2("ข้อมูลสาขา", className="fw-bold text-dark"),
                    html.P(
                        "สรุปประสิทธิภาพและการเติบโตแยกตามรายสาขา",
                        className="text-muted",
                    ),
                ],
                className="mb-4",
            ),

            render_branch_kpis(df),

            dbc.Row(
                [
                    dbc.Col(render_card(chart_member_column(df)), lg=6),
                    dbc.Col(render_card(chart_income_line(df)), lg=6),
                ],
                className="g-4 align-items-stretch",
            ),

            dbc.Row(
                [
                    dbc.Col(render_card(chart_approval_mode(df)), lg=6),
                    dbc.Col(render_card(chart_member_income_dual(df)), lg=6),
                ],
                className="g-4 align-items-stretch",
            ),
        ],
    )


layout = create_branch_layout()
