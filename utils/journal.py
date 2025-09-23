# -*- coding: utf-8 -*-
import json
import os


def load_all_trades(path):
    """
    Load all trades from a JSON file.
    Always returns a flat list of trade dicts.
    Handles both flat trade lists and nested trade sessions.
    """
    if not os.path.exists(path):
        print(f"[DEBUG] No journal file at {path}, returning []")
        return []

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"[DEBUG] Failed to parse {path}, returning []")
            return []

    if not data:  # empty file
        print(f"[DEBUG] Empty journal file {path}, returning []")
        return []

    trades = []
    if isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict) and "trades" in entry and isinstance(entry["trades"], list):
                trades.extend(entry["trades"])  # nested session
            elif isinstance(entry, dict):
                trades.append(entry)  # flat trade
    elif isinstance(data, dict):
        if "trades" in data and isinstance(data["trades"], list):
            trades.extend(data["trades"])
        else:
            trades.append(data)

    print(f"[DEBUG] Parsed {len(trades)} trades -> {path}")
    return trades


def load_sessions(path):
    """
    Load journal sessions (list of sessions).
    Each session is a dict with a 'trades' list inside.
    Used by graduation/sandbox logic.
    """
    if not os.path.exists(path):
        print(f"[DEBUG] No journal file at {path}, returning []")
        return []

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"[DEBUG] Failed to parse {path}, returning []")
            return []

    if not data:
        print(f"[DEBUG] Empty journal file {path}, returning []")
        return []

    sessions = []
    if isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict) and "trades" in entry and isinstance(entry["trades"], list):
                sessions.append(entry)
            elif isinstance(entry, dict):
                sessions.append({"trades": [entry]})
    elif isinstance(data, dict):
        if "trades" in data and isinstance(data["trades"], list):
            sessions.append(data)
        else:
            sessions.append({"trades": [data]})

    print(f"[DEBUG] Parsed {len(sessions)} sessions -> {path}")
    return sessions


def save_trades(path, trades):
    """
    Save trades to a JSON file.
    Writes a flat list of trade dicts for simplicity.
    """
    if not trades:
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        print(f"[DEBUG] Saved 0 trades -> {path}")
        return

    if not isinstance(trades, list):
        trades = [trades]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(trades, f, indent=2)

    print(f"[DEBUG] Saved {len(trades)} trades -> {path}")


def enrich_session(trades):
    """
    Add extra metadata to a session of trades.
    Includes:
      - mode (default SANDBOX)
      - expectancy
      - discipline_ai with score
      - broker stub
    """
    expectancy = sum(t.get("pnl", 0) for t in trades if isinstance(t, dict)) / max(len(trades), 1)

    enriched = {
        "mode": "SANDBOX",
        "expectancy": expectancy,
        "discipline_ai": {
            "score": max(0, 100 - len(trades)),  # simple score placeholder
            "messages": [
                "Discipline AI: Keep stop losses tight.",
                "Avoid revenge trading after losses.",
            ],
        },
        "broker": {"connected": False, "account": "demo"},
    }

    print(
        f"[DEBUG] Enriched session -> mode={enriched['mode']}, "
        f"expectancy={enriched['expectancy']:.2f}, "
        f"discipline_ai.score={enriched['discipline_ai']['score']}"
    )

    return enriched
