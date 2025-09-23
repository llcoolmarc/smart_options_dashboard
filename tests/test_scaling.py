import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils import scaling


def test_scaling_blocks_oversized_trade():
    portfolio = {"positions": [{"symbol": "AAPL", "strategy": "vertical", "max_loss": 500}]}
    result = scaling.check_scaling(portfolio, account_size=10000)
    assert result["compliant"] is False


def test_scaling_allows_valid_trade():
    portfolio = {"positions": [{"symbol": "MSFT", "strategy": "vertical", "max_loss": 100}]}
    result = scaling.check_scaling(portfolio, account_size=10000)
    assert result["compliant"] is True


def main():
    try:
        test_scaling_blocks_oversized_trade()
        print("[PASS] Scaling blocked oversized trade")
    except AssertionError:
        print("[FAIL] Scaling did not block oversized trade")

    try:
        test_scaling_allows_valid_trade()
        print("[PASS] Scaling allowed valid trade")
    except AssertionError:
        print("[FAIL] Scaling rejected valid trade")


if __name__ == "__main__":
    main()
