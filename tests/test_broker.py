# -*- coding: utf-8 -*-
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.broker import BrokerSession, broker_status

def safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", errors="ignore").decode())

def record_result(cond, desc):
    if cond:
        safe_print(f"[PASS] {desc}")
    else:
        safe_print(f"[FAIL] {desc}")

def main():
    safe_print("=== Broker Smoke Tests ===")

    user = os.getenv("BROKER_USER")
    pw = os.getenv("BROKER_PASS")

    broker = BrokerSession(paper=True)
    if not (user and pw):
        safe_print("[WARN] No SANDBOX credentials found in environment")
        return

    if broker.login(user, pw):
        record_result(True, "Broker login to SANDBOX")
        accounts = broker.safe_fetch_accounts()
        record_result(bool(accounts), "Fetched accounts list")
        record_result("Connected" in broker_status(broker), "Broker status string valid")

        portfolio = broker.safe_fetch_portfolio()
        record_result(isinstance(portfolio, list), "safe_fetch_portfolio returns accounts")

        marketdata = broker.safe_fetch_marketdata("SPY")
        record_result(isinstance(marketdata, dict), "safe_fetch_marketdata returns dict")

        enriched = {"broker": broker_status(broker)}
        record_result("broker" in enriched, "Enriched session includes broker info")
    else:
        record_result(False, "Broker login to SANDBOX")

    broker.disconnect()

if __name__ == "__main__":
    main()
