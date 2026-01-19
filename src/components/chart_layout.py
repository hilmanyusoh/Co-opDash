CHART_HEIGHT = 340

def apply_layout(fig, title=None, height=CHART_HEIGHT, show_legend=True):
    fig.update_layout(
        title={
            "text": f"<b>{title}</b>" if title else "",
            "x": 0.02,
            "xanchor": "left",
        },
        height=height,
        margin=dict(t=50, b=40, l=60, r=30),
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0.02)",
        font=dict(
            family="Sarabun, sans-serif",
            color="#334155",
        ),
        showlegend=show_legend,
        hoverlabel=dict(
            bgcolor="rgba(15,23,42,0.95)",
            font_color="white",
        ),
    )
    return fig
