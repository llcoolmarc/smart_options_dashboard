# -*- coding: utf-8 -*-
import sys, os, io
# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
# Ensure repo root is in path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.broker import BrokerSession, safe_fetch_portfolio, safe_fetch_marketdata, broker_status
from app_dash import get_enriched_session

TEST_RESULTS = {"pass": 0, "fail": 0}

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
    USERNAME = os.getenv("TASTY_USERNAME", "your_username")
    PASSWORD = os.getenv("TASTY_PASSWORD", "your_password")

    broker_sess = BrokerSession(paper=True)
    record_result(broker_sess.login(USERNAME, PASSWORD), "Broker login to SANDBOX")

    accounts = broker_sess.get_accounts()
    record_result(isinstance(accounts, list), "Fetched accounts list")
    if accounts:
        acc = accounts[0]
        record_result("cash-balance" in acc, "Account includes cash balance")
        record_result("buying-power" in acc, "Account includes buying power")
        record_result(isinstance(broker_sess.get_positions(acc['number']), list), "Fetched positions list")

    record_result("Connected" in broker_status(broker_sess) or "Not connected" in broker_status(broker_sess),
                  "Broker status string valid")

    record_result("accounts" in safe_fetch_portfolio(broker_sess), "safe_fetch_portfolio returns accounts")
    record_result(isinstance(safe_fetch_marketdata(broker_sess, "SPY"), dict), "safe_fetch_marketdata returns dict")

    broker_sess.disconnect()

    session = get_enriched_session()
    record_result("broker" in session, "Enriched session includes broker info")

    print_summary("Broker Test Harness", TEST_RESULTS)

if __name__ == "__main__":
    main()
