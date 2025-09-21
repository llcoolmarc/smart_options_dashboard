"""
utils/journal.py

Journal utilities for Defined-Risk Spreads Cockpit.
Phase 10: Scaling Ladder Enforcement
Phase 11: Profitability Enforcer
Phase 12: Auto-Scaling Gatekeeper
Phase 13: Graduation Lock Support
"""

import json
import os
from utils import discipline

# -------------------------------------------------------------------
# Absolute path handling
# -------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOURNAL_PATH = os.path.join(BASE_DIR, "trade_journal.json")


# -------------------------------------------------------------------
# Core Loaders
# -------------------------------------------------------------------
def load_journal(path: str = JOURNAL_PATH):
    if not os.path.exists(path):
        print(f"[DEBUG] Journal file not found at {path}")
        return []

    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            content = f.read().strip()
            if not content:
                print(f"[DEBUG] Journal file at {path} is empty")
                return []

        entries = json.loads(content)

        if isinstance(entries, dict):
            entries = [entries]
        elif not isinstance(entries, list):
            print(f"[DEBUG] Unexpected journal format in {path}")
            return []

        parsed_entries = []
        for e in entries:
            if isinstance(e, str):
                try:
                    e = json.loads(e)
                except Exception:
                    continue
            if isinstance(e, dict):
                parsed_entries.append(e)

        print(f"[DEBUG] Loaded {len(parsed_entries)} session entries from {path}")
        return parsed_entries
    except Exception as e:
        print(f"[DEBUG] Failed to load journal: {e}")
        return []


def save_journal(entries, path: str = JOURNAL_PATH):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
        print(f"[DEBUG] Journal saved with {len(entries)} entries → {path}")
    except Exception as e:
        print(f"Journal save failed: {e}")


# -------------------------------------------------------------------
# Trade Logging with Gatekeeper + Discipline
# -------------------------------------------------------------------
def log_trade(trade: dict, session_meta: dict = None, mode: str = "SIM", graduated: bool = False, path: str = JOURNAL_PATH):
    entries = load_journal(path)

    # ---------------- Gatekeeper Precheck (Phase 12) ----------------
    allowed, msg = discipline.precheck_trade_entry(trade, mode=mode, graduated=graduated)

    if not allowed:
        # Blocked trade in LIVE mode
        trade_entry = {
            "timestamp": session_meta.get("timestamp") if session_meta else None,
            "mode": mode,
            "graduated": graduated,
            "status": "blocked_entry",
            "reason": msg,
            "trade": trade
        }
        entries.append(trade_entry)
        save_journal(entries, path)
        print(f"[DEBUG] Trade blocked: {msg}")
        return trade_entry

    # ---------------- Normal Discipline Checks ----------------
    violations = discipline.run_discipline_checks(
        graduated=graduated,
        trades=[trade],
        portfolio=session_meta.get("portfolio", {}) if session_meta else {},
        mode=mode
    )

    scaling_violation = trade.get("scaling_violation", False)
    profit_violation = trade.get("profit_violation", False)

    trade["scaling_violation"] = scaling_violation
    trade["profit_violation"] = profit_violation
    trade["violation_details"] = trade.get("violation_details", [])

    # ---------------- Session Entry ----------------
    session_entry = {
        "timestamp": session_meta.get("timestamp") if session_meta else None,
        "mode": mode,
        "graduated": graduated,
        "trades": [trade],
        "session_audit": {
            **(session_meta or {}),
            "scaling_violations": int(scaling_violation),
            "profitability_violations": int(profit_violation),
            "total_violations": int(scaling_violation) + int(profit_violation)
        },
        "discipline": violations
    }

    # Log SIM oversize trades as practice violations
    if "SIM Oversize Practice" in msg:
        session_entry["status"] = "practice_violation"
        session_entry["reason"] = msg

    entries.append(session_entry)
    save_journal(entries, path)

    return trade


# -------------------------------------------------------------------
# Trade / Session Extractors
# -------------------------------------------------------------------
def load_all_trades(path: str = JOURNAL_PATH):
    entries = load_journal(path)
    trades = []
    flat_trades = 0
    nested_trades = 0

    for e in entries:
        if not isinstance(e, dict):
            continue

        # Case 1: flat trade dict
        if "pnl" in e:
            trades.append(e)
            flat_trades += 1

        # Case 2: nested trades
        session_trades = e.get("trades", [])
        if isinstance(session_trades, dict):
            trades.append(session_trades)
            nested_trades += 1
        elif isinstance(session_trades, list):
            for t in session_trades:
                if isinstance(t, str):
                    try:
                        t = json.loads(t)
                    except Exception:
                        continue
                if isinstance(t, dict):
                    trades.append(t)
                    nested_trades += 1

    print(f"[DEBUG] Parsed {len(trades)} trades → {path} "
          f"({flat_trades} flat, {nested_trades} nested)")
    return trades


def load_latest_session(path: str = JOURNAL_PATH):
    entries = load_journal(path)
    if not entries:
        return {}
    last_entry = entries[-1]
    if isinstance(last_entry, dict):
        return last_entry.get("session_audit", {})
    return {}
