"""
utils/filters.py

Phase 16: Advanced Market Filters
- Earnings calendar checks
- Fed / macro event filters
- Volatility regime checks
"""

from datetime import datetime, timedelta

def check_filters(market: dict, events: list = None, vix: float = None) -> dict:
    """
    Evaluate advanced filters.
    Args:
        market: dict containing tickers and earnings dates
        events: list of scheduled macro events (strings)
        vix: current volatility index level
    Returns dict with 'compliant' and 'messages'
    """
    messages = []
    compliant = True

    today = datetime.today().date()

    # Earnings filter
    for sym, data in market.get("symbols", {}).items():
        earnings_date = data.get("earnings_date")
        if earnings_date:
            try:
                e_date = datetime.strptime(earnings_date, "%Y-%m-%d").date()
                if abs((e_date - today).days) <= 3:
                    compliant = False
                    messages.append(
                        f"🚫 {sym} has earnings {earnings_date} — no trades allowed ±3 days."
                    )
            except Exception:
                pass

    # Macro event filter
    if events:
        for e in events:
            if "Fed" in e or "CPI" in e or "Jobs" in e:
                compliant = False
                messages.append(f"⚠️ Macro Event: {e} — avoid new trades.")

    # Volatility regime filter
    if vix is not None:
        if vix > 30:
            compliant = False
            messages.append(f"🚫 VIX is {vix:.1f} (>30). Too risky, no trades allowed.")
        elif vix >= 20:
            messages.append(f"⚠️ VIX is {vix:.1f} (20–30). Elevated risk, reduce size.")
        else:
            messages.append(f"✅ VIX is {vix:.1f}, normal trading environment.")

    if compliant:
        messages.append("✅ All advanced filters passed.")

    return {"compliant": compliant, "messages": messages}
def check_market_conditions(session: dict) -> dict:
    market = session.get("marketdata", {})
    events = session.get("events", [])
    vix = session.get("vix", None)
    return check_filters(market, events=events, vix=vix)

def check_events(session: dict) -> dict:
    """Alias: Extract event-specific messages."""
    result = check_market_conditions(session)
    return {"messages": [m for m in result["messages"] if "Event" in m or "earnings" in m]}
