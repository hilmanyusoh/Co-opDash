from dash import dcc, html
import dash_bootstrap_components as dbc

def chart_card(fig, title=None, height=None):
    graph = (
        fig if isinstance(fig, dcc.Graph)
        else dcc.Graph(
            figure=fig,
            config={
                "displayModeBar": False, 
                "responsive": True,
                # เพิ่มพารามิเตอร์เพื่อให้ Plotly วาดใหม่เมื่อขนาดจอเปลี่ยน
                "autosizable": True 
            },
            # กำหนดความสูงที่แน่นอนให้ dcc.Graph เพื่อไม่ให้คำนวณผิดพลาด
            style={"height": f"{height}px"} if height else {"height": "100%"},
        )
    )

    return dbc.Card(
        dbc.CardBody(
            [
                html.H6(
                    title, 
                    className="fw-bold mb-3",
                    style={"color": "#1e293b", "fontSize": "15px"} # ล็อกสีและขนาดหัวข้อ
                ) if title else None,
                # ห่อหุ้ม Graph ด้วย Div ที่คุม Overflow
                html.Div(graph, style={"overflow": "hidden"}) 
            ],
            style={"padding": "18px"},
        ),
        className="shadow-sm rounded-3 border-0 mb-3",
        style={
            "height": "100%", 
            "overflow": "hidden", # กั้นไม่ให้สิ่งที่อยู่ข้างในล้นออกมานอกการ์ด
            "backgroundColor": "white"
        },
    )