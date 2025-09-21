"""
utils/profits.py

Phase 17: Profit Distribution & Tracking
- Tracks realized profits
- Suggests withdrawals vs reinvestment
"""

import datetime

def calculate_profits(journal: list, prefs: dict = None) -> dict:
    """
    Analyze trade journal for realized profits.
    Args:
        journal: list of trade dicts
        prefs: dict with user preferences (withdrawal_pct, profit_goal)
    Returns dict with 'realized', 'withdraw', 'reinvest', 'messages'
    """
    prefs = prefs or {}
    withdrawal_pct = prefs.get("withdrawal_pct", 0.25)
    profit_goal = prefs.get("profit_goal", 1000)

    today = datetime.date.today()
    month_start = today.replace(day=1)

    realized = 0
    for trade in journal:
        closed = trade.get("closed", False)
        pnl = trade.get("pnl", 0)
        closed_date = trade.get("closed_date")
        if closed and closed_date:
            try:
                c_date = datetime.datetime.strptime(closed_date, "%Y-%m-%d").date()
                if c_date >= month_start:
                    realized += pnl
            except Exception:
                continue

    withdraw = 0
    reinvest = 0
    messages = []

    if realized >= profit_goal:
        withdraw = realized * withdrawal_pct
        reinvest = realized - withdraw
        messages.append(
            f"💰 Monthly realized profit = ${realized:.2f}. "
            f"Suggest withdrawing ${withdraw:.2f} (25%) and reinvesting ${reinvest:.2f}."
        )
    elif realized > 0:
        reinvest = realized
        messages.append(
            f"📈 Monthly realized profit = ${realized:.2f}. Below goal, no withdrawals yet. Reinvest all."
        )
    else:
        messages.append("⚠️ No profits to withdraw. Stay disciplined until expectancy turns positive.")

    return {
        "realized": realized,
        "withdraw": withdraw,
        "reinvest": reinvest,
        "messages": messages
    }
def evaluate_distribution(session: dict) -> dict:
    journal = session.get("trades", [])
    prefs = session.get("preferences", {})
    return calculate_profits(journal, prefs)
