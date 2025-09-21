# -*- coding: utf-8 -*-
import sys, os, io
# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
# Ensure repo root in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import graduation
from utils.broker import BrokerSession, broker_status
from app_dash import get_enriched_session

TEST_RESULTS = {"pass": 0, "fail": 0}

def record_result(cond, desc):
    if cond: 
        print(f"[✅ PASS] {desc}"); TEST_RESULTS["pass"] += 1
    else: 
        print(f"[❌ FAIL] {desc}"); TEST_RESULTS["fail"] += 1

def print_summary(name, results):
    print(f"\n=== {name} Summary ===")
    print(f"✅ Passed: {results['pass']}")
    print(f"❌ Failed: {results['fail']}")
    if results["fail"] == 0:
        print("🎉 All tests passed successfully!")
    else:
        print("⚠️ Some tests failed — review output above.")

def main():
    # -------------------
    # Graduation Tests
    # -------------------
    grad = graduation.check_graduation()
    record_result(isinstance(grad, dict), "Graduation returns dict")
    record_result("graduated" in grad, "Graduation dict has 'graduated'")

    fail_case = {"trades": 10, "clean_sessions": 5, "expectancy": -0.5, "win_rate": 40}
    record_result(not graduation.check_graduation(fail_case)["graduated"], "Fail case rejected")

    pass_case = {"trades": 30, "clean_sessions": 20, "expectancy": 0.5, "win_rate": 60}
    grad_pass = graduation.check_graduation(pass_case)
    record_result(grad_pass["graduated"], "Pass case accepted")

    if grad_pass["graduated"]:
        broker = BrokerSession(paper=True)
        if broker.login("user", "pass"):  # dummy creds unless env set
            record_result("Connected" in broker_status(broker), "Broker connects after graduation")
            broker.disconnect()

    # -------------------
    # Sandbox Ready Tests
    # -------------------
    fake_session = {
        "mode": "SANDBOX",
        "trades": [{"mode": "SANDBOX", "pnl": 50}] * 5,  # only 5 trades
        "expectancy": {"expectancy": 0.8}
    }
    res = graduation.check_sandbox_ready(fake_session)
    record_result(not res["ready"], "Sandbox fails with <10 trades")

    fake_session["trades"] = [{"mode": "SANDBOX", "pnl": 50}] * 12
    fake_session["expectancy"] = {"expectancy": -0.5}
    res = graduation.check_sandbox_ready(fake_session)
    record_result(not res["ready"], "Sandbox fails with negative expectancy")

    fake_session["expectancy"] = {"expectancy": 0.5}
    res = graduation.check_sandbox_ready(fake_session)
    record_result(res["ready"], "Sandbox passes with ≥10 trades and positive expectancy")

    # -------------------
    # Enriched Session Checks
    # -------------------
    session = get_enriched_session()
    record_result(session.get("mode") in ["SIM", "SANDBOX", "LIVE"], f"Valid mode → {session.get('mode')}")
    record_result("discipline_ai" in session, "Discipline AI included")

    print_summary("Graduation + Sandbox Test Harness", TEST_RESULTS)

if __name__ == "__main__":
    main()
