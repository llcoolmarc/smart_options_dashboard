import time
from utils.analytics import AnalyticsEngine
from utils import portfolio, marketdata, journal
from components import dashboard


def launch(prefs: dict, broker: object):
    """
    Launch Smart Options Dashboard with auto-refresh capability.
    Refreshes evaluation every N seconds using AnalyticsEngine.
    """
    refresh_rate = prefs.get("refresh_rate", 30)  # seconds

    engine = AnalyticsEngine(prefs, broker=broker)

    while True:
        # Reload portfolio + journal + marketdata each cycle
        port = portfolio.load_portfolio()
        trades = journal.load_trades("trade_journal.json")
        mdata = marketdata.fetch_market_snapshot(port)

        # Run analytics
        evaluation = engine.evaluate_portfolio(port, trades, mdata)

        # Attach context for dashboard rendering
        evaluation["portfolio"] = port
        evaluation["marketdata"] = mdata
        evaluation["preferences"] = prefs

        # Render dashboard
        dashboard.render_dashboard(evaluation)

        # Wait for next cycle
        time.sleep(refresh_rate)
