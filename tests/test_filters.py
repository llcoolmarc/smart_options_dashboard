import pytest
from utils import filters

def test_high_vix_blocks_trade():
    market = {"symbols": {}}
    result = filters.check_filters(market, events=[], vix=35)
    assert result["compliant"] is False

def test_normal_conditions_allow_trade():
    market = {"symbols": {}}
    result = filters.check_filters(market, events=[], vix=18)
    assert result["compliant"] is True
