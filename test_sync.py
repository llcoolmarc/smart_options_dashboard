"""
test_sync.py — Cockpit Safe-Mode Test Harness
Launches the dashboard in --safe mode and injects fake broker data.
"""

import sys
import json
import os
from utils import journal
from components import dashboard


def main():
    # Fake broker data (mocking Tastytrade API response)
    fake_broker_data = {
        "mode": "LIVE",
        "positions": [
            {"symbol": "AAPL", "contracts": 1, "strike": 175, "premium": 2.35}
        ],
        "fills": [
            {
                "timestamp": "2025-09-12T20:00:00Z",
                "symbol": "AAPL",
                "strategy": "Cash-Secured Put",
                "contracts": 1,
                "strike": 175,
                "premium": 2.35,
            },
            {
                "timestamp": "2025-09-12T20:05:00Z",
                "symbol": "MSFT",
                "strategy": "Covered Call",
                "contracts": 1,
                "strike": 340,
                "premium": 1.25,
            },
        ],
        "timestamp": "2025-09-12T20:10:00Z",
    }

    print("🔧 Running Cockpit in SAFE MODE with Fake Broker Data")
    updated_journal = journal.reconcile_journal(fake_broker_data, safe_mode=True)

    # Render dashboard with safe mode = True
    dashboard.render_dashboard(safe_mode=True)

    # Confirm sandbox file location
    fake_path = os.path.join(
        os.path.dirname(__file__), "trade_journal_fake.json"
    )
    print(f"\n✅ Fake sync complete. Entries written to {fake_path}")


if __name__ == "__main__":
    main()
