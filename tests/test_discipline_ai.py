import pytest
from utils import discipline_ai
import datetime

today = datetime.date.today().strftime("%Y-%m-%d")

def test_overtrading_flagged():
    journal = [
        {"date": today, "pnl": 50},
        {"date": today, "pnl": -20},
        {"date": today, "pnl": 10},
    ]
    result = discipline_ai.analyze_habits(journal)
    assert any("overtrading" in m for m in result["messages"][0].lower())

def test_revenge_trading_flagged():
    journal = [
        {"date": today, "pnl": -100},
        {"date": today, "pnl": -50},
    ]
    result = discipline_ai.analyze_habits(journal)
    assert any("revenge" in m.lower() for m in result["messages"])
