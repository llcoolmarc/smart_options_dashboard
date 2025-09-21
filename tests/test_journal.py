# -*- coding: utf-8 -*-
import sys, os, io, json
# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
# Ensure repo root in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import journal
from app_dash import get_enriched_session

TEST_PATH = os.path.join(os.path.dirname(__file__), "trade_journal_test.json")
TEST_RESULTS = {"pass": 0, "fail": 0}

def reset_test_file(entries):
    with open(TEST_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)

def record_result(cond, desc):
    if cond: print(f"[✅ PASS] {desc}"); TEST_RESULTS["pass"] += 1
    else: print(f"[❌ FAIL] {desc}"); TEST_RESULTS["fail"] += 1

def print_summary(name, results):
    print(f"\n=== {name} Summary ===")
    print(f"✅ Passed: {results['pass']}")
    print(f"❌ Failed: {results['fail']}")
    if results["fail"] == 0:
        print("🎉 All tests passed successfully!")
    else:
        print("⚠️ Some tests failed — review output above.")

def main():
    # Keep your detailed journal parsing checks
    reset_test_file([])
    record_result(isinstance(journal.load_all_trades(TEST_PATH), list), "Empty journal handled")

    flat_trades = [
        {"symbol": "SPY", "pnl": 50, "type": "vertical"},
        {"symbol": "QQQ", "pnl": -20, "type": "iron_condor"},
    ]
    reset_test_file(flat_trades)
    record_result(len(journal.load_all_trades(TEST_PATH)) == 2, "Flat trades parsed")

    nested_sessions = [
        {"timestamp": "2025-09-20T09:30:00", "mode": "SIM", "clean": True,
         "trades": [{"symbol": "SPY", "pnl": 100}, {"symbol": "QQQ", "pnl": -50}]}
    ]
    reset_test_file(nested_sessions)
    record_result(len(journal.load_all_trades(TEST_PATH)) == 2, "Nested trades parsed")

    # Enriched session validation
    session = get_enriched_session()
    record_result(session.get("mode") in ["SIM","SANDBOX","LIVE"], "Mode valid")
    record_result("expectancy" in session, "Expectancy present")

    dai = session.get("discipline_ai", {})
    record_result("score" in dai, "Discipline AI score present")
    if "messages" in dai and dai["messages"]:
        print("[INFO] Discipline AI messages:")
        for m in dai["messages"]: print("  -", m)

    record_result("broker" in session, "Broker info included in session")

    print_summary("Journal Test Harness", TEST_RESULTS)

if __name__ == "__main__":
    main()
