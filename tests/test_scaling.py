import pytest
from utils import scaling

def test_scaling_blocks_oversized_trade():
    portfolio = {"positions": [{"symbol": "AAPL", "strategy": "vertical", "max_loss": 500}]}
    result = scaling.check_scaling(portfolio, account_size=10000)
    assert result["compliant"] is False

def test_scaling_allows_valid_trade():
    portfolio = {"positions": [{"symbol": "MSFT", "strategy": "vertical", "max_loss": 100}]}
    result = scaling.check_scaling(portfolio, account_size=10000)
    assert result["compliant"] is True
