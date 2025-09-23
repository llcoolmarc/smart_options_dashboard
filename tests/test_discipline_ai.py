import sys, os, datetime
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils import discipline_ai

today = datetime.date.today().strftime("%Y-%m-%d")

def test_overtrading_flagged():
    journal = [
        {"date": today, "pnl": 50},
        {"date": today, "pnl": -20},
        {"date": today, "pnl": 10},
    ]
    result = discipline_ai.analyze_habits(journal)
    assert any("overtrading" in m.lower() for m in result["messages"])

def test_revenge_trading_flagged():
    journal = [
        {"date": today, "pnl": -100},
        {"date": today, "pnl": -50},
    ]
    result = discipline_ai.analyze_habits(journal)
    assert any("revenge" in m.lower() for m in result["messages"])

if __name__ == "__main__":
    try:
        test_overtrading_flagged()
        print("[PASS] Overtrading flagged")
    except AssertionError:
        print("[FAIL] Overtrading not flagged")

    try:
        test_revenge_trading_flagged()
        print("[PASS] Revenge trading flagged")
    except AssertionError:
        print("[FAIL] Revenge trading not flagged")
