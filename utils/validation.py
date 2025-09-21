"""
Validation module for trades and accounts.
Enforces discipline rules before trade execution.
"""

import math


class Account:
    def __init__(self, balance, max_risk_per_trade=0.02, min_dte=20):
        self.balance = balance
        self.max_risk_per_trade = max_risk_per_trade
        self.min_dte = min_dte


class Trade:
    def __init__(self, type, risk, margin_required, dte, stock_price,
                 premium=0, expiry=None, strike_price=None):
        self.type = type  # "cash_secured_put", "credit_spread", "iron_condor"
        self.risk = risk
        self.margin_required = margin_required
        self.dte = dte
        self.stock_price = stock_price
        self.premium = premium
        self.expiry = expiry
        self.strike_price = strike_price
        self.legs = []  # optional multi-leg details
        self.ticker = None  # set externally for tracking


def validate_trade(trade, account, portfolio, contracts):
    """
    Validate a trade against account rules and portfolio guardrails.
    Returns (is_valid, message).
    """

    # === Risk per trade check ===
    max_risk_allowed = account.balance * account.max_risk_per_trade
    total_trade_risk = trade.risk * contracts

    if total_trade_risk > max_risk_allowed:
        return False, (f"🚫 Trade risk ${total_trade_risk:.2f} exceeds "
                       f"max per-trade risk ${max_risk_allowed:.2f}.")

    # === DTE check ===
    if trade.dte < account.min_dte:
        return False, (f"🚫 Trade DTE {trade.dte} is below minimum "
                       f"{account.min_dte} days.")

    # === Multi-leg structure check ===
    if trade.type == "credit_spread":
        if len(trade.legs) != 2:
            return False, "🚫 Credit spread must have exactly 2 legs."
        expiries = {leg.get("expiry") for leg in trade.legs}
        if len(expiries) > 1:
            return False, "🚫 Credit spread legs must share the same expiry."

    if trade.type == "iron_condor":
        if len(trade.legs) != 4:
            return False, "🚫 Iron condor must have exactly 4 legs."
        expiries = {leg.get("expiry") for leg in trade.legs}
        if len(expiries) > 1:
            return False, "🚫 Iron condor legs must share the same expiry."

    # === Portfolio guardrails ===
    portfolio_risk = portfolio.total_risk() + total_trade_risk
    if portfolio_risk > portfolio.portfolio_risk_cap():
        return False, (f"🚫 Adding this trade exceeds portfolio risk cap. "
                       f"Total risk would be ${portfolio_risk:.2f}.")

    total_contracts = portfolio.total_contracts() + contracts
    if total_contracts > portfolio.contract_cap():
        return False, (f"🚫 Adding this trade exceeds contract cap. "
                       f"Total contracts would be {total_contracts}.")

    return True, (f"✅ Trade validated. Risk ${total_trade_risk:.2f} "
                  f"within per-trade cap ${max_risk_allowed:.2f}.")
