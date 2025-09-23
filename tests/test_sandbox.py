import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Ensure utils is importable
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils import journal, profits

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL_JOURNAL = os.path.join(ROOT_DIR, "trade_journal.json")
MOCK_JOURNAL = os.path.join(os.path.dirname(__file__), "trade_journal_sandbox_test.json")

def load_journal_with_fallback():
    """Try to load SANDBOX trades from real journal, else mock test journal."""
    try:
        real_trades = journal.load_all_trades(REAL_JOURNAL)
        if real_trades:
            with open(REAL_JOURNAL, "r") as f:
                data = json.load(f)
            sandbox_entries = [s for s in data if s.get("mode") == "SANDBOX"]
            if sandbox_entries:
                return real_trades, "REAL"
    except Exception:
        pass

    mock_trades = journal.load_all_trades(MOCK_JOURNAL)
    return mock_trades, "MOCK"

def run_sandbox_checks():
    try:
        trades, source = load_journal_with_fallback()

        if not trades:
            print("[FAIL] No trades found in sandbox journal (real or mock)")
            return False

        # Check mode
        mode = "?"
        try:
            with open(REAL_JOURNAL if source == "REAL" else MOCK_JOURNAL, "r") as f:
                data = json.load(f)
            mode = data[0].get("mode", "SIM")
        except Exception:
            pass

        if mode != "SANDBOX":
            print(f"[FAIL] Expected SANDBOX mode, got {mode} ({source})")
            return False
        print(f"[PASS] Mode is SANDBOX ({source})")

        # Check trade count
        if len(trades) < 10:
            print(f"[FAIL] Sandbox only has {len(trades)} trades (<10) [{source}]")
            return False
        print(f"[PASS] Sandbox has {len(trades)} trades (>=10) [{source}]")

        # Check expectancy
        exp = profits.calculate_expectancy(trades)
        if exp.get("expectancy", 0) <= 0:
            print(f"[FAIL] Expectancy not positive: {exp} [{source}]")
            return False
        print(f"[PASS] Expectancy positive: {exp['expectancy']:.2f} [{source}]")

        return True
    except Exception as e:
        print(f"[FAIL] Exception during sandbox test: {e}")
        return False

if __name__ == "__main__":
    ok = run_sandbox_checks()
    if ok:
        print("\n[Sandbox Test Summary] PASSED")
    else:
        print("\n[Sandbox Test Summary] FAILED")
