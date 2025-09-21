"""
components/risk_heatmap.py (L53.7)

Visual Portfolio Risk Heatmaps

- Capital concentration by ticker
- Expiration concentration by week
- Contract type exposure (calls vs puts)
"""

import matplotlib.pyplot as plt
from collections import Counter
from datetime import datetime
from utils.portfolio import get_portfolio_positions


def plot_capital_concentration(portfolio):
    """Bar chart of capital allocation by symbol."""
    tickers = [p["symbol"] for p in portfolio]
    values = [p["market_value"] for p in portfolio]

    plt.figure(figsize=(6,4))
    plt.bar(tickers, values)
    plt.title("Capital Concentration by Symbol")
    plt.ylabel("Market Value ($)")
    plt.xlabel("Symbol")
    plt.tight_layout()
    plt.show()


def plot_expiration_clusters(portfolio):
    """Bar chart of contracts expiring by week."""
    expirations = [p.get("expiry") for p in portfolio if p.get("expiry")]
    weeks = []
    for exp in expirations:
        try:
            dt = datetime.strptime(exp, "%Y-%m-%d")
            weeks.append(dt.isocalendar()[1])
        except Exception:
            continue

    week_counts = Counter(weeks)

    plt.figure(figsize=(6,4))
    plt.bar(week_counts.keys(), week_counts.values())
    plt.title("Expiration Clusters by Week")
    plt.ylabel("Contracts Expiring")
    plt.xlabel("ISO Week Number")
    plt.tight_layout()
    plt.show()


def plot_contract_type_exposure(portfolio):
    """Pie chart of puts vs calls exposure."""
    types = Counter([p.get("type", "Unknown") for p in portfolio])

    plt.figure(figsize=(5,5))
    plt.pie(types.values(), labels=types.keys(), autopct="%1.1f%%")
    plt.title("Contract Type Exposure")
    plt.tight_layout()
    plt.show()


def show_risk_heatmaps():
    """Convenience function to show all risk views."""
    portfolio = get_portfolio_positions()

    if not portfolio:
        print("No portfolio positions available for risk heatmaps.")
        return

    plot_capital_concentration(portfolio)
    plot_expiration_clusters(portfolio)
    plot_contract_type_exposure(portfolio)
