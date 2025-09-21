# tt_quotes_patch.py
"""
Safe monkey-patch that adds TastytradeClient.get_quotes(symbols)
without modifying your existing tt_client.py.

Usage:
    import tt_quotes_patch  # <-- ensure this is imported once (e.g., in app.py)
    from tt_client import TastytradeClient
    c = TastytradeClient()
    quotes = c.get_quotes(["AAPL","TSLA"])
    # -> {'AAPL': {'last': 210.55, 'bid': 210.5, 'ask': 210.6}, ...}

This uses /market-data/by-type (equity=SYM1,SYM2,...) on your configured API base.
"""

from __future__ import annotations
from typing import Dict, List, Optional
import os
import math
import requests

# import your existing classes
from tt_client import TastytradeClient, TastytradeAuth  # type: ignore


def _num(x) -> Optional[float]:
    """Convert tasty numeric fields (strings, 'NaN', None) to float or None."""
    try:
        if x is None:
            return None
        if isinstance(x, (int, float)):
            # normalize NaN to None
            if isinstance(x, float) and math.isnan(x):
                return None
            return float(x)
        s = str(x).strip()
        if s.lower() == "nan" or s == "":
            return None
        return float(s)
    except Exception:
        return None


def _pick_last(item: dict) -> Optional[float]:
    """
    Prefer 'last', otherwise 'mark', otherwise 'mid', otherwise computed (bid+ask)/2.
    """
    last = _num(item.get("last"))
    if last is not None:
        return last
    mark = _num(item.get("mark"))
    if mark is not None:
        return mark
    mid = _num(item.get("mid"))
    if mid is not None:
        return mid
    bid = _num(item.get("bid") or item.get("bidPrice"))
    ask = _num(item.get("ask") or item.get("askPrice"))
    if bid is not None and ask is not None:
        return (bid + ask) / 2.0
    return bid or ask  # may be None


def _tt_get_quotes(self: TastytradeClient, symbols: List[str]) -> Dict[str, Dict[str, Optional[float]]]:
    """
    Return quotes for the given equity symbols via /market-data/by-type.

    Output:
      {
        "AAPL": {"last": 210.55, "bid": 210.5, "ask": 210.6},
        "TSLA": {"last": 289.44, "bid": 289.44, "ask": 289.49},
        ...
      }

    Notes:
      • Values can be None (e.g., off-hours).
      • Unknown symbols will still appear with None values.
    """
    out: Dict[str, Dict[str, Optional[float]]] = {}
    if not symbols:
        return out

    # Determine base URL exactly how your client does.
    base = getattr(self, "API_BASE", None) or os.environ.get("TASTYTRADE_API_BASE") or "https://api.cert.tastytrade.com"
    url = f"{base}/market-data/by-type"

    # Auth from your existing helper
    auth = getattr(self, "auth", None) or TastytradeAuth()
    token = auth.access_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Tasty handles a CSV list; we’ll chunk just in case (kept small by default)
    syms = [s.strip().upper() for s in symbols if s and str(s).strip()]
    if not syms:
        return out

    CHUNK = 50  # safe chunk size
    for i in range(0, len(syms), CHUNK):
        chunk = syms[i : i + CHUNK]
        params = {"equity": ",".join(chunk)}
        try:
            r = requests.get(url, headers=headers, params=params, timeout=20)
            r.raise_for_status()
            j = r.json() or {}
            items = j.get("data", {}).get("items", [])
            seen = set()
            for it in items:
                sym = (it.get("symbol") or "").upper()
                if not sym:
                    continue
                last = _pick_last(it)
                bid = _num(it.get("bid") or it.get("bidPrice"))
                ask = _num(it.get("ask") or it.get("askPrice"))
                out[sym] = {"last": last, "bid": bid, "ask": ask}
                seen.add(sym)
            # ensure we return keys for everything we asked, even if missing
            for s in chunk:
                if s not in seen and s not in out:
                    out[s] = {"last": None, "bid": None, "ask": None}
        except Exception as e:
            # If the whole chunk fails, still surface keys with None
            for s in chunk:
                if s not in out:
                    out[s] = {"last": None, "bid": None, "ask": None}
            # Optionally, stash error on the instance for debugging
            try:
                setattr(self, "_last_quotes_error", repr(e))
            except Exception:
                pass

    return out


# Attach only if missing; don’t clobber a future built-in
if not hasattr(TastytradeClient, "get_quotes"):
    TastytradeClient.get_quotes = _tt_get_quotes  # type: ignore[attr-defined]
