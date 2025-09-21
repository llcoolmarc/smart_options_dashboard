import random
from coaching.strategies import suggest_strategy
from utils.earnings import get_upcoming_earnings

MOCK_UNIVERSE = ["AAPL", "TSLA", "MSFT", "AMZN", "SPY"]

def find_next_trade(market_context="neutral"):
    """
    Suggest the next trade candidate based on market context.
    Returns ticker, mock stock data, and suggested strategy playbook.
    """
    # Filter out earnings risk (mock earnings)
    earnings = get_upcoming_earnings()
    safe_tickers = [t for t in MOCK_UNIVERSE if t not in earnings]

    if not safe_tickers:
        return {"error": "No safe tickers available (earnings risk)."}

    # Pick a random candidate (in reality this could pull live data)
    ticker = random.choice(safe_tickers)

    # Mock stock data
    stock_price = random.randint(50, 300)   # safe price range
    volatility = round(random.uniform(0.2, 0.5), 2)  # implied vol mock

    # Suggest strategy based on market context
    strat = suggest_strategy(market_context)

    return {
        "ticker": ticker,
        "stock_price": stock_price,
        "volatility": volatility,
        "strategy": strat
    }
