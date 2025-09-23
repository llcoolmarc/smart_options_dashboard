# -*- coding: utf-8 -*-
import sys, io, os, subprocess

# Force UTF-8 output (fix Windows cp1252 crash with emojis and arrows)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

TESTS = [
    ("Broker", os.path.join(BASE_DIR, "test_broker.py")),
    ("Graduation", os.path.join(BASE_DIR, "test_graduation.py")),
    ("Journal", os.path.join(BASE_DIR, "test_journal.py")),
    ("Scaling", os.path.join(BASE_DIR, "test_scaling.py")),
    ("Filters", os.path.join(BASE_DIR, "test_filters.py")),
    ("Profits", os.path.join(BASE_DIR, "test_profits.py")),
    ("DisciplineAI", os.path.join(BASE_DIR, "test_discipline_ai.py")),
    ("Sandbox", os.path.join(BASE_DIR, "test_sandbox.py")),
]

def clean_output(text: str) -> str:
    """Replace emojis with plain text for safer Windows logs."""
    replacements = {
        "✅": "[PASS]",
        "❌": "[FAIL]",
        "⚠️": "[WARN]",
        "→": "->",
        "⛔": "[BLOCK]",
    }
    for bad, repl in replacements.items():
        text = text.replace(bad, repl)
    return text

def run_test(name, path):
    print(f"\n=== Running {name} Tests ===")
    try:
        # Inherit environment and patch PYTHONPATH so child tests can import utils
        env = os.environ.copy()
        env["PYTHONPATH"] = PROJECT_ROOT + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env
        )
        stdout = clean_output(result.stdout or "")
        stderr = clean_output(result.stderr or "")

        print(stdout)
        if stderr:
            print("[STDERR]", stderr)

        # Detect failures
        if "[FAIL]" in stdout or result.returncode != 0:
            return False
        # [WARN] does not fail the test
        return True
    except Exception as e:
        print(f"[ERROR] Could not run {name} tests: {e}")
        return False

if __name__ == "__main__":
    results = {name: run_test(name, path) for name, path in TESTS}

    print("\n=== Master Test Summary ===")
    for name, ok in results.items():
        print(f"{name:<12} {'✅ PASSED' if ok else '❌ FAILED'}")

    if all(results.values()):
        print("\n🎉 ALL TESTS PASSED -> Cockpit integrity verified (Phase 19+21 harness ready)")
    else:
        print("\n⚠️ Some tests failed — review harness outputs above.")
