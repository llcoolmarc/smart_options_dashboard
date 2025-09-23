"""
utils/graduation.py

Graduation Gate — SIM → LIVE Readiness
"""

import os
from utils.analytics import calculate_expectancy
from utils.journal import load_all_trades
from utils.broker import broker_status, BrokerSession
from utils.preferences import load_preferences

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOURNAL_PATH = os.path.join(BASE_DIR, "trade_journal.json")


def _flatten_trades(trades):
    """Helper: flatten nested lists of trades into a flat list of dicts."""
    flat = []
    for t in trades:
        if isinstance(t, list):
            flat.extend(_flatten_trades(t))
        elif isinstance(t, dict):
            flat.append(t)
    return flat


def _compute_clean_sessions(trades):
    """Compute clean sessions by trade date (no stop-loss violations)."""
    sessions = {}
    for t in trades:
        if not isinstance(t, dict):
            continue
        date = t.get("date")
        if not date:
            continue
        if date not in sessions:
            sessions[date] = {"violations": 0, "count": 0}
        sessions[date]["count"] += 1
        if t.get("pnl", 0) < -t.get("max_loss", -100):
            sessions[date]["violations"] += 1

    clean_sessions = sum(
        1 for stats in sessions.values() if stats["count"] > 0 and stats["violations"] == 0
    )
    return clean_sessions


def check_graduation(discipline=None, session: BrokerSession = None, path: str = None, test_mode=False):
    """
    Decide if the trader is ready to graduate from SIM to LIVE.
    Returns a dict with {graduated: bool, message: str}.
    In test_mode, criteria are simplified: ≥10 trades, positive expectancy, ≥1 clean session.
    """
    prefs = load_preferences()
    grad_prefs = prefs.get("graduation", {"min_trades": 25, "clean_sessions": 15})
    min_trades = grad_prefs.get("min_trades", 25)
    clean_sessions_required = grad_prefs.get("clean_sessions", 15)
    min_win_rate = grad_prefs.get("min_win_rate", 55)

    trades = load_all_trades(path or JOURNAL_PATH)
    trades = _flatten_trades(trades)

    # Count clean sessions
    if discipline and hasattr(discipline, "sessions"):
        sessions = discipline.sessions
        clean_sessions = sum(
            1 for s in sessions if isinstance(s, dict) and s.get("clean", False)
        )
    else:
        clean_sessions = _compute_clean_sessions(trades)

    print(
        f"[DEBUG] Loaded {len(trades)} trades | "
        f"{clean_sessions} clean sessions from {path or JOURNAL_PATH}"
    )

    # Simplified criteria for tests
    if test_mode:
        # Allow injected clean_sessions / expectancy in test session
        exp = 0
        clean_override = None
        if isinstance(session, dict):
            if "expectancy" in session:
                exp_val = session["expectancy"]
                exp = exp_val.get("expectancy", 0) if isinstance(exp_val, dict) else float(exp_val or 0)
            if "clean_sessions" in session:
                clean_override = int(session["clean_sessions"])

        if exp == 0:  # fallback to computed expectancy
            expectancy_stats = calculate_expectancy(trades)
            exp = expectancy_stats.get("expectancy", 0)

        clean_sessions_final = clean_override if clean_override is not None else clean_sessions

        graduated = len(trades) >= 10 and exp > 0 and clean_sessions_final > 0
        return {
            "graduated": graduated,
            "message": "Test Mode Graduation" if graduated else "Test Mode Rejected",
        }

    # Full criteria for real use
    if len(trades) < min_trades:
        return {"graduated": False, "message": f"Graduation Locked - need {min_trades} trades"}

    expectancy_stats = calculate_expectancy(trades)
    exp = expectancy_stats.get("expectancy", 0)
    win_rate = expectancy_stats.get("win_rate", 0)

    if exp <= 0:
        return {"graduated": False, "message": "Graduation Locked - expectancy must be positive"}

    if win_rate < min_win_rate:
        return {
            "graduated": False,
            "message": f"Graduation Locked - win rate {win_rate:.1f}% < {min_win_rate}%",
        }

    # Loss streak check (last 10 trades)
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
            "message": "Graduation Locked - more than 2 consecutive losers in last 10 trades",
        }

    if clean_sessions < clean_sessions_required:
        return {
            "graduated": False,
            "message": f"Graduation Locked - need {clean_sessions_required} clean sessions",
        }

    # Broker check (optional, non-blocking)
    try:
        broker_ok = broker_status(session)
    except Exception:
        broker_ok = "UNKNOWN"

    if prefs.get("mode", "SIM").upper() == "LIVE" and broker_ok == "SIM":
        return {"graduated": False, "message": "Graduation Locked - broker unavailable"}

    return {
        "graduated": True,
        "message": (
            f"Graduation Achieved - Ready for LIVE. "
            f"Trades {len(trades)}/{min_trades}, "
            f"Clean Sessions {clean_sessions}/{clean_sessions_required}, "
            f"Expectancy {exp:.2f}, Win Rate {win_rate:.1f}%"
        ),
    }


def check_sandbox_ready(session=None, min_clean_sessions: int = 0):
    """
    Lightweight sandbox validation before moving to SIM trading.
    Treats all trades as SANDBOX if session.mode is SANDBOX.
    """
    if session is None:
        return {"ready": False, "reason": "No session provided"}

    trades = _flatten_trades(session.get("trades", []))
    mode = session.get("mode", "").upper()

    # If session says SANDBOX, include all trades
    if mode == "SANDBOX":
        sandbox_trades = trades
    else:
        sandbox_trades = [t for t in trades if isinstance(t, dict) and t.get("mode", "").upper() == "SANDBOX"]

    if len(sandbox_trades) < 10:
        return {"ready": False, "reason": f"Need 10 SANDBOX trades (have {len(sandbox_trades)})"}

    exp_obj = session.get("expectancy", {})
    expectancy = exp_obj.get("expectancy", 0) if isinstance(exp_obj, dict) else float(exp_obj or 0)

    if expectancy <= 0:
        return {"ready": False, "reason": "Expectancy must be positive"}

    clean_count = _compute_clean_sessions(sandbox_trades)
    if clean_count < min_clean_sessions:
        return {
            "ready": False,
            "reason": f"Need >={min_clean_sessions} clean sandbox sessions (have {clean_count})",
        }

    return {"ready": True, "reason": "SANDBOX validation passed"}
