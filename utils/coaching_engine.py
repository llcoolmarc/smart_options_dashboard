"""
Coaching Engine — provides plain-English guidance on entries, exits, adjustments,
and discipline reinforcement for defined-risk options spreads.
"""

def live_coaching(marketdata: dict, portfolio: dict, preferences: dict) -> list:
    """
    Core coaching logic. Returns a list of plain-English guidance messages
    based on market conditions, portfolio state, and preferences.
    """
    messages = []

    # Entries — simple placeholder rules
    if marketdata.get("volatility_index", 0) > 25:
        messages.append("⚠️ Elevated volatility — size down or wait for stabilization.")
    else:
        messages.append("✅ Volatility within range — entries permitted.")

    # Exits — profit taking
    if portfolio.get("unrealized_pnl", 0) > preferences.get("take_profit", 100):
        messages.append("💰 Consider taking profits on winning positions.")

    # Exits — stop loss
    if portfolio.get("unrealized_pnl", 0) < -preferences.get("stop_loss", 100):
        messages.append("❌ Stop-loss triggered — exit losing position.")

    # Adjustments
    if portfolio.get("theta", 0) < 0:
        messages.append("⏳ Negative theta — consider rolling into positive carry spreads.")

    # Concentration
    if len(portfolio.get("positions", [])) > preferences.get("max_positions", 5):
        messages.append("⚠️ Too many open positions — reduce risk concentration.")

    return messages


# ================================
# Aliases for app_dash.py
# ================================
def generate(session: dict) -> dict:
    """
    Alias for main coaching logic — wraps live_coaching().
    Returns { "messages": [...] }
    """
    messages = live_coaching(
        marketdata=session.get("marketdata", {}),
        portfolio=session.get("portfolio", {}),
        preferences=session.get("preferences", {}),
    )
    return {"messages": messages}


def trade_instructions(session: dict) -> dict:
    """
    Alias for trade instruction guidance.
    Currently reuses generate() until specialized logic is added.
    """
    return generate(session)


def best_strategy(session: dict) -> dict:
    """
    Alias for best-strategy recommendation.
    Currently reuses generate() until specialized logic is added.
    """
    return generate(session)
