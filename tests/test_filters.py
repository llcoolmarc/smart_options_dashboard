import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils import filters


def test_high_vix_blocks_trade():
    market = {"symbols": {}}
    result = filters.check_filters(market, events=[], vix=35)
    assert result["compliant"] is False


def test_normal_conditions_allow_trade():
    market = {"symbols": {}}
    result = filters.check_filters(market, events=[], vix=18)
    assert result["compliant"] is True


def main():
    try:
        test_high_vix_blocks_trade()
        print("[PASS] High VIX blocked trade")
    except AssertionError:
        print("[FAIL] High VIX not blocked")

    try:
        test_normal_conditions_allow_trade()
        print("[PASS] Normal conditions allowed trade")
    except AssertionError:
        print("[FAIL] Normal conditions incorrectly blocked")


if __name__ == "__main__":
    main()
