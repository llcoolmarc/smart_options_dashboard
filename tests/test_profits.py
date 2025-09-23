import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils import profits

def test_profit_split_positive():
    journal = [{"closed": True, "pnl": 1200, "closed_date": "2025-09-01"}]
    result = profits.calculate_profits(journal)
    assert result["withdraw"] > 0 and result["reinvest"] > 0

def test_profit_split_zero():
    journal = []
    result = profits.calculate_profits(journal)
    assert result["withdraw"] == 0 and result["reinvest"] == 0

if __name__ == "__main__":
    try:
        test_profit_split_positive()
        print("[PASS] Profit split handled positive case")
    except AssertionError:
        print("[FAIL] Profit split failed positive case")

    try:
        test_profit_split_zero()
        print("[PASS] Profit split handled zero case")
    except AssertionError:
        print("[FAIL] Profit split failed zero case")
