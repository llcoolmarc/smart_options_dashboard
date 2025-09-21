def check_allocation(portfolio, account):
    """
    Check portfolio allocation risks.
    Returns a list of warnings (if any).
    """
    warnings = []

    # Portfolio risk check
    total_risk = portfolio.total_risk()
    risk_cap = portfolio.portfolio_risk_cap()
    if total_risk > risk_cap * 0.9:  # warn if >90% of cap
        warnings.append(f"⚠️ Portfolio risk is {total_risk:.2f}, near cap {risk_cap:.2f}")

    # Concentration check
    for t in portfolio.trades:
        ticker = getattr(t["trade"], "ticker", "UNKNOWN")
        if portfolio.contracts_by_ticker(ticker) > 2:
            warnings.append(f"⚠️ Concentration risk: {ticker} has {portfolio.contracts_by_ticker(ticker)} contracts")

    return warnings
