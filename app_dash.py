import os
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

from utils import (
    journal,
    graduation,
    coaching_engine,
    scaling,
    filters,
    profits,
    discipline_ai,
    preferences,
    broker,
)

# Absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOURNAL_PATH = os.path.join(BASE_DIR, "trade_journal.json")
PREF_PATH = os.path.join(BASE_DIR, "preferences.json")

# ================================
# Enriched Session
# ================================
def get_enriched_session():
    session = {"mode": "SIM"}

    # Preferences
    prefs = preferences.load_preferences(PREF_PATH)
    session["preferences"] = prefs

    # Journal & graduation
    trades = journal.load_all_trades(JOURNAL_PATH)
    grad = graduation.check_graduation()
    session["graduation"] = grad

    # Default broker info
    session["broker"] = {"status": "❌ Not connected", "accounts": [], "positions": []}

    # Mode awareness
    if grad.get("graduated"):
        session["mode"] = "SANDBOX"
        broker_sess = broker.BrokerSession(paper=True)

        # ⚠️ Credentials should come from env or prefs.json in practice
        USERNAME = prefs.get("broker_username", "")
        PASSWORD = prefs.get("broker_password", "")

        if broker_sess.login(USERNAME, PASSWORD):
            accounts = broker_sess.get_accounts()
            positions = broker_sess.get_positions(accounts[0]["number"]) if accounts else []
            session["broker"] = {
                "status": broker.broker_status(broker_sess),
                "accounts": accounts,
                "positions": positions,
            }

            # Override account size for scaling
            if accounts and accounts[0].get("buying-power") is not None:
                bp = accounts[0]["buying-power"]
                session["account_size"] = bp
                da = session.setdefault("discipline_ai", {"messages": [], "score": 0})
                da["messages"].append(
                    f"⚖️ Scaling enforced against live broker buying power = ${bp:,.2f}"
                )
        else:
            session["broker"]["status"] = "❌ Broker login failed"
    else:
        session["mode"] = "SIM"
        session["broker"]["status"] = "🔒 Graduation lock — broker disabled"

    # Expectancy
    try:
        exp = profits.calculate_expectancy(trades)
        session["expectancy"] = exp
    except Exception:
        session["expectancy"] = {"expectancy": 0, "win_rate": 0}

    # Discipline AI
    try:
        da = discipline_ai.evaluate(trades, prefs)
        session["discipline_ai"] = da
    except Exception:
        session["discipline_ai"] = {"messages": ["⚠️ Discipline AI unavailable"], "score": 0}

    return session


# ================================
# Builders
# ================================
def build_expectancy(session):
    exp = session.get("expectancy", {})
    if isinstance(exp, dict):
        val = exp.get("expectancy", 0)
        win_rate = exp.get("win_rate", 0)
    else:
        val, win_rate = exp, 0
    return html.Div([
        html.P(f"📈 Expectancy: {val:.2f}"),
        html.P(f"Win Rate: {win_rate:.1f}%")
    ])


def build_discipline(session):
    violations = session.get("discipline", {}).get("violations", [])
    if not violations:
        return html.Div("✅ No discipline violations")
    return html.Ul([html.Li(v) for v in violations])


def build_discipline_ai(session):
    da = session.get("discipline_ai", {})
    score = da.get("score", 0)
    messages = da.get("messages", [])
    items = [html.Li(msg) for msg in messages]
    return html.Div([
        html.P(f"Discipline AI Score: {score}/100", className="fw-bold"),
        html.Ul(items)
    ])


def build_broker(session):
    broker_info = session.get("broker", {})
    status = broker_info.get("status", "❌ Broker unavailable")
    accounts = broker_info.get("accounts", [])
    positions = broker_info.get("positions", [])

    elements = [html.P(f"Status: {status}", className="fw-bold")]

    if accounts:
        elements.append(html.H6("Accounts:", className="mt-2"))
        acc_list = []
        for acct in accounts:
            line = f"{acct['number']}"
            if acct.get("cash-balance") is not None:
                line += f" | Cash: ${acct['cash-balance']:.2f}"
            if acct.get("buying-power") is not None:
                line += f" | BP: ${acct['buying-power']:.2f}"
            acc_list.append(html.Li(line))
        elements.append(html.Ul(acc_list))

    if positions:
        elements.append(html.H6("Positions:", className="mt-2"))
        pos_list = []
        for pos in positions:
            symbol = pos.get("symbol") or pos.get("instrument-type", "Unknown")
            qty = pos.get("quantity", "?")
            cost = pos.get("cost-basis", "?")
            pos_list.append(html.Li(f"{symbol} | Qty: {qty} | Cost: {cost}"))
        elements.append(html.Ul(pos_list))

    return html.Div(elements)


# Coaching, Scaling, Filters, Profits, Trade Instructions, Best Strategy, Events, Alerts
# (same builders we added earlier, unchanged except scaling uses account_size override)

def build_coaching(session):
    market = session.get("marketdata", {})
    portfolio_data = session.get("portfolio", {})
    prefs = session.get("preferences", {})
    try:
        coaching_msgs = coaching_engine.live_coaching(market, portfolio_data, prefs)
    except Exception:
        coaching_msgs = []
    if not coaching_msgs:
        return html.Div("No coaching guidance available yet.")
    return html.Ul([html.Li(m) for m in coaching_msgs])


def build_scaling(session):
    portfolio_data = session.get("portfolio", {})
    prefs = session.get("preferences", {})
    account_size = prefs.get("account_size", 10000)
    if session.get("account_size"):
        account_size = session["account_size"]
    try:
        result = scaling.check_scaling(portfolio_data, account_size)
    except Exception:
        result = {"messages": ["⚠️ Scaling check unavailable."], "compliant": True}
    return html.Div([html.Ul([html.Li(m) for m in result.get("messages", [])])])


def build_filters(session):
    try:
        result = filters.check_filters({}, [], None)
    except Exception:
        result = {"messages": ["⚠️ Filters unavailable"], "compliant": True}
    da = session.setdefault("discipline_ai", {"messages": [], "score": 0})
    if not result.get("compliant"):
        da["messages"].append("🚫 Trade blocked due to market filter (earnings/VIX).")
    return html.Div([html.Ul([html.Li(m) for m in result.get("messages", [])])])


def build_profits(session):
    prefs = session.get("preferences", {})
    try:
        entries = journal.load_journal(JOURNAL_PATH)
        result = profits.calculate_profits(entries, prefs)
    except Exception:
        result = {"messages": ["⚠️ Profit calc unavailable"], "realized": 0}
    return html.Div([
        html.P(f"Realized profit this month: ${result.get('realized', 0):.2f}"),
        html.Ul([html.Li(m) for m in result.get("messages", [])])
    ])


def build_trade_instructions(session):
    instructions = session.get("instructions", [])
    violations = session.get("discipline", {}).get("violations", [])
    extra = []
    if "Scaling violation" in " ".join(violations):
        extra.append("Reject trades above allowed contract ladder.")
    return html.Div([
        html.P("Trade Instructions:", className="fw-bold"),
        html.Ul([html.Li(instr) for instr in instructions + extra])
    ])


def build_best_strategy(session):
    instructions = session.get("instructions", [])
    spreads = [i for i in instructions if "spread" in i.lower()]
    if not spreads:
        return html.Div("⚠️ No validated spread strategy.")
    return html.Ul([html.Li(s) for s in spreads])


def build_events(session):
    return html.Div("No events scheduled.")


def build_alerts(session):
    violations = session.get("discipline", {}).get("violations", [])
    if not violations:
        return html.Div("✅ No alerts.")
    return html.Ul([html.Li(v) for v in violations])


# ================================
# Layout
# ================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


def serve_layout():
    session = get_enriched_session()
    return dbc.Container([
        html.H2("📊 Defined-Risk Options Cockpit", className="mt-4"),

        dbc.Button("⬇️ Export Compliance CSV", color="secondary", className="mb-4"),

        # Broker Card at top
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("📡 Broker Connection"),
                dbc.CardBody(build_broker(session))
            ], className="shadow-sm border-primary"), width=12)
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("🎓 Graduation Status"),
                dbc.CardBody(html.Div(session["graduation"]["message"]))
            ]), width=12)
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("📈 Expectancy"),
                dbc.CardBody(build_expectancy(session))
            ]), width=12)
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("🧑‍🏫 Coaching"),
                dbc.CardBody(build_coaching(session))
            ]), width=12)
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("📏 Scaling"),
                dbc.CardBody(build_scaling(session))
            ]), width=12)
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("🚦 Filters"),
                dbc.CardBody(build_filters(session))
            ]), width=12)
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("💰 Profits"),
                dbc.CardBody(build_profits(session))
            ]), width=12)
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("⚖️ Discipline"),
                dbc.CardBody(build_discipline(session))
            ]), width=12)
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("🤖 Discipline AI"),
                dbc.CardBody(build_discipline_ai(session))
            ]), width=12)
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("📋 Trade Instructions"),
                dbc.CardBody(build_trade_instructions(session))
            ]), width=12)
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("🏆 Best Strategy"),
                dbc.CardBody(build_best_strategy(session))
            ]), width=12)
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("📅 Events"),
                dbc.CardBody(build_events(session))
            ]), width=12)
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("🚨 Alerts"),
                dbc.CardBody(build_alerts(session))
            ]), width=12)
        ], className="mb-4"),
    ], fluid=True)


app.layout = serve_layout

if __name__ == "__main__":
    app.run_server(debug=True)
