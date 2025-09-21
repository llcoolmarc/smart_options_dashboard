import pytest
from utils import profits

def test_profit_split_positive():
    journal = [
        {"closed": True, "pnl": 1200, "closed_date": "2025-09-01"}
    ]
    result = profits.calculate_profits(journal)
    assert result["withdraw"] > 0 and result["reinvest"] > 0

def test_profit_split_zero():
    journal = []
    result = profits.calculate_profits(journal)
    assert result["withdraw"] == 0 and result["reinvest"] == 0
