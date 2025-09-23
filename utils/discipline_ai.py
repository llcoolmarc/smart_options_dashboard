"""
utils/discipline_ai.py

Phase 18: Continuous Discipline AI
- Detects trading habit patterns
- Provides real-time corrective guidance
- Aggregates repeated violations into summaries
- Reinforces positive behavior (clean sessions)
"""

import datetime


def _flatten(trades):
    """Helper: flatten nested lists of trades into a flat list of dicts."""
    flat = []
    for t in trades:
        if isinstance(t, list):
            flat.extend(_flatten(t))
        elif isinstance(t, dict):
            flat.append(t)
    return flat


def analyze_habits(journal: list) -> dict:
    """
    Analyze trading journal for bad habits and clean sessions.
    Args:
        journal: list of trade dicts (possibly nested)
    Returns:
        dict with 'messages'
    """
    journal = _flatten(journal)
    messages = []
    today = datetime.date.today()

    # ---------------------------
    # Overtrading (daily trade count)
    # ---------------------------
    trades_today = [t for t in journal if t.get("date") == today.strftime("%Y-%m-%d")]
    if len(trades_today) > 2:
        messages.append(
            f"[Discipline AI] {len(trades_today)} trades today — risk of overtrading. Cap at 2 per day."
        )

    # ---------------------------
    # Revenge trading (after losses)
    # ---------------------------
    revenge_count = 0
    for i in range(1, len(journal)):
        prev, curr = journal[i - 1], journal[i]
        if prev.get("pnl", 0) < 0 and curr.get("date") == prev.get("date"):
            revenge_count += 1
    if revenge_count > 0:
        messages.append(
            f"[Discipline AI] Detected {revenge_count} revenge trade(s). Wait before re-entering after losses."
        )

    # ---------------------------
    # Ignoring stop-loss
    # ---------------------------
    stop_loss_violations = sum(
        1 for t in journal if t.get("pnl", 0) < -t.get("max_loss", -100)
    )
    if stop_loss_violations > 0:
        messages.append(
            f"[Discipline AI] {stop_loss_violations} trades exceeded planned max loss. "
            f"Stick to stop-loss discipline and exit earlier."
        )

    # ---------------------------
    # Symbol overexposure
    # ---------------------------
    symbol_counts = {}
    for t in journal:
        sym = t.get("symbol")
        if sym:
            symbol_counts[sym] = symbol_counts.get(sym, 0) + 1
    for sym, count in symbol_counts.items():
        if count > 5:
            messages.append(
                f"[Discipline AI] {count} trades in {sym}. Diversify to reduce symbol risk."
            )

    # ---------------------------
    # Positive Reinforcement: Clean Sessions
    # ---------------------------
    clean_sessions = 0
    session_map = {}
    for t in journal:
        d = t.get("date")
        if not d:
            continue
        if d not in session_map:
            session_map[d] = {"violations": 0, "count": 0}
        session_map[d]["count"] += 1
        if t.get("pnl", 0) < -t.get("max_loss", -100):
            session_map[d]["violations"] += 1

    for d, stats in session_map.items():
        if stats["count"] > 0 and stats["violations"] == 0:
            clean_sessions += 1

    if clean_sessions > 0:
        messages.append(
            f"[Discipline AI] {clean_sessions} session(s) were clean with zero violations. Stay consistent!"
        )

    # ---------------------------
    # No violations at all
    # ---------------------------
    if not messages:
        messages.append("[Discipline AI] No bad habits detected. Stay consistent.")

    return {"messages": messages}


def evaluate(journal: list, prefs: dict = None) -> dict:
    journal = _flatten(journal)
    return analyze_habits(journal)


def check_alerts(session: dict) -> dict:
    journal = _flatten(session.get("trades", []))
    return analyze_habits(journal)
