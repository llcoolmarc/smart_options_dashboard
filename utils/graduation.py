"""
utils/graduation.py

Graduation Gate — SIM → LIVE Readiness
Phase 10: Scaling Ladder Enforcement
Phase 11: Profitability Enforcer
Phase 13: Final Graduation Lock (25 trades / 15 clean sessions)
"""

import os
from utils.analytics import calculate_expectancy
from utils.journal import load_all_trades, load_journal
from utils.broker import broker_status, BrokerSession
from utils.preferences import load_preferences

# Absolute path to journal file (always relative to project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOURNAL_PATH = os.path.join(BASE_DIR, "trade_journal.json")


def check_graduation(discipline=None, session: BrokerSession = None):
    """
    Graduation Gate:
    - At least N trades in journal (default 25)
    - Expectancy > 0
    - Win rate ≥ 55%
    - No more than 2 consecutive losers in last 10 trades
    - At least M clean sessions (default 15)
    - Broker API online (LIVE only)
    """

    prefs = load_preferences()
    grad_prefs = prefs.get("graduation", {"min_trades": 25, "clean_sessions": 15})
    min_trades = grad_prefs.get("min_trades", 25)
    clean_sessions_required = grad_prefs.get("clean_sessions", 15)

    # Load trades & sessions
    trades = load_all_trades()
    sessions = load_journal()

    # 🔎 Debug Print
    print(f"[DEBUG] Loaded {len(trades)} trades | "
          f"{sum(1 for s in sessions if s.get('clean', False))} clean sessions "
          f"from {JOURNAL_PATH}")

    # --- Minimum trades check ---
    if len(trades) < min_trades:
        return {
            "graduated": False,
            "message": f"❌ Graduation Locked — Requires at least {min_trades} trades.\n"
                       f"Progress: Trades {len(trades)}/{min_trades}"
        }

    # --- Expectancy & win rate ---
    expectancy_stats = calculate_expectancy(trades)
    exp = expectancy_stats["expectancy"]
    win_rate = expectancy_stats["win_rate"]

    if exp <= 0:
        return {
            "graduated": False,
            "message": f"❌ Graduation Locked — Expectancy must be positive.\n"
                       f"Current Expectancy: {exp:.2f}"
        }
    if win_rate < 55:
        return {
            "graduated": False,
            "message": f"❌ Graduation Locked — Win rate {win_rate:.1f}% < 55%."
        }

    # --- Consecutive losers check ---
    last_10 = trades[-10:]
    loss_streak = 0
    max_loss_streak = 0
    for t in last_10:
        if t.get("pnl", 0) < 0:
            loss_streak += 1
            max_loss_streak = max(max_loss_streak, loss_streak)
        else:
            loss_streak = 0
    if max_loss_streak > 2:
        return {
            "graduated": False,
            "message": "❌ Graduation Locked — More than 2 consecutive losers in last 10 trades."
        }

    # --- Clean sessions check ---
    clean_sessions = sum(1 for s in sessions if s.get("clean", False))
    if clean_sessions < clean_sessions_required:
        return {
            "graduated": False,
            "message": f"❌ Graduation Locked — Requires at least {clean_sessions_required} clean sessions.\n"
                       f"Progress: Clean Sessions {clean_sessions}/{clean_sessions_required}"
        }

    # --- Broker check ---
    broker_ok = broker_status(session)
    if prefs.get("mode", "SIM").upper() == "LIVE" and broker_ok == "SIM":
        return {
            "graduated": False,
            "message": "❌ Graduation Locked — Broker API unavailable."
        }

    # --- Success ---
    return {
        "graduated": True,
        "message": (
            f"✅ Graduation Achieved — Ready for LIVE.\n"
            f"Trades {len(trades)}/{min_trades} | "
            f"Clean Sessions {clean_sessions}/{clean_sessions_required} | "
            f"Expectancy {exp:.2f} | Win Rate {win_rate:.1f}%"
        )
    }

def check_sandbox_ready(session=None):
    """
    Validate whether SANDBOX account is ready to unlock LIVE mode.
    Criteria:
      - At least 10 SANDBOX trades logged
      - Positive expectancy
    Returns:
      dict with {"ready": bool, "reason": str}
    """
    if session is None:
        return {"ready": False, "reason": "No session provided"}

    trades = session.get("trades", [])
    sandbox_trades = [t for t in trades if t.get("mode") == "SANDBOX"]

    if len(sandbox_trades) < 10:
        return {
            "ready": False,
            "reason": f"Need at least 10 SANDBOX trades (have {len(sandbox_trades)})"
        }

    expectancy = 0
    exp_obj = session.get("expectancy", {})
    if isinstance(exp_obj, dict):
        expectancy = exp_obj.get("expectancy", 0)
    elif isinstance(exp_obj, (int, float)):
        expectancy = exp_obj

    if expectancy <= 0:
        return {"ready": False, "reason": "Expectancy must remain positive"}

    return {"ready": True, "reason": "SANDBOX validation passed"}
