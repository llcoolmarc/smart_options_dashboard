from dash import html
import dash_bootstrap_components as dbc

def build_analytics_layout(state):
    closed_trades = state.get("closed_trades", [])
    open_trades = state.get("open_trades", [])

    if not closed_trades and not open_trades:
        return html.Div([
            html.H5("Profitability Deep Dive"),
            html.P("No trade data available."),
            html.H5("Portfolio What-If Simulator"),
            html.P("Not enough data for simulation.")
        ])

    realized = [t.get("exit_price", 0) - t.get("price", 0) for t in closed_trades if "price" in t and "exit_price" in t]
    total_realized = sum(realized) if realized else 0
    total_unrealized = 0
    net_total = total_realized + total_unrealized

    summary = dbc.Card(dbc.CardBody([
        html.H5("Profitability Deep Dive"),
        html.P(f"Closed PnL: {total_realized}"),
        html.P(f"Open PnL: {total_unrealized}"),
        html.P(f"Net Total: {net_total}")
    ]))

    whatif_notes = []
    if closed_trades:
        whatif_notes.append("If losers were cut earlier, PnL would improve.")
        whatif_notes.append("If winners were taken earlier, PnL would be smoother.")
        whatif_notes.append("Applying both rules would shift net PnL.")

    whatif_section = html.Div([
        html.H5("Portfolio What-If Simulator"),
        html.Ul([html.Li(n) for n in whatif_notes]) if whatif_notes else html.P("Not enough data for simulation.")
    ])

    return html.Div([summary, whatif_section], style={"padding": "20px"})
