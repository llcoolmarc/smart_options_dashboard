import random
from typing import Dict, Any, List

def best_strategy(expectancy_report: Dict[str, Any], portfolio: List[Dict[str, Any]], marketdata: Dict[str, Any], prefs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine the best trade strategy given expectancy, portfolio, and ladder rules.
    Returns both structured suggestion and plain-English coaching.
    """

    # Filter only positive expectancy symbols
    candidates = {s: r for s, r in expectancy_report.items() if r["expectancy"] > 0}

    if not candidates:
        return {
            "symbol": None,
            "strategy": None,
            "coaching": "No positive expectancy opportunities. Do not open new trades."
        }

    # Pick best expectancy symbol
    best_symbol = max(candidates, key=lambda s: candidates[s]["expectancy"])

    # Ladder rule: how many contracts allowed
    max_contracts = prefs.get("scaling_ladder", {}).get("max_contracts", 1)
    current_contracts = sum(1 for pos in portfolio if pos["symbol"] == best_symbol)

    if current_contracts >= max_contracts:
        return {
            "symbol": best_symbol,
            "strategy": None,
            "coaching": f"Ladder full for {best_symbol}. No new trades allowed."
        }

    # Choose strategy type
    # Simplified logic — can expand with volatility + trend
    if any(pos.get("shares", 0) > 0 for pos in portfolio if pos["symbol"] == best_symbol):
        strat_type = "Covered Call"
        # Dummy strike selection: ATM strike
        strike = marketdata.get(best_symbol, {}).get("atm_strike", 100)
        premium = marketdata.get(best_symbol, {}).get("cc_premium", round(random.uniform(1.0, 5.0), 2))
        coaching = f"Sell 1 Covered Call on {best_symbol} at {strike} strike for ${premium}."
    else:
        strat_type = "Cash-Secured Put"
        strike = marketdata.get(best_symbol, {}).get("csp_strike", 100)
        premium = marketdata.get(best_symbol, {}).get("csp_premium", round(random.uniform(1.0, 5.0), 2))
        coaching = f"Sell 1 Cash-Secured Put on {best_symbol} at {strike} strike for ${premium}."

    return {
        "symbol": best_symbol,
        "strategy": strat_type,
        "strike": strike,
        "premium": premium,
        "coaching": coaching
    }
