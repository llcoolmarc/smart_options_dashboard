from dash import html
import dash_bootstrap_components as dbc

def build_trade_table(state):
    open_trades = state.get("open_trades", [])
    closed_trades = state.get("closed_trades", [])

    return html.Div([
        html.H5("Open Trades"),
        dbc.Table(
            [html.Thead(html.Tr([html.Th("Ticker"), html.Th("Strategy"), html.Th("Qty"), html.Th("Price")]))] +
            [html.Tr([html.Td(t.get("ticker", "-")), html.Td(t.get("strategy", "-")), html.Td(t.get("qty", "-")), html.Td(t.get("price", "-"))]) for t in open_trades],
            bordered=True, striped=True, hover=True
        ) if open_trades else html.P("No open trades."),

        html.H5("Closed Trades", className="mt-4"),
        dbc.Table(
            [html.Thead(html.Tr([html.Th("Ticker"), html.Th("Strategy"), html.Th("Qty"), html.Th("Exit Price")]))] +
            [html.Tr([html.Td(t.get("ticker", "-")), html.Td(t.get("strategy", "-")), html.Td(t.get("qty", "-")), html.Td(t.get("exit_price", "-"))]) for t in closed_trades],
            bordered=True, striped=True, hover=True
        ) if closed_trades else html.P("No closed trades.")
    ])
