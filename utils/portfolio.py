"""
utils/portfolio.py

Portfolio utilities
- Fetches positions from broker or SIM fallback
- Calculates allocations & exposure
"""

import os
from utils import broker


def load_portfolio(session: broker.BrokerSession = None) -> dict:
    """
    Load portfolio positions.
    If a broker session is provided, attempt to fetch positions.
    Falls back to SIM (empty) if unavailable.
    """
    return broker.safe_fetch_portfolio(session)


def summarize_allocations(portfolio: dict) -> dict:
    """
    Summarize portfolio allocations by symbol and total risk.
    Args:
        portfolio: dict with "positions" key
    Returns dict with summary
    """
    positions = portfolio.get("positions", [])
    summary = {"total_risk": 0, "by_symbol": {}}

    for pos in positions:
        sym = pos.get("symbol", "UNKNOWN")
        risk = pos.get("risk", 0)

        summary["total_risk"] += risk
        summary["by_symbol"][sym] = summary["by_symbol"].get(sym, 0) + risk

    return summary


def check_symbol_limits(summary: dict, prefs: dict) -> list:
    """
    Check symbol-specific allocation limits.
    Example prefs:
    {
        "max_spy": 0.5,  # 50% max in SPY
        "max_qqq": 0.3,  # 30% max in QQQ
        "account_size": 10000
    }
    Returns list of violation messages.
    """
    violations = []
    total_risk = summary.get("total_risk", 0)
    account_size = prefs.get("account_size", 10000)

    for sym, risk in summary.get("by_symbol", {}).items():
        pct = risk / account_size if account_size else 0
        if sym == "SPY" and pct > prefs.get("max_spy", 0.5):
            violations.append(f"⚠️ Too much risk in SPY ({pct:.0%}) > 50% allowed")
        if sym == "QQQ" and pct > prefs.get("max_qqq", 0.3):
            violations.append(f"⚠️ Too much risk in QQQ ({pct:.0%}) > 30% allowed")

    if total_risk > account_size * 0.05:  # 5% max portfolio risk
        violations.append(f"⚠️ Portfolio risk {total_risk:.2f} exceeds 5% of account")

    return violations


# Convenience wrapper for cockpit
def get_portfolio_summary(session: broker.BrokerSession = None, prefs: dict = None) -> dict:
    """
    Full portfolio summary with allocations and violations.
    """
    prefs = prefs or {}
    portfolio = load_portfolio(session)
    summary = summarize_allocations(portfolio)
    violations = check_symbol_limits(summary, prefs)
    return {"portfolio": portfolio, "summary": summary, "violations": violations}
