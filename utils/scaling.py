"""
utils/scaling.py

Phase 15: Portfolio Scaling Rules
- Max risk per trade
- Max portfolio risk
- Symbol allocation limits
- Max number of open trades
- Per-strategy limits
Outputs plain-English warnings for the dashboard.
"""

def check_scaling(portfolio: dict, account_size: float = 10000, max_trades: int = 5) -> dict:
    """
    Evaluate portfolio scaling rules.
    Returns dict with compliance status and messages.
    """
    messages = []
    compliant = True

    positions = portfolio.get("positions", [])
    total_risk = 0
    symbol_exposure = {}
    strategy_counts = {"iron_condor": 0, "butterfly": 0, "vertical": 0}

    # ---------------------------
    # Per-trade and total risk checks
    # ---------------------------
    for pos in positions:
        if not isinstance(pos, dict):
            # Skip malformed entries gracefully
            continue

        sym = pos.get("symbol", "Unknown")
        strat = str(pos.get("strategy", "")).lower()
        risk = float(pos.get("max_loss", 0))  # defined-risk per trade
        total_risk += risk
        symbol_exposure[sym] = symbol_exposure.get(sym, 0) + risk

        # Count strategies
        if "condor" in strat:
            strategy_counts["iron_condor"] += 1
        elif "butterfly" in strat:
            strategy_counts["butterfly"] += 1
        elif "vertical" in strat or "spread" in strat:
            strategy_counts["vertical"] += 1

        # Max risk per trade
        if risk > account_size * 0.02:  # >2% equity
            compliant = False
            messages.append(
                f"⚠️ {sym}: Trade risk {risk} exceeds 2% of account equity. "
                "Reduce contract size."
            )

    # Max portfolio risk
    if total_risk > account_size * 0.05:  # >5% equity
        compliant = False
        messages.append(
            f"⚠️ Total portfolio risk {total_risk} exceeds 5% of account equity. "
            "Close or reduce positions."
        )

    # Symbol allocation
    for sym, risk in symbol_exposure.items():
        share = risk / account_size
        if sym == "SPY" and share > 0.5:
            compliant = False
            messages.append(
                f"⚠️ Too much exposure in SPY ({share:.0%} of account). "
                "Limit to ≤50%."
            )
        if sym == "QQQ" and share > 0.3:
            compliant = False
            messages.append(
                f"⚠️ Too much exposure in QQQ ({share:.0%} of account). "
                "Limit to ≤30%."
            )

    # ---------------------------
    # Max number of trades
    # ---------------------------
    open_trades = sum(1 for p in positions if isinstance(p, dict))
    if open_trades > max_trades:
        compliant = False
        messages.append(
            f"⚠️ Too many open trades ({open_trades}). "
            f"Limit is {max_trades}. Having too many positions reduces discipline."
        )
    else:
        messages.append(f"✅ Number of open trades ({open_trades}) is within safe limits.")

    # ---------------------------
    # Per-strategy limits
    # ---------------------------
    if strategy_counts["iron_condor"] > 2:
        compliant = False
        messages.append(
            f"⚠️ Too many Iron Condors ({strategy_counts['iron_condor']}). Limit is 2."
        )
    if strategy_counts["butterfly"] > 2:
        compliant = False
        messages.append(
            f"⚠️ Too many Butterflies ({strategy_counts['butterfly']}). Limit is 2."
        )
    if strategy_counts["vertical"] > 3:
        compliant = False
        messages.append(
            f"⚠️ Too many Verticals ({strategy_counts['vertical']}). Limit is 3."
        )

    if all(count <= limit for count, limit in zip(
        strategy_counts.values(), [2, 2, 3])):
        messages.append("✅ Strategy mix is within safe limits.")

    # ---------------------------
    # Final check
    # ---------------------------
    if compliant:
        messages.append("✅ Portfolio scaling is within safe limits.")

    return {"compliant": compliant, "messages": messages}


def check_allocation(session: dict) -> dict:
    """
    Alias wrapper so app_dash.py can call scaling.check_allocation(session).
    """
    trades = session.get("trades", [])
    # Flatten in case of nested lists
    flat_positions = []
    for t in trades:
        if isinstance(t, list):
            flat_positions.extend(t)
        else:
            flat_positions.append(t)

    portfolio = {"positions": flat_positions}
    account_size = session.get("account_size", 10000)
    return check_scaling(portfolio, account_size=account_size)
