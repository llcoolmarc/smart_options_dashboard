from dash import html
import dash_bootstrap_components as dbc

def build_signals_table(open_trades):
    if not open_trades:
        return html.P("No open trades available for signals.")

    signals = []
    for trade in open_trades:
        ticker = trade.get("ticker", "?")
        qty = trade.get("qty", 0)
        strategy = trade.get("strategy", "")

        if "earnings" in strategy.lower():
            signals.append(f"⚠️ {ticker} near earnings. Consider risk.")
        if qty > 5:
            signals.append(f"⚠️ {ticker} position size large. Check concentration.")

    return html.Div([
        html.H5("Signals & Guardrails"),
        html.Ul([html.Li(s) for s in signals]) if signals else html.P("No major risks detected.")
    ])
