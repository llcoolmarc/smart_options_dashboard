# -*- coding: utf-8 -*-
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import graduation
from utils.broker import BrokerSession, broker_status
from app_dash import get_enriched_session

TEST_RESULTS = {"pass": 0, "fail": 0}

def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", errors="ignore").decode())

def record_result(cond: bool, desc: str):
    if cond:
        safe_print(f"[PASS] {desc}")
        TEST_RESULTS["pass"] += 1
    else:
        safe_print(f"[FAIL] {desc}")
        TEST_RESULTS["fail"] += 1

def print_summary(name: str, results: dict):
    safe_print(f"\n=== {name} Summary ===")
    safe_print(f"Passed: {results['pass']}")
    safe_print(f"Failed: {results['fail']}")
    if results["fail"] == 0:
        safe_print("All tests passed successfully!")
    else:
        safe_print("Some tests failed — review output above.")

def main():
    # --- Graduation core checks ---
    grad = graduation.check_graduation(test_mode=True)
    record_result(isinstance(grad, dict), "Graduation returns dict")
    record_result("graduated" in grad, "Graduation dict has 'graduated'")

    # Fail case
    fail_session = {
        "trades": [{}] * 10,
        "expectancy": -0.5,  # float
        "clean_sessions": 5,
    }
    grad_fail = graduation.check_graduation(session=fail_session, test_mode=True)
    record_result(not grad_fail.get("graduated", False), "Fail case rejected")

    # Pass case
    pass_session = {
        "trades": [{}] * 30,
        "expectancy": 0.5,  # float
        "clean_sessions": 20,
    }
    grad_pass = graduation.check_graduation(session=pass_session, test_mode=True)
    record_result(grad_pass.get("graduated", False), "Pass case accepted")

    # --- Broker gate after graduation (only if creds exist) ---
    broker = BrokerSession(paper=True, base_url="https://api.cert.tastyworks.com")
    if os.getenv("BROKER_SANDBOX_USER") and os.getenv("BROKER_SANDBOX_PASS"):
        if broker.login(os.getenv("BROKER_SANDBOX_USER"), os.getenv("BROKER_SANDBOX_PASS")):
            record_result("Connected" in broker_status(broker), "Broker connects after graduation")
            broker.disconnect()
        else:
            record_result(False, "Broker login failed (check credentials)")
    else:
        safe_print("[WARN] No SANDBOX credentials found in environment")

    # --- Sandbox readiness checks ---
    fake_session = {
        "mode": "SANDBOX",
        "trades": [{}] * 5,
        "expectancy": 0.8,
    }
    res = graduation.check_sandbox_ready(fake_session)
    record_result(not res.get("ready", False), "Sandbox fails with <10 trades")

    fake_session["trades"] = [{}] * 12
    fake_session["expectancy"] = -0.5
    res = graduation.check_sandbox_ready(fake_session)
    record_result(not res.get("ready", False), "Sandbox fails with negative expectancy")

    fake_session["expectancy"] = 0.5
    res = graduation.check_sandbox_ready(fake_session)
    record_result(res.get("ready", False), "Sandbox passes with ≥10 trades and positive expectancy")

    # --- Enriched session ---
    session = get_enriched_session()
    record_result(session.get("mode") in ["SIM", "SANDBOX", "LIVE"], f"Valid mode -> {session.get('mode')}")
    record_result("discipline_ai" in session, "Discipline AI included")

    print_summary("Graduation + Sandbox Test Harness", TEST_RESULTS)

if __name__ == "__main__":
    main()
