"""
journal_logger.py

CLI tool for logging trades into trade_journal.json
Supports:
  - Adding new trades
  - Closing trades with realized PnL
"""

import json
import os
import datetime

JOURNAL_PATH = "trade_journal.json"


def load_journal():
    """Load the current journal or start a new one."""
    if not os.path.exists(JOURNAL_PATH):
        return []
    try:
        with open(JOURNAL_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_journal(entries):
    """Save journal back to file."""
    with open(JOURNAL_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


def add_trade():
    """Prompt user for trade details and add to journal."""
    symbol = input("Enter symbol (SPY/QQQ): ").strip().upper()
    strat = input("Enter strategy (put_spread/call_spread/iron_condor/butterfly): ").strip().lower()
    expiry = input("Enter expiration (YYYY-MM-DD): ").strip()
    contracts = int(input("Enter contracts: ").strip())
    entry_price = float(input("Enter net credit/debit: ").strip())
    notes = input("Notes: ").strip()

    # Legs
    legs = []
    print("Enter legs (type 'done' when finished):")
    while True:
        action = input("  Action (BUY/SELL or 'done'): ").strip().upper()
        if action == "DONE":
            break
        strike = float(input("  Strike: ").strip())
        leg_expiry = input(f"  Expiry (default {expiry}): ").strip() or expiry
        premium = float(input("  Premium: ").strip())
        legs.append({
            "action": action,
            "strike": strike,
            "expiry": leg_expiry,
            "premium": premium
        })

    # Build trade
    trade_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    trade = {
        "id": trade_id,
        "symbol": symbol,
        "type": strat,
        "legs": legs,
        "expiration": expiry,
        "entry_price": entry_price,
        "contracts": contracts,
        "status": "OPEN",
        "notes": notes
    }

    # Load journal
    entries = load_journal()

    # If no sessions exist, create one
    if not entries:
        session = {
            "timestamp": datetime.datetime.now().isoformat(),
            "mode": "SIM",
            "session_audit": {
                "expectancy": 0.0,
                "discipline": [],
                "instructions": [],
                "graduation": "❌ SIM Only — not eligible for LIVE",
                "expectancy_report": {}
            },
            "trades": []
        }
        entries.append(session)

    # Append to most recent session
    entries[-1]["trades"].append(trade)

    save_journal(entries)
    print(f"✅ Trade {trade_id} added to journal.")


def close_trade():
    """Prompt user to close an open trade and record PnL."""
    entries = load_journal()
    if not entries or not entries[-1].get("trades"):
        print("⚠️ No trades found.")
        return

    trades = entries[-1]["trades"]
    open_trades = [t for t in trades if t.get("status") == "OPEN"]

    if not open_trades:
        print("⚠️ No open trades to close.")
        return

    # Show open trades
    print("\nOpen Trades:")
    for i, t in enumerate(open_trades, start=1):
        print(f"{i}. {t['id']} | {t['symbol']} {t['type']} exp {t['expiration']} @ {t['entry_price']}")

    choice = int(input("\nSelect trade to close (number): ").strip()) - 1
    if choice < 0 or choice >= len(open_trades):
        print("⚠️ Invalid choice.")
        return

    trade = open_trades[choice]

    exit_price = float(input("Enter exit price (credit/debit): ").strip())
    realized = (trade["entry_price"] - exit_price) * trade["contracts"] * 100  # per-contract multiplier

    trade["status"] = "CLOSED"
    trade["exit_price"] = exit_price
    trade["realized"] = realized
    trade["closed_at"] = datetime.datetime.now().isoformat()

    save_journal(entries)

    result = "✅ WIN" if realized > 0 else "❌ LOSS"
    print(f"{result}: Closed {trade['symbol']} {trade['type']} for {realized:.2f}.")


def main():
    print("Journal Logger")
    print("1. Add trade")
    print("2. Close trade")
    choice = input("Select option: ").strip()

    if choice == "1":
        add_trade()
    elif choice == "2":
        close_trade()
    else:
        print("⚠️ Invalid option.")


if __name__ == "__main__":
    main()
