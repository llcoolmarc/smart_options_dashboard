# -*- coding: utf-8 -*-
import os
from utils import journal


def main():
    print("=== Journal Smoke Tests ===")

    test_file = "tests/trade_journal_test.json"

    # Always reset test file to an empty list
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("[]")

    # ---- Empty Journal ----
    trades = journal.load_all_trades(test_file)
    if isinstance(trades, list) and len(trades) == 0:
        print("[PASS] Empty journal handled")
    else:
        print("[FAIL] Empty journal handled")

    # ---- Flat trades ----
    flat = [{"symbol": "AAPL", "pnl": 50}]
    journal.save_trades(test_file, flat)
    trades = journal.load_all_trades(test_file)
    if len(trades) == 1 and trades[0]["symbol"] == "AAPL":
        print("[PASS] Flat trades parsed")
    else:
        print("[FAIL] Flat trades parsed")

    # ---- Nested trades ----
    nested = [{"trades": [{"symbol": "MSFT", "pnl": -20}, {"symbol": "TSLA", "pnl": 100}]}]
    journal.save_trades(test_file, nested)
    trades = journal.load_all_trades(test_file)
    if len(trades) == 2 and any(t["symbol"] == "TSLA" for t in trades):
        print("[PASS] Nested trades parsed")
    else:
        print("[FAIL] Nested trades parsed")

    # ---- Enrichment ----
    root_file = "trade_journal.json"
    if not os.path.exists(root_file):
        with open(root_file, "w", encoding="utf-8") as f:
            f.write("[]")

    trades = journal.load_all_trades(root_file)
    enriched = journal.enrich_session(trades)
    if enriched.get("mode") in ("SANDBOX", "LIVE", "SIM"):
        print("[PASS] Mode valid")
    else:
        print("[FAIL] Mode valid")

    if "expectancy" in enriched:
        print("[PASS] Expectancy present")
    else:
        print("[FAIL] Expectancy present")

    if "discipline_ai" in enriched and "score" in enriched["discipline_ai"]:
        print("[PASS] Discipline AI score present")
    else:
        print("[FAIL] Discipline AI score present")

    if "broker" in enriched:
        print("[PASS] Broker info included in session")
    else:
        print("[FAIL] Broker info included in session")


if __name__ == "__main__":
    main()
