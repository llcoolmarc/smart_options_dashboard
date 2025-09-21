"""
utils/earnings.py (L53.x)

Provides upcoming earnings events.
- In SIM mode: returns static dummy earnings schedule.
- In LIVE mode: could be extended to call an API.
"""

from datetime import datetime, timedelta


def get_upcoming_earnings(days_ahead=7):
    """
    Return upcoming earnings within X days.
    For now: dummy SIM data.
    
    Returns:
        list of dicts:
        [
          {"symbol": "AAPL", "date": "YYYY-MM-DD"},
          {"symbol": "MSFT", "date": "YYYY-MM-DD"}
        ]
    """
    today = datetime.today()
    cutoff = today + timedelta(days=days_ahead)

    # Dummy SIM earnings calendar
    dummy_earnings = [
        {"symbol": "AAPL", "date": (today + timedelta(days=2)).strftime("%Y-%m-%d")},
        {"symbol": "MSFT", "date": (today + timedelta(days=5)).strftime("%Y-%m-%d")},
        {"symbol": "GOOG", "date": (today + timedelta(days=9)).strftime("%Y-%m-%d")},  # will be filtered out if > days_ahead
    ]

    upcoming = [
        e for e in dummy_earnings
        if datetime.strptime(e["date"], "%Y-%m-%d") <= cutoff
    ]

    return upcoming
