"""
utils/profits.py

Phase 17: Profit Distribution & Tracking
- Tracks realized profits
- Suggests withdrawals vs reinvestment
- Provides expectancy calculation
"""

import datetime

__all__ = ["calculate_profits", "evaluate_distribution", "calculate_expectancy"]


def _flatten_trades(trades):
    """
    Helper: flatten nested lists of trades into a flat list of dicts.
    """
    flat = []
    for t in trades:
        if isinstance(t, list):
            flat.extend(_flatten_trades(t))  # recursive flatten
        elif isinstance(t, dict):
            flat.append(t)
    return flat


def calculate_profits(journal: list, prefs: dict = None) -> dict:
    """
    Analyze trade journal for realized profits.
    Args:
        journal: list of trade dicts (possibly nested lists)
        prefs: dict with user preferences (withdrawal_pct, profit_goal)
    Returns:
        dict with 'realized', 'withdraw', 'reinvest', 'messages'
    """
    prefs = prefs or {}
    withdrawal_pct = prefs.get("withdrawal_pct", 0.25)
    profit_goal = prefs.get("profit_goal", 1000)

    # Always flatten trades first
    trades = _flatten_trades(journal)

    today = datetime.date.today()
    month_start = today.replace(day=1)

    realized = 0
    for trade in trades:
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
            f"Monthly realized profit = ${realized:.2f}. "
            f"Suggest withdrawing ${withdraw:.2f} ({withdrawal_pct:.0%}) "
            f"and reinvesting ${reinvest:.2f}."
        )
    elif realized > 0:
        reinvest = realized
        messages.append(
            f"Monthly realized profit = ${realized:.2f}. "
            "Below goal, no withdrawals yet. Reinvest all."
        )
    else:
        messages.append("No profits to withdraw. Stay disciplined until expectancy turns positive.")

    return {
        "realized": realized,
        "withdraw": withdraw,
        "reinvest": reinvest,
        "messages": messages,
    }


def evaluate_distribution(session: dict) -> dict:
    """
    Wrapper to evaluate profit distribution from a session object.
    Ensures trades are flattened before calculation.
    """
    journal = session.get("trades", [])
    prefs = session.get("preferences", {})

    flat_trades = _flatten_trades(journal)
    return calculate_profits(flat_trades, prefs)


def calculate_expectancy(trades: list) -> dict:
    """
    Calculate expectancy from a list of trades.
    Expectancy = (avg win × win rate) − (avg loss × loss rate).
    """
    trades = _flatten_trades(trades)

    if not trades:
        return {"expectancy": 0, "win_rate": 0, "avg_win": 0, "avg_loss": 0}

    wins = [t.get("pnl", 0) for t in trades if t.get("pnl", 0) > 0]
    losses = [t.get("pnl", 0) for t in trades if t.get("pnl", 0) <= 0]

    win_rate = len(wins) / len(trades) if trades else 0
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = abs(sum(losses) / len(losses)) if losses else 0

    expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

    return {
        "expectancy": expectancy,
        "win_rate": win_rate * 100,  # percentage
        "avg_win": avg_win,
        "avg_loss": avg_loss,
    }
