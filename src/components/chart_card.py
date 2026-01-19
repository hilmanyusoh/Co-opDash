from dash import dcc, html
import dash_bootstrap_components as dbc

def chart_card(fig, title=None, height=None):
    graph = (
        fig if isinstance(fig, dcc.Graph)
        else dcc.Graph(
            figure=fig,
            config={"displayModeBar": False, "responsive": True},
            style={"height": f"{height}px"} if height else {},
        )
    )

    return dbc.Card(
        dbc.CardBody(
            [
                html.H6(title, className="fw-bold mb-3") if title else None,
                graph,
            ],
            style={"padding": "18px"},
        ),
        className="shadow-sm rounded-3 border-0 mb-3",
    )
