"""
utils/marketdata.py

Market data utilities for the Defined-Risk Spreads Cockpit.
Handles both LIVE broker API feeds and SIM fallback mode.
Ensures missing fields (like 'market_value') do not crash cockpit.
"""

import random

# -------------------------------------------------------------------
# SIM-SAFE SNAPSHOT BUILDER
# -------------------------------------------------------------------

def fetch_market_snapshot(portfolio):
    """
    Fetch a market snapshot for portfolio holdings.

    Args:
        portfolio (dict): current portfolio dictionary
            Example:
            {
                "SPY": {"contracts": 2, "price": 420.50},
                "QQQ": {"contracts": 1}
            }

    Returns:
        dict: snapshot keyed by symbol
            {
                "SPY": {"market_value": 841.0, "price": 420.50, "contracts": 2},
                "QQQ": {"market_value": 0, "price": 0, "contracts": 1}
            }
    """
    snapshot = {}

    for sym, pos in portfolio.items():
        try:
            # Pull from broker-style fields if available
            market_val = pos.get("market_value", 0)
            price = pos.get("price", 0)
            contracts = pos.get("contracts", 0)

            snapshot[sym] = {
                "market_value": market_val,
                "price": price,
                "contracts": contracts,
            }

        except Exception as e:
            print(f"[WARN] Marketdata fallback for {sym}: {e}")
            snapshot[sym] = {
                "market_value": 0,
                "price": 0,
                "contracts": 0,
            }

    return snapshot


# -------------------------------------------------------------------
# OPTIONAL SIM HELPERS
# -------------------------------------------------------------------

def simulate_price(symbol, base_price=100):
    """
    Generate a random SIM price for testing (when no broker feed is present).
    """
    return round(base_price * (1 + random.uniform(-0.02, 0.02)), 2)


def enrich_with_prices(snapshot):
    """
    Add random SIM prices to a snapshot if missing.
    Useful in demo/testing mode when no broker is connected.
    """
    for sym, data in snapshot.items():
        if data.get("price", 0) == 0:
            data["price"] = simulate_price(sym, 100)
            data["market_value"] = data["price"] * data.get("contracts", 0)
    return snapshot


# -------------------------------------------------------------------
# ENTRY POINT (cockpit will call fetch_market_snapshot)
# -------------------------------------------------------------------

def get_snapshot(portfolio, sim_mode=True):
    """
    Entry point for cockpit.
    - In LIVE mode, this would call a broker API.
    - In SIM mode, we enrich with random prices.

    Args:
        portfolio (dict)
        sim_mode (bool)

    Returns:
        dict snapshot
    """
    snapshot = fetch_market_snapshot(portfolio)
    if sim_mode:
        snapshot = enrich_with_prices(snapshot)
    return snapshot
