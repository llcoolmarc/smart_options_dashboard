"""
utils/discipline.py

Discipline enforcement for Defined-Risk Spreads Cockpit.
Phase 10: Scaling Ladder Enforcement
Phase 11: Profitability Enforcer
Phase 12: Auto-Scaling Gatekeeper
"""

import datetime
from utils.preferences import load_preferences
from utils.analytics import calculate_expectancy


# ---------------------------
# Pre-Check: Gatekeeper (Phase 12)
# ---------------------------

def precheck_trade_entry(trade, mode="SIM", graduated=False):
    """
    Auto-block trades that exceed ladder rung before logging.
    Returns (allowed: bool, message: str)
    """
    prefs = load_preferences()
    ladder_prefs = prefs.get("ladder", {})
    allowed_rungs = ladder_prefs.get("contracts", [1])

    if not graduated:
        allowed_rungs = allowed_rungs[:2]

    contracts = trade.get("contracts", 0)
    allowed = max([r for r in allowed_rungs if r <= contracts], default=allowed_rungs[0])

    if contracts > allowed:
        msg = f"Trade {trade.get('symbol')} {contracts} exceeds ladder rung {allowed}."
        if mode.upper() == "LIVE":
            return False, f"❌ Gatekeeper Block: {msg}"
        else:
            return True, f"⚠️ SIM Oversize Practice: {msg}"

    return True, "✅ Trade within ladder limits."


# ---------------------------
# Scaling Ladder Enforcement
# ---------------------------

def check_scaling_ladder(trades, mode="SIM", graduated=False):
    prefs = load_preferences()
    ladder_prefs = prefs.get("ladder", {})
    allowed_rungs = ladder_prefs.get("contracts", [1])
    enforce_live = ladder_prefs.get("enforce_live", True)
    warn_sim = ladder_prefs.get("warn_sim", True)

    if not graduated:
        allowed_rungs = allowed_rungs[:2]

    violations = []

    for trade in trades:
        contracts = trade.get("contracts", 0)
        allowed = max([r for r in allowed_rungs if r <= contracts], default=allowed_rungs[0])

        if contracts > allowed:
            msg = f"Trade {trade.get('symbol')} {contracts} exceeds ladder rung {allowed}."
            if mode.upper() == "LIVE" and enforce_live:
                violations.append(f"❌ Scaling violation: {msg}")
                trade["scaling_violation"] = True
                trade.setdefault("violation_details", []).append(f"❌ {msg}")
            elif mode.upper() == "SIM" and warn_sim:
                violations.append(f"⚠️ Scaling warning: {msg}")
                trade["scaling_violation"] = True
                trade.setdefault("violation_details", []).append(f"⚠️ {msg}")
        else:
            trade["scaling_violation"] = False
            trade.setdefault("violation_details", [])

    return violations


# ---------------------------
# Profitability Enforcement (Phase 11)
# ---------------------------

def check_profitability(trades, mode="SIM"):
    violations = []

    for trade in trades:
        exp_val = trade.get("expectancy")
        rr_ratio = None

        if exp_val is None:
            exp_data = calculate_expectancy([trade])
            exp_val = exp_data["expectancy"]
            trade["expectancy"] = exp_val

        max_gain = trade.get("max_gain")
        max_loss = trade.get("max_loss")
        if max_gain and max_loss and max_loss > 0:
            rr_ratio = max_gain / max_loss
            trade["reward_risk"] = rr_ratio

        if exp_val is not None and exp_val <= 0:
            msg = f"Trade {trade.get('symbol')} has negative expectancy ({exp_val:.2f})."
            if mode.upper() == "LIVE":
                violations.append(f"❌ Profitability violation: {msg}")
                trade["profit_violation"] = True
                trade.setdefault("violation_details", []).append(f"❌ {msg}")
            else:
                violations.append(f"⚠️ Profitability warning: {msg}")
                trade["profit_violation"] = True
                trade.setdefault("violation_details", []).append(f"⚠️ {msg}")

        if rr_ratio is not None and rr_ratio < 1.5:
            msg = f"Trade {trade.get('symbol')} reward:risk {rr_ratio:.2f} below 1.5."
            if mode.upper() == "LIVE":
                violations.append(f"❌ Profitability violation: {msg}")
                trade["profit_violation"] = True
                trade.setdefault("violation_details", []).append(f"❌ {msg}")
            else:
                violations.append(f"⚠️ Profitability warning: {msg}")
                trade["profit_violation"] = True
                trade.setdefault("violation_details", []).append(f"⚠️ {msg}")

        if "profit_violation" not in trade:
            trade["profit_violation"] = False
            trade.setdefault("violation_details", [])

    return violations


# ---------------------------
# Other Checks (placeholders)
# ---------------------------

def check_overexposure(portfolio):
    return []

def check_expiration_clusters(trades):
    return []

def check_contract_skew(portfolio):
    return []


# ---------------------------
# Unified Discipline Runner
# ---------------------------

def run_discipline_checks(graduated=False, trades=None, portfolio=None, mode="SIM"):
    violations = []

    if trades:
        violations.extend(check_scaling_ladder(trades, mode=mode, graduated=graduated))
    if trades:
        violations.extend(check_profitability(trades, mode=mode))
    if portfolio:
        violations.extend(check_overexposure(portfolio))
    if trades:
        violations.extend(check_expiration_clusters(trades))
    if portfolio:
        violations.extend(check_contract_skew(portfolio))

    blocked = any("❌" in v for v in violations)

    return {
        "blocked": blocked,
        "violations": violations,
        "instructions": ["Reduce violations before continuing."] if violations else []
    }