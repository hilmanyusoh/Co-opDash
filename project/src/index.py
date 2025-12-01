# src/index.py

from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

# Imports จากภายใน src/ 
from .app import app
from .components.sidebar import render_sidebar 

# Imports Layout และ Register Functions จากแต่ละ Page
from .pages import home, analysis, review 

# Layout Styles 
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "18rem", 
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa", 
    "box-shadow": "2px 0 5px rgba(0, 0, 0, 0.1)",
}

CONTENT_STYLE = {
    "margin-left": "18rem", 
    "padding": "2rem 2rem",
}

# การจัด Layout หลักของแอปพลิเคชัน 
app.layout = html.Div([
    dcc.Location(id="url", refresh=False), 
    render_sidebar(), 
    html.Div(id="page-content", style=CONTENT_STYLE), 
])

# Callback หลัก: การจัดการ Routing 
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    
    if pathname == "/" or pathname == "/home":
        return home.layout
    
    elif pathname == "/analysis":
        return analysis.layout
            
    elif pathname == "/review":
        return review.layout 
            
    # กรณีไม่พบหน้า (404)
    return dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"เส้นทาง {pathname} ไม่ถูกต้อง"),
        ], 
        className="p-3" 
    )

# ลงทะเบียน Callbacks ของแต่ละ Page 
home.register_callbacks(app)
analysis.register_callbacks(app)
review.register_callbacks(app)

# รันแอปพลิเคชัน 
if __name__ == '__main__':
    # รันจาก index.py 
    app.run(debug=True)