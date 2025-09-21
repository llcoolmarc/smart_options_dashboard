from dash import html, dcc

console_component = html.Div(
    [
        html.Div(
            id="console-log",
            style={
                "whiteSpace": "pre-line",
                "fontFamily": "monospace",
                "fontSize": "12px",
                "color": "#eee",
            }
        ),
        dcc.Interval(id="console-interval", interval=2000, n_intervals=0)
    ],
    style={
        "backgroundColor": "#111",
        "padding": "5px",
        "height": "140px",
        "overflowY": "scroll",
    }
)
