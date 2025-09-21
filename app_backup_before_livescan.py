# app.py
from dotenv import load_dotenv
load_dotenv()
"""
Smart Options Assistant – v6h4-L10 (v6i)
– Performance Summary narrative box
– Pacing bar with axis titles & 100% goal line
– Tooltips on performance summary items
– UI labels + Legend & Terms panel
– IV Rank diagnostics panel + IVR alerts
– Live scan swap + Paper Fill Engine v1
– Paper Close Engine v1 (auto target/early-lock/partial)
– Runtime controls for Paper Close Engine + Auto Actions Log
– Toast moved under drilldown (left column) + smart colors
"""

import os, json, time, uuid, random, datetime, traceback, math
from typing import Dict, Any, Iterable, Optional

from tt_client import TastytradeAuth, TastytradeClient
ACCOUNT_NUMBER = os.getenv("TASTYTRADE_ACCOUNT_NUMBER")

# — Initialize Tastytrade API Client —
auth = TastytradeAuth()
tt   = TastytradeClient(auth)

# — Simulation vs Live Toggle —
USE_LIVE = os.getenv("USE_LIVE", "false").lower() == "true"
# Defaults (can be overridden at runtime via UI Controls)
IVR_ALERT_THRESHOLD = int(os.getenv("IVR_ALERT_THRESHOLD", "50"))
PAPER_SLIPPAGE      = float(os.getenv("PAPER_SLIPPAGE", "0.02"))  # mid − 0.02
PAPER_AUTOCLOSE     = os.getenv("PAPER_AUTOCLOSE", "true").lower() == "true"
PAPER_PARTIAL_AT    = float(os.getenv("PAPER_PARTIAL_AT", "50"))
PAPER_EARLYLOCK_DIFF= float(os.getenv("PAPER_EARLYLOCK_DIFF", "5"))
ALWAYS_DRY_RUN = os.getenv("ALWAYS_DRY_RUN", "false").lower() == "true"


def get_underlying_price(symbol: str) -> float:
    """
    Returns latest price for `symbol`.
    SIM mode → simulate_symbol_basics()
    LIVE mode → REST /market/quotes
    """
    if USE_LIVE:
        try:
            resp = tt.get("/market/quotes", params={"symbols": symbol})
            q = None
            if isinstance(resp, dict):
                if "quotes" in resp and isinstance(resp["quotes"], dict):
                    q = resp["quotes"].get("quote")
                if q is None and "data" in resp and isinstance(resp["data"], list) and resp["data"]:
                    q = resp["data"][0]
            if isinstance(q, list) and q:
                q = q[0]
            price = (q.get("last") or q.get("mark") or q.get("close") or q.get("price"))
            return round(float(price), 2)
        except Exception:
            pass
        b = simulate_symbol_basics({"symbol": symbol})
        return b["price"]
    else:
        b = simulate_symbol_basics({"symbol": symbol})
        return b["price"]

def fetch_iv_rank(symbol: str) -> Optional[float]:
    """Return IV Rank (0–100) from Market Metrics if available (often None in Sandbox)."""
    if not USE_LIVE:
        return None
    try:
        resp = tt.get("/market-metrics", params={"symbol[]": symbol})
        data = resp.get("data", resp)
        row = None
        if isinstance(data, list) and data:
            row = data[0]
        elif isinstance(data, dict):
            items = data.get("items") or data.get("data")
            if isinstance(items, list) and items:
                row = items[0]
            else:
                row = data
        ivr = None
        if isinstance(row, dict):
            for k in ("iv_rank", "ivr", "implied_volatility_rank", "implied-volatility-rank"):
                if row.get(k) is not None:
                    ivr = float(row[k]); break
        return ivr
    except Exception:
        return None

# ---- LIVE chain helpers ----
def _days_until(date_str: str) -> Optional[int]:
    try:
        y,m,d = [int(x) for x in date_str.split("-")]
        dt = datetime.date(y,m,d)
        return (dt - datetime.date.today()).days
    except Exception:
        return None

def _as_float(d: dict, *keys, default=None) -> Optional[float]:
    for k in keys:
        if k in d and d[k] is not None:
            try: return float(d[k])
            except Exception: pass
    return default

def _option_type(d: dict) -> Optional[str]:
    for k in ("option_type","put_call","putCall","call_or_put","option-type"):
        v = d.get(k)
        if isinstance(v, str):
            v = v.lower()
            if v in ("put","call"): return v
            if v in ("p","c"): return "put" if v=="p" else "call"
    return None

def _iter_options(nested: Any) -> Iterable[dict]:
    """Yield option dicts from nested chain structures."""
    if isinstance(nested, dict):
        if any(k in nested for k in ("strike","strike_price","strike-price")) and _option_type(nested) in ("put","call"):
            yield nested
        for v in nested.values():
            yield from _iter_options(v)
    elif isinstance(nested, list):
        for v in nested:
            yield from _iter_options(v)

def _best_put_from_chain(nested_chain: Any, dte_min: int, dte_max: int, delta_min: float, delta_max: float):
    """Pick a short put near target delta and inside DTE window."""
    best = None
    best_score = 1e9
    for row in _iter_options(nested_chain):
        if _option_type(row) != "put": continue

        # DTE
        dte = row.get("dte")
        if dte is None:
            exp = (row.get("expiration") or row.get("expiration_date") or row.get("expiration-date"))
            if isinstance(exp, str):
                dte = _days_until(exp)
        if dte is None or not isinstance(dte, (int,float)): continue
        dte = int(dte)
        if dte < dte_min or dte > dte_max: continue

        # |Delta|
        delta = _as_float(row, "delta","theoretical_delta","option_delta")
        if delta is None: continue
        ad = abs(delta)
        if not (delta_min <= ad <= delta_max): continue

        # Pricing
        bid = _as_float(row, "bid","bid_price","bidPrice")
        ask = _as_float(row, "ask","ask_price","askPrice")
        mid = None
        if bid is not None and ask is not None:
            mid = round((bid + ask)/2.0, 2)
        else:
            mid = _as_float(row, "mark","last","theoretical_price","mark_price")
        strike = _as_float(row, "strike","strike_price","strike-price")
        if strike is None or mid is None: continue
        expiration = row.get("expiration") or row.get("expiration_date") or row.get("expiration-date")

        # Option symbol (if present in this nested shape)
        symbol = row.get("put") or row.get("symbol") or None

        # Score: delta closeness + DTE center bias
        target_delta = (delta_min + delta_max)/2.0
        target_dte   = (dte_min + dte_max)//2
        score = (abs(ad - target_delta)*100.0) + (abs(dte - target_dte)*0.5)
        if score < best_score:
            best_score = score
            best = {
                "strike": round(float(strike),2),
                "dte": int(dte),
                "delta": float(delta),
                "bid": bid, "ask": ask, "mid": mid,
                "expiration": expiration,
                "symbol": symbol
            }
    return best

def _fetch_chain(symbol: str):
    try:
        if hasattr(tt, "get_option_chain_nested"):
            return tt.get_option_chain_nested(symbol)
    except Exception:
        pass
    try:
        return tt.get("/option-chains", params={"symbol": symbol, "include_greeks": "true"})
    except Exception:
        return None

def _conservative_sell_fill(bid: Optional[float], ask: Optional[float], mid: Optional[float]) -> Optional[float]:
    """Conservative credit for SELL: mid − small cushion, clipped to [bid, ask]."""
    if mid is None and (bid is not None and ask is not None):
        mid = (bid + ask) / 2.0
    if mid is None:
        return round(bid, 2) if bid is not None else None
    px = mid - PAPER_SLIPPAGE
    if ask is not None: px = min(px, ask)
    if bid is not None: px = max(px, bid)
    return round(px, 2)

# ---- Live scan builder ----
def build_live_candidate(symbol: str) -> Optional[dict]:
    try:
        uprice = get_underlying_price(symbol)
        if not uprice or uprice <= 0: return None
        chain = _fetch_chain(symbol)
        if not chain: return None

        dmin, dmax = CONFIG["income"]["delta_range"]
        tmin, tmax = CONFIG["income"]["dte_range"]
        pick = _best_put_from_chain(chain, int(tmin), int(tmax), float(dmin), float(dmax))
        if not pick: return None

        credit = _conservative_sell_fill(pick["bid"], pick["ask"], pick["mid"])
        if credit is None or credit <= 0: return None

        ivr = fetch_iv_rank(symbol)
        ivr = ivr if ivr is not None else 50.0

        return {
            "id": str(uuid.uuid4()),
            "strategy_type": "income",
            "symbol": symbol,
            "price": round(float(uprice),2),
            "strike": pick["strike"],
            "dte": int(pick["dte"]),
            "delta": abs(float(pick["delta"])),
            "iv_rank": round(float(ivr)),
            "credit": float(credit),
            # NEW: carry-through for order routing
            "expiration": pick.get("expiration"),
            "option_symbol": pick.get("symbol"),
            "_debug": {"bid": pick["bid"], "ask": pick["ask"], "mid": pick["mid"], "exp": pick.get("expiration")}
        }
    except Exception:
        return None

# ---------------------------------------------------------------

import dash
from dash import Dash, html, dcc, Input, Output, State, dash_table
import plotly.graph_objects as go

APP_VERSION = "v6h4-L10"

# --- Configuration ---
POLL_INTERVAL_MS = 6000
PRICE_MOVE_SD_PCT = 0.0035
EXIT_CFG = {
    "goal_buffer_pct": 0,
    "early_lock_min_cap": 40,
    "early_lock_time_used_max": 0.50,
    "roll_dte_max": 5,
    "roll_min_capture": 55,
    "urgent_dte_max": 2,
    "urgent_capture_under": 70
}
CONFIG = {
    "starting_balance": 5000.0,
    "income":    {"delta_range": (0.20,0.30), "dte_range": (7,14)},
    "targets":   {"profit_capture_base": 55},
    "lists":     {"default_watchlist":["AAPL","TSLA","MSFT","NVDA","SPY","QQQ"]},
    "limits":    {"scan_history": 50, "action_queue_max": 60},
    "capture_efficiency": {"cap":2.0},
    "daily_profit_goal_default": 100
}
STATE_PATH = "data/state.json"
BACKUP_DIR  = "data/backups"

# --- Runtime state ---
runtime_state: Dict[str, Any] = {}

# --- Persistence helpers ---
def ensure_dirs():
    os.makedirs("data", exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)

def save_state():
    ensure_dirs()
    s = runtime_state.copy()
    if isinstance(s.get("used_tips"), set):
        s["used_tips"] = list(s["used_tips"])
    with open(STATE_PATH, "w") as f:
        json.dump(s, f, default=list)

def load_state():
    ensure_dirs()
    default = {
        "trades": [], "scan_history": [], "performance": [],
        "action_queue": [], "sim_day": 0, "tick_counter": 0,
        "risk_cache": {}, "used_tips": set(), "eff_history": [],
        "last_ivr": {}
    }

    # If file missing or empty → start fresh
    if not os.path.exists(STATE_PATH) or os.path.getsize(STATE_PATH) == 0:
        runtime_state.update(default)
        save_state()
        return

    # Try to read JSON; if corrupted, back it up and reset safely
    try:
        with open(STATE_PATH, "r") as f:
            d = json.load(f)
    except Exception:
        try:
            ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            bad = os.path.join(BACKUP_DIR, f"state_corrupt_{ts}.json")
            os.makedirs(BACKUP_DIR, exist_ok=True)
            try:
                os.replace(STATE_PATH, bad)
            except Exception:
                pass
        finally:
            runtime_state.update(default)
            save_state()
            return

    d["used_tips"] = set(d.get("used_tips", []))
    runtime_state.update(default)
    runtime_state.update(d)

load_state()

# --- Ensure defaults (watchlist, goal) ---
def ensure_default_settings():
    runtime_state.setdefault("settings", {})
    s = runtime_state["settings"]
    s.setdefault("watchlist", CONFIG["lists"]["default_watchlist"])
    s.setdefault("daily_profit_goal", CONFIG["daily_profit_goal_default"])
    save_state()
ensure_default_settings()

# --- Broker connectivity (Sandbox/Live) ---
def broker_whoami():
    try:
        auth2 = TastytradeAuth(); tt2 = TastytradeClient(auth2)
        try:
            who = tt2.get("/customers/me", timeout=12)
            if who: pass
        except Exception as e_who:
            e1 = str(e_who)
        else:
            e1 = None
        try:
            data = tt2.get("/customers/me/accounts", timeout=12)
            items = data.get("data", {}).get("items", [])
            return {"ok": True, "count": len(items)}
        except Exception as e_acc:
            if e1 is None: return {"ok": True, "count": 0}
            return {"ok": False, "error": f"id: {e1} | accounts: {e_acc}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# --- Send-to-Broker helpers ---
def send_equity_test_order(symbol: str, qty: int = 1, price: float = 1.00) -> str:
    try:
        acct = os.getenv("TASTYTRADE_ACCOUNT_NUMBER")
        if not acct: return "Broker error: TASTYTRADE_ACCOUNT_NUMBER is missing in .env"
        auth2 = TastytradeAuth(); tt2 = TastytradeClient(auth2)
        _ = tt2.place_equity_order(
            account_number=acct, symbol=symbol, quantity=int(qty),
            action="Buy to Open", order_type="Limit", price=float(price), time_in_force="Day", timeout=15,
            source=f"smart-options-assistant/{APP_VERSION}"
        )
        return f"Sent LIMIT $1 Buy 1 {symbol} (Sandbox). Check Orders."
    except Exception as e:
        return f"Broker error: {e}"

def send_short_put_order(trade: Dict[str, Any], quantity: int = 1, limit_price: float = None, dry_run: bool = None) -> str:
    """
    If we have an option symbol on the trade, submit a short put LIMIT order.
    - Sandbox: dry_run defaults True.
    - Live:    dry_run defaults False unless ALWAYS_DRY_RUN=true.
    Falls back to equity $1 test order if we lack option details.
    """
    try:
        acct = os.getenv("TASTYTRADE_ACCOUNT_NUMBER")
        if not acct:
            return "Broker error: TASTYTRADE_ACCOUNT_NUMBER is missing in .env"

        # Decide dry_run default safely
        if dry_run is None:
            dry_run = ALWAYS_DRY_RUN or (not USE_LIVE)

        opt_sym = trade.get("option_symbol")
        expiration = trade.get("expiration")
        strike = trade.get("strike")
        underlying = trade.get("symbol")

        # Choose a reasonable default limit price
        if limit_price is None:
            limit_price = float(trade.get("current_option_mark") or trade.get("initial_credit") or 0.50)

        auth2 = TastytradeAuth()
        client = TastytradeClient(auth2)

        # Resolve symbol if needed and we have enough info
        if not opt_sym and (underlying and expiration and strike):
            try:
                opt_sym = client.find_equity_option_symbol(underlying, expiration, float(strike), right="put")
            except Exception:
                # Fallback to super-safe $1 equity test order
                return send_equity_test_order(underlying, qty=1, price=1.00)

        # If we still don't have an option symbol, use equity test fallback
        if not opt_sym:
            return send_equity_test_order(underlying, qty=1, price=1.00)

        # Submit short put LIMIT (Credit)
        _ = client.place_equity_option_order(
            account_number=acct,
            option_symbol=opt_sym,
            quantity=int(quantity),
            limit_price=float(limit_price),
            time_in_force="Day",
            dry_run=bool(dry_run),
            source=f"smart-options-assistant/{APP_VERSION}"
        )

        if dry_run:
            return f"Order DRY-RUN: STO 1 {opt_sym} @ {limit_price:.2f} — validated (Sandbox/Paper)"
        return f"Sent STO 1 {opt_sym} @ {limit_price:.2f} (Paper/Live). Check Orders."
    except Exception as e:
        return f"Broker error: {e}"

def enqueue_toast(msg, level="info"):
    runtime_state["action_queue"].append({"epoch": time.time(), "type":"toast", "level":level, "msg":msg})
    runtime_state["action_queue"] = runtime_state["action_queue"][-CONFIG["limits"]["action_queue_max"]:]

# --- Metrics & normalization ---
def adaptive_target(iv, dte, base):
    tgt = base
    if iv>=70: tgt -=5
    elif iv<40: tgt +=5
    if dte<=5: tgt -=5
    elif dte>12: tgt +=2
    return max(35, min(75, tgt))

def compute_capture_eff(t):
    if t["strategy_type"]!="income":
        t["capture_efficiency"] = None; return
    init = t.get("initial_dte",t.get("dte",0))
    if not init:
        t["capture_efficiency"]=None; return
    used = (init - t["dte"])/init
    if used<=0:
        t["capture_efficiency"]=None; return
    eff = (t["prem_captured_pct"]/100)/used
    t["capture_efficiency"] = round(min(eff,CONFIG["capture_efficiency"]["cap"]),2)

def classify_exit_state(t):
    if t["strategy_type"]!="income" or t.get("closed"):
        t["exit_state"] = None; return
    cap,goal,dte = t["prem_captured_pct"],t["target_capture_pct"],t["dte"]
    init = max(1,t["initial_dte"]); used = (init-dte)/init
    if cap>=goal:
        st="Goal"
    elif cap>=EXIT_CFG["early_lock_min_cap"] and used<=EXIT_CFG["early_lock_time_used_max"]:
        st="EarlyLock"
    elif dte<=EXIT_CFG["urgent_dte_max"] and cap<EXIT_CFG["urgent_capture_under"]:
        st="Urgent"
    elif dte<=EXIT_CFG["roll_dte_max"] and cap>=EXIT_CFG["roll_min_capture"]:
        st="RollWindow"
    else:
        st="Monitor"
    t["exit_state"] = st

def normalize_trades():
    for t in runtime_state["trades"]:
        t.setdefault("strategy_type","income")
        t.setdefault("strike",0); t.setdefault("dte",0)
        t.setdefault("initial_dte",t["dte"])
        t.setdefault("delta",0.0); t.setdefault("iv_rank",50)
        t.setdefault("initial_credit", t.get("credit",0.0))
        t.setdefault("current_option_mark", t["initial_credit"])
        t.setdefault("prem_captured_pct",0.0)
        t.setdefault("time_used_pct",0.0)
        t.setdefault("unrealized_pnl",0.0); t.setdefault("realized_pnl",0.0)
        t.setdefault("partial_closed", False)
        if t["strategy_type"]=="income":
            t.setdefault("target_capture_pct",
                adaptive_target(t["iv_rank"],t["dte"],CONFIG["targets"]["profit_capture_base"]))
        compute_capture_eff(t); classify_exit_state(t)
    save_state()
normalize_trades()

# --- Simulation & risk snapshot ---
def compute_risk_snapshot():
    open_trades=[x for x in runtime_state["trades"] if not x.get("closed")]
    coll = sum(x["strike"]*100 for x in open_trades if x["strategy_type"]=="income")
    symc={}; near=0
    for t in open_trades:
        symc[t["symbol"]] = symc.get(t["symbol"],0)+1
        if t["dte"]<=2: near+=1
    tot=CONFIG["starting_balance"]
    runtime_state["risk_cache"] = {
        "collateral_pct": coll/tot if tot else 0,
        "max_symbol_fraction": max(symc.values())/len(open_trades) if open_trades else 0,
        "near_expiry": near, "open_trades": len(open_trades)
    }

def simulate_tick():
    try:
        runtime_state["tick_counter"] += 1
        for t in runtime_state["trades"]:
            if t.get("closed"): continue
            u = get_underlying_price(t["symbol"])
            u += random.gauss(0, PRICE_MOVE_SD_PCT)*u
            t["underlying_mark"] = round(max(1,u),2)

            if t["strategy_type"]=="income":
                # Gentle time decay per heartbeat so Time% and Cap% move in sim mode
                dte_decay = 0.2
                t["dte"] = max(0.0, round(float(t["dte"]) - dte_decay, 2))

                init, dte = t["initial_credit"], t["dte"]
                init_dte = max(1,t["initial_dte"])
                used = (init_dte - dte)/init_dte
                t["time_used_pct"] = round(max(0.0, min(1.0, used))*100, 1)

                theo = init * ((1 - t["target_capture_pct"]/100 * used)**1.05)
                newm = 0.6*t["current_option_mark"] + 0.4*max(0.05,theo*(1 - t["delta"]*0.05))
                t["current_option_mark"] = round(newm,2)

                cap = init - newm
                t["prem_captured_pct"] = round(max(0.0, cap/init*100), 2)
                t["unrealized_pnl"]   = round(cap*100,2)

        compute_risk_snapshot()
        save_state()
    except Exception:
        traceback.print_exc()

# --- Paper Close Engine v1 ---
def enforce_paper_exits(settings: Optional[dict]):
    if not settings: return
    if not settings.get("paper_autoclose", True): return
    partial_at = float(settings.get("partial_at", PAPER_PARTIAL_AT))
    earlylock  = float(settings.get("earlylock_diff", PAPER_EARLYLOCK_DIFF))

    for t in list(runtime_state["trades"]):
        if t.get("closed") or t.get("strategy_type")!="income":
            continue
        cap = float(t.get("prem_captured_pct", 0.0))
        tu  = float(t.get("time_used_pct", 0.0))
        tgt = float(t.get("target_capture_pct", CONFIG["targets"]["profit_capture_base"]))

        # 1) Full close at target
        if cap >= tgt:
            close_trade(t["id"], full=True)
            enqueue_toast(f"Auto-closed (target): {t['symbol']} at {cap:.0f}% (target {tgt:.0f}%)")
            continue

        # 2) Early-lock
        if (cap - tu) >= earlylock:
            close_trade(t["id"], full=True)
            enqueue_toast(f"Auto-closed (early-lock): {t['symbol']} — Cap {cap:.0f}% vs Time {tu:.0f}%")
            continue

        # 3) First time partial
        if (not t.get("partial_closed")) and cap >= partial_at:
            close_trade(t["id"], full=False)
            for tt_ in runtime_state["trades"]:
                if tt_["id"] == t["id"]:
                    tt_["partial_closed"] = True
                    break
            save_state()
            enqueue_toast(f"Auto partial: {t['symbol']} at {cap:.0f}% (took half)")

# --- Performance & pacing snapshots ---
def performance_snapshot():
    trades = runtime_state["trades"]
    open_inc = [t for t in trades if t["strategy_type"]=="income" and not t.get("closed")]
    all_inc  = [t for t in trades if t["strategy_type"]=="income"]
    tot_real = sum(t["realized_pnl"] for t in trades)
    today    = datetime.datetime.now().strftime("%Y-%m-%d")
    real_today = sum(t["realized_pnl"] for t in trades if t.get("closed_time","").startswith(today))
    equity   = CONFIG["starting_balance"] + tot_real + sum(t["unrealized_pnl"] for t in open_inc)
    cap_val  = sum((t["prem_captured_pct"]/100)*t["initial_credit"] for t in all_inc)
    sold     = sum(t["initial_credit"] for t in all_inc)
    cap_pct  = (cap_val/sold*100) if sold else 0
    avg_c    = sum(t["prem_captured_pct"] for t in open_inc)/len(open_inc) if open_inc else 0
    avg_t    = sum(t["time_used_pct"] for t in open_inc)/len(open_inc) if open_inc else 0
    return {
        "equity": equity,
        "equity_pct": (equity/CONFIG["starting_balance"]-1)*100,
        "realized_today": real_today,
        "cap_pct": cap_pct,
        "avg_cap": avg_c,
        "avg_time": avg_t,
        "eff_history": runtime_state["eff_history"]
    }

def pacing_status(cap, use, tol=5):
    diff = cap - use
    if diff>tol:   return "Ahead"
    if diff<-tol:  return "Behind"
    return "On Pace"

# --- Scanner & trade helpers ---
def simulate_symbol_basics(sym):
    return {"symbol":sym["symbol"] if isinstance(sym, dict) else sym,
            "price":round(random.uniform(40,300),2),
            "iv_rank":random.randint(30,80)}

def make_income_candidate(b):
    delta=random.uniform(*CONFIG["income"]["delta_range"])
    dte  =random.randint(*CONFIG["income"]["dte_range"])
    strike=round(b["price"]*(1 - delta*0.1),2)
    credit=round(random.uniform(0.8,2.5),2)
    return {"id":str(uuid.uuid4()),"strategy_type":"income","symbol":b["symbol"],
            "price":b["price"],"strike":strike,"dte":dte,"delta":delta,"iv_rank":b["iv_rank"],"credit":credit}

def generate_scan_live():
    watch = runtime_state.get("settings", {}).get("watchlist", CONFIG["lists"]["default_watchlist"])
    basics=[]
    for s in watch:
        cand = build_live_candidate(s)
        if cand: basics.append(cand)
    runtime_state["scan_history"].append({"time": datetime.datetime.now().strftime("%H:%M:%S"), "count": len(basics)})
    runtime_state["scan_history"] = runtime_state["scan_history"][-CONFIG["limits"]["scan_history"]:]
    save_state(); return basics

def generate_scan():
    """USE_LIVE → chain-based; else simulation (with graceful fallback)."""
    if USE_LIVE:
        print("[SCAN] Live mode: building candidates from option chains")
        cands = generate_scan_live()
        if not cands:
            print("[SCAN] Live chain unavailable; fallback to simulated candidates")
            watch = runtime_state.get("settings", {}).get("watchlist", CONFIG["lists"]["default_watchlist"])
            basics = []
            for s in watch:
                price = get_underlying_price(s)
                basics.append({"symbol":s, "price":price, "iv_rank":round(fetch_iv_rank(s) or 50)})
            cands = [make_income_candidate(b) for b in basics]
        return cands
    else:
        watch = runtime_state.get("settings", {}).get("watchlist", CONFIG["lists"]["default_watchlist"])
        print(f"[SCAN] Simulation mode. Watchlist: {watch}")
        basics = [simulate_symbol_basics({"symbol":s}) for s in watch]
        inc = [make_income_candidate(b) for b in basics]
        runtime_state["scan_history"].append({"time": datetime.datetime.now().strftime("%H:%M:%S"), "count": len(inc)})
        runtime_state["scan_history"] = runtime_state["scan_history"][-CONFIG["limits"]["scan_history"]:]
        save_state(); return inc

def add_trade_from_candidate(c):
    if c["strategy_type"] != "income":
        return
    tgt = adaptive_target(c["iv_rank"], c["dte"], CONFIG["targets"]["profit_capture_base"])
    t = {
        "id": c["id"],
        "opened": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "symbol": c["symbol"],
        "strategy_type": "income",
        "strike": c["strike"],
        "dte": c["dte"],
        "initial_dte": c["dte"],
        "delta": c["delta"],
        "iv_rank": c["iv_rank"],
        "initial_credit": c["credit"],
        "current_option_mark": c["credit"],
        "prem_captured_pct": 0.0,
        "unrealized_pnl": 0.0,
        "realized_pnl": 0.0,
        "target_capture_pct": tgt,
        "why_summary": f"Short put. Goal {tgt}%. Δ{c['delta']:.2f}.",
        "closed": False,
        # NEW: carry-through if live scan provided them
        "expiration": c.get("expiration"),
        "option_symbol": c.get("option_symbol")
    }
    runtime_state["trades"].append(t)
    normalize_trades()

def close_trade(trade_id, full=True):
    for t in runtime_state["trades"]:
        if t["id"]==trade_id and not t.get("closed"):
            if full:
                t["realized_pnl"] += t["unrealized_pnl"]; t["unrealized_pnl"] = 0
                t["closed"] = True; t["closed_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                enqueue_toast(f"Closed {t['symbol']}")
            else:
                half = t["unrealized_pnl"]/2
                t["realized_pnl"] += half; t["unrealized_pnl"] -= half
                enqueue_toast(f"Partially closed {t['symbol']}")
            break
    normalize_trades()

# --- Dash app & layout ---
app = Dash(__name__)
server = app.server
app.title = "Smart Options Assistant"

trade_columns = [
    {"id":"prem_captured_pct","name":""},
    {"id":"time_used_pct","name":""},
    {"id":"opened","name":"Opened"},
    {"id":"symbol","name":"Symbol"},
    {"id":"strategy_type","name":"Type"},
    {"id":"strike","name":"Strike"},
    {"id":"dte","name":"DTE"},
    {"id":"capture_progress","name":"Progress"},
    {"id":"unrealized_pnl","name":"Unreal$"},
    {"id":"exit_state","name":"Exit"},
    {"id":"why_summary","name":"Why"},
    {"id":"close_half","name":"Close 1/2"},
    {"id":"close_all","name":"Close All"},
    {"id":"send_broker","name":"Send to Broker"}
]

app.layout = html.Div([
    dcc.Store(id="toast-store"),
    dcc.Store(id="candidates-store"),
    dcc.Store(id="runtime-settings", data={
        "paper_autoclose": PAPER_AUTOCLOSE,
        "partial_at": PAPER_PARTIAL_AT,
        "earlylock_diff": PAPER_EARLYLOCK_DIFF,
        "ivr_threshold": IVR_ALERT_THRESHOLD
    }),

    dcc.Interval(id="poll-interval", interval=POLL_INTERVAL_MS, n_intervals=0),
    dcc.Interval(id="broker-ping", interval=60_000, n_intervals=0),
    dcc.Interval(id="ivr-ping", interval=45_000, n_intervals=0),
    dcc.Download(id="actions-download"),

    # Top controls (IVR diag pinned to the right)
    html.Div([
        html.H3(f"Smart Options Assistant ({APP_VERSION})", style={"margin":"0"}),
        html.Button("Scan Market", id="scan-btn", style={"marginLeft":"12px"}),
        html.Span(" Mode: Simulation", style={"marginLeft":"20px","fontSize":"12px"}) if not USE_LIVE else
        html.Span(" Mode: Live (Paper)", style={"marginLeft":"20px","fontSize":"12px"}),
        html.Span(id="broker-status", style={"marginLeft":"16px","fontSize":"12px"}),
        html.Span(id="scan-status", style={
            "marginLeft":"12px","fontSize":"12px","padding":"2px 6px",
            "border":"1px solid #ddd","borderRadius":"4px","background":"#fafafa"
        }),
        html.Div(id="diag-panel", style={
            "marginLeft":"auto","fontSize":"12px","padding":"6px 8px",
            "background":"#f5f5f5","border":"1px solid #e5e5e5",
            "borderRadius":"4px","display":"inline-block","maxWidth":"360px"
        })
    ], style={"display":"flex","alignItems":"center","gap":"8px","marginBottom":"8px"}),

    # Main columns (no wrap: keep right column on the right)
    html.Div(style={"display":"flex","flexWrap":"nowrap","alignItems":"flex-start"}, children=[

        # LEFT: Open Trades + Drilldown + Toast
        html.Div(style={"flex":"1 1 60%","minWidth":"520px"}, children=[
            html.Div("Open Trades", style={"fontWeight":"bold","margin":"4px 0 6px 0","fontSize":"13px"}),
            dash_table.DataTable(
                id="trade-table",
                columns=trade_columns,
                data=[],
                hidden_columns=["prem_captured_pct","time_used_pct"],
                page_size=20,
                style_cell={"fontSize":"11px","whiteSpace":"normal","height":"auto","padding":"4px"},
                style_header={"background":"#eee","fontWeight":"bold"},
                style_data_conditional=[
                    {"if":{"column_id":"exit_state","filter_query":"{exit_state}='Goal'"},
                     "backgroundColor":"#d4edda","color":"#155724"},
                    {"if":{"column_id":"exit_state","filter_query":"{exit_state}='EarlyLock'"},
                     "backgroundColor":"#d1ecf1","color":"#0c5460"},
                    {"if":{"column_id":"exit_state","filter_query":"{exit_state}='RollWindow'"},
                     "backgroundColor":"#fff3cd","color":"#856404"},
                    {"if":{"column_id":"exit_state","filter_query":"{exit_state}='Urgent'"},
                     "backgroundColor":"#f8d7da","color":"#721c24"},
                    {"if":{"filter_query":"{exit_state}='Urgent'"},
                     "backgroundColor":"#f8d7da"}
                ]
            ),
            html.Pre(id="drilldown", style={
                "fontSize":"11px","background":"#f9f9f9","padding":"6px",
                "minHeight":"90px","marginTop":"4px"
            }),
            # Toast moved here under drilldown
            html.Div(id="toast", style={
                "fontWeight":"bold","minHeight":"20px","marginTop":"6px","fontSize":"12px",
                "padding":"6px","border":"1px solid #e5e5e5","borderRadius":"4px","background":"#fafafa"
            })
        ]),

        # RIGHT: all the stacked panels
        html.Div(style={"flex":"1 1 40%","minWidth":"340px","paddingLeft":"10px"}, children=[
            # 0) Automation Controls (runtime)
            html.Div(id="auto-controls", style={
                "background":"#fcfffa","border":"1px solid #d6f0c2",
                "padding":"8px","marginBottom":"8px","fontSize":"12px","borderRadius":"4px"
            }, children=[
                html.Div("Automation Controls", style={"fontWeight":"bold","marginBottom":"6px","fontSize":"13px"}),
                dcc.Checklist(
                    id="auto-toggle",
                    options=[{"label":" Enable Paper Close Engine", "value":"on"}],
                    value=["on"] if PAPER_AUTOCLOSE else [],
                    style={"marginBottom":"6px"}
                ),
                html.Div([
                    html.Span("Partial at %: "),
                    dcc.Input(id="input-partial", type="number", min=30, max=95, step=1, value=int(PAPER_PARTIAL_AT), style={"width":"70px","marginRight":"12px"}),
                    html.Span("Early-lock diff %: "),
                    dcc.Input(id="input-earlylock", type="number", min=1, max=20, step=1, value=int(PAPER_EARLYLOCK_DIFF), style={"width":"70px","marginRight":"12px"}),
                    html.Span("IVR alert ≥ "),
                    dcc.Input(id="input-ivr", type="number", min=0, max=100, step=1, value=int(IVR_ALERT_THRESHOLD), style={"width":"70px","marginRight":"12px"}),
                    html.Button("Apply", id="btn-apply", n_clicks=0, style={"marginLeft":"6px"})
                ], style={"display":"flex","flexWrap":"wrap","alignItems":"center","gap":"6px"})
            ]),
            # 1) Performance Summary
            html.Div(id="perf-summary", style={
                "background":"#e6f7ff","border":"1px solid #b3e0ff",
                "padding":"8px","marginBottom":"8px","fontSize":"12px","borderRadius":"4px"
            }),
            # 2) Health Panel
            html.Div(id="health-panel", style={
                "background":"#f4f8ff","border":"1px solid #cbd7ef",
                "padding":"8px","marginBottom":"8px","fontSize":"12px","borderRadius":"4px"
            }),
            # 3) Pacing Bar
            dcc.Graph(id="pacing-bar", config={"displayModeBar":False}, style={
                "height":"140px","marginBottom":"8px","border":"1px solid #ddd","borderRadius":"4px"
            }),
            # 4) Daily Goal Panel
            html.Div(id="goal-panel", style={
                "background":"#fffbe6","border":"1px solid #f1d19b",
                "padding":"8px","marginBottom":"8px","fontSize":"12px","borderRadius":"4px"
            }),
            # 5) Efficiency Line
            dcc.Graph(id="eff-line", config={"displayModeBar":False}, style={
                "height":"100px","marginBottom":"8px","border":"1px solid #ddd","borderRadius":"4px"
            }),
            # 6) Actions Panel
            html.Div(id="actions-panel", style={
                "background":"#fff7e6","border":"1px solid #f1d19b",
                "padding":"8px","marginBottom":"8px","fontSize":"12px","borderRadius":"4px"
            }),
            # 6b) Auto Actions Log
            html.Div(id="auto-log-panel", style={
                "background":"#f9f9ff","border":"1px solid #dfe4ff",
                "padding":"8px","marginBottom":"8px","fontSize":"12px","borderRadius":"4px"
            }),
            html.Button(
    "Download Actions Log (CSV)",
    id="btn-export",
    n_clicks=0,
    style={"marginBottom":"8px","fontSize":"12px"}
),

            # 7) Guidance Panel
            html.Div(id="guidance-panel", style={
                "background":"#f6fff4","border":"1px solid #bfe3b2",
                "padding":"8px","marginBottom":"8px","fontSize":"12px","borderRadius":"4px"
            }),
            # 8) Equity Sparkline
            dcc.Graph(id="equity-spark", config={"displayModeBar":False}, style={
                "height":"180px","border":"1px solid #ddd","borderRadius":"4px"
            }),
            # --- Legend & Terms ---
            html.Div(id="legend-panel", style={
                "background":"#fbfbfb","border":"1px solid #e5e5e5",
                "padding":"8px","marginTop":"8px","fontSize":"12px","borderRadius":"4px"
            }, children=[
                html.Div("Legend & Panel Guide", style={"fontWeight":"bold","marginBottom":"6px","fontSize":"13px"}),
                html.Ul(style={"paddingLeft":"18px","margin":"0"}, children=[
                    html.Li("Performance Summary: Totals & averages for realized profits and today's progress."),
                    html.Li("Account Health: Equity, realized today, premium captured, open trades, collateral, concentration, near expiries."),
                    html.Li("Pacing: Cap% vs Time% (Cap% ≥ Time% + 5 → ahead)."),
                    html.Li("Daily Goal: Target and remaining amount."),
                    html.Li("Efficiency: Speed-of-capture index (~1.0 = on time)."),
                    html.Li("Actions: Nudges like closing winners near goal; IVR notices."),
                    html.Li("Auto Actions Log: Most recent automatic partial/close events with reasons."),
                    html.Li("Equity Sparkline: Recent equity trend (includes unrealized on open trades)."),
                    html.Li("Key terms — Cap%: % of option credit captured. Time%: % of DTE used. DTE: Days to expiration. IV Rank (IVR): Volatility rank vs last year. Realized P/L: Closed-trade profit. Unrealized P/L: Open-trade P/L."),
                ])
            ])
        ])
    ]),
], style={"fontFamily":"Arial, sans-serif","padding":"10px","maxWidth":"1400px","margin":"0 auto"})

# --- Apply runtime settings ---
@app.callback(
    Output("runtime-settings", "data"),
    Output("toast-store","data", allow_duplicate=True),
    Input("btn-apply", "n_clicks"),
    State("auto-toggle","value"),
    State("input-partial","value"),
    State("input-earlylock","value"),
    State("input-ivr","value"),
    prevent_initial_call=True
)
def apply_settings(n, toggle_val, partial_at, earlylock_diff, ivr_thresh):
    try:
        settings = {
            "paper_autoclose": ("on" in (toggle_val or [])),
            "partial_at": float(partial_at or PAPER_PARTIAL_AT),
            "earlylock_diff": float(earlylock_diff or PAPER_EARLYLOCK_DIFF),
            "ivr_threshold": int(ivr_thresh or IVR_ALERT_THRESHOLD)
        }
        enqueue_toast(f"Automation updated: auto={'on' if settings['paper_autoclose'] else 'off'}, "
                      f"partial≥{int(settings['partial_at'])}%, early-lock+{int(settings['earlylock_diff'])}, "
                      f"IVR≥{settings['ivr_threshold']}", level="success")
        return settings, {"msg": "Settings applied", "level": "success"}
    except Exception as e:
        return dash.no_update, {"msg": f"Settings error: {e}", "level": "error"}

# --- Heartbeat ---
@app.callback(
    Output("toast-store","data", allow_duplicate=True),
    Output("trade-table","data", allow_duplicate=True),
    Output("health-panel","children"),
    Output("perf-summary","children"),
    Output("pacing-bar","figure"),
    Output("goal-panel","children"),
    Output("eff-line","figure"),
    Output("actions-panel","children"),
    Output("auto-log-panel","children"),
    Output("guidance-panel","children"),
    Output("equity-spark","figure"),
    Input("poll-interval","n_intervals"),
    State("runtime-settings","data"),
    prevent_initial_call=True
)
def heartbeat(n, rt_settings):
    try:
        simulate_tick()
        enforce_paper_exits(rt_settings or {})

        snap = performance_snapshot()
        risk = runtime_state["risk_cache"]

        # Table rows
        rows = []
        for t in runtime_state["trades"]:
            if t.get("closed"): continue
            cap, tu = t["prem_captured_pct"], t["time_used_pct"]
            prog = f"{cap:.0f}% | {tu:.0f}%"
            rows.append({
                "opened": t["opened"], "symbol": t["symbol"],
                "strategy_type": t["strategy_type"], "strike": t["strike"],
                "dte": int(max(0, round(t["dte"]))),
                "capture_progress": prog,
                "unrealized_pnl": round(t["unrealized_pnl"], 2),
                "exit_state": t["exit_state"], "why_summary": t["why_summary"],
                "close_half": "½", "close_all": "×", "send_broker": "→",
                "prem_captured_pct": cap, "time_used_pct": tu
            })

        # Latest toast
        toast=None
        for x in reversed(runtime_state["action_queue"]):
            if x["type"]=="toast": toast=x; break
        toast_data={"msg":toast["msg"], "level": toast.get("level","info")} if toast else dash.no_update

        # Health
        hp = [
            html.Div("Account Health", style={"fontWeight":"bold","marginBottom":"4px","fontSize":"13px"}),
            html.Div(f"Equity: ${snap['equity']:.0f} ({snap['equity_pct']:+.1f}%)"),
            html.Div(f"Realized Today: ${snap['realized_today']:.0f}"),
            html.Div(f"Premium Captured: {snap['cap_pct']:.1f}%"),
            html.Div(f"Open Trades: {risk['open_trades']}")
        ]
        cp=risk["collateral_pct"]*100
        hp.append(html.Div([html.Span("Collateral: "),
            html.Span(f"{cp:.1f}%", style={"color":"green" if cp<25 else "#d7a200" if cp<40 else "red"})
        ]))
        mf=risk["max_symbol_fraction"]*100
        hp.append(html.Div([html.Span("Concentration: "),
            html.Span(f"{mf:.1f}%", style={"color":"green" if mf<30 else "#d7a200" if mf<40 else "red"})
        ]))
        hp.append(html.Div(f"Near Expiry (≤2 DTE): {risk['near_expiry']}"))

        # Performance Summary
        tot_real = sum(t["realized_pnl"] for t in runtime_state["trades"])
        pct_tot = (tot_real/CONFIG["starting_balance"])*100
        today = snap["realized_today"]
        closed_dates = {t["closed_time"][:10] for t in runtime_state["trades"] if t.get("closed_time")}
        avg_daily = (tot_real/len(closed_dates)) if closed_dates else today
        ps = [
            html.Div("Performance Summary", style={"fontWeight":"bold","marginBottom":"4px","fontSize":"13px"}),
            html.Div([html.Span(f"Total P/L: ${tot_real:.2f} ({pct_tot:+.2f}%)"),
                      html.Span(" ?", title="Net profit or loss since your starting balance.",
                                style={"cursor":"help","marginLeft":"4px"})]),
            html.Div([html.Span(f"Today's P/L: ${today:.2f}"),
                      html.Span(" ?", title="Profit or loss realized so far today.",
                                style={"cursor":"help","marginLeft":"4px"})]),
            html.Div([html.Span(f"Avg Daily P/L: ${avg_daily:.2f}"),
                      html.Span(" ?", title="Average profit or loss per day (over days you closed trades).",
                                style={"cursor":"help","marginLeft":"4px"})])
        ]

        # Pacing bar
        c_avg, t_avg = snap["avg_cap"], snap["avg_time"]
        stat = pacing_status(c_avg,t_avg)
        bar_fig = go.Figure()
        bar_fig.add_trace(go.Bar(x=["Cap %","Time %"], y=[c_avg,t_avg], marker_color=["#2ca02c","#7f7f7f"], name=""))
        bar_fig.add_shape(type="line", x0=-0.5, x1=1.5, y0=100, y1=100, line=dict(dash="dash", color="#888"))
        bar_fig.update_layout(
            title_text=f"Pacing (Cap% vs Time%): {stat}",
            xaxis_title="Metric", yaxis_title="Percentage",
            margin=dict(l=30,r=10,t=35,b=30), yaxis=dict(range=[0,120], tickfont=dict(size=9)),
            template="plotly_white", height=140
        )

        # Daily goal
        goal = runtime_state.get("settings",{}).get("daily_profit_goal",CONFIG["daily_profit_goal_default"])
        got  = snap["realized_today"]; pctd = (got/goal*100) if goal else 0
        color="green" if pctd>=100 else "#d7a200" if pctd>=50 else "red"
        gp = [
            html.Div("Daily Goal", style={"fontWeight":"bold","marginBottom":"4px","fontSize":"13px"}),
            html.Div(f"Daily Goal: ${goal}", style={"fontWeight":"bold"}),
            html.Div(f"Achieved: ${got:.0f} ({pctd:.0f}%)", style={"color":color})
        ]
        rem = max(0,goal-got); avg_win=25
        gp.append(html.Div(f"Need ${rem:.0f} (~{math.ceil(rem/avg_win)} more)"))

        # Efficiency
        eh = snap["eff_history"]; ev = eh[-1] if eh else 1
        label = "Faster" if ev>1.1 else "Slow" if ev<0.9 else "On Schedule"
        eff_fig = go.Figure(go.Scatter(y=eh, mode="lines+markers", line=dict(width=2)))
        eff_fig.update_layout(
            title_text=f"Efficiency (Capture vs Time): {label} ({ev:.2f})",
            margin=dict(l=30,r=10,t=35,b=25), height=100, yaxis_title="Eff", template="plotly_white"
        )

        # Actions (plus IVR hints)
        ap=[html.Div("Actions", style={"fontWeight":"bold","marginBottom":"4px","fontSize":"13px"})]
        if stat=="Behind":
            for t in runtime_state["trades"]:
                if (t["strategy_type"]=="income" and not t.get("closed")
                    and t["prem_captured_pct"]>=t["target_capture_pct"]-5):
                    ap.append(html.Div("Tip: Close near-goal winners.",style={"color":"red"})); break
        try:
            hot = []
            ivr_thresh = int((rt_settings or {}).get("ivr_threshold", IVR_ALERT_THRESHOLD))
            for sym, rec in (runtime_state.get("last_ivr") or {}).items():
                ivr = (rec or {}).get("ivr")
                if ivr is not None and ivr >= ivr_thresh:
                    hot.append(f"{sym} ({ivr:.0f})")
            if hot:
                ap.append(html.Div(
                    f"IVR Hot: {', '.join(hot[:3])} ≥ {ivr_thresh}. Consider prioritizing premium sells.",
                    style={"color":"#a86500"}
                ))
        except Exception:
            pass
        if len(ap)==1: ap.append(html.Div("No urgent actions."))

        # Auto Actions Log
        logs = [x for x in runtime_state.get("action_queue", []) if x.get("type")=="toast" and str(x.get("msg","")).startswith("Auto")]
        logs = logs[-5:]
        alog = [html.Div("Auto Actions Log (last 5)", style={"fontWeight":"bold","marginBottom":"4px","fontSize":"13px"})]
        if logs:
            for e in logs[::-1]:
                ts = datetime.datetime.fromtimestamp(e["epoch"]).strftime("%H:%M:%S")
                alog.append(html.Div(f"{ts} – {e['msg']}"))
        else:
            alog.append(html.Div("No auto actions yet."))

        # Guidance
        partial_at = int((rt_settings or {}).get("partial_at", PAPER_PARTIAL_AT))
        earlylock  = int((rt_settings or {}).get("earlylock_diff", PAPER_EARLYLOCK_DIFF))
        gpnl=[
            html.Div("Guidance", style={"fontWeight":"bold","marginBottom":"4px","fontSize":"13px"}),
            html.Ul([
                html.Li(f"Paper Close Engine: partial @ {partial_at}%, auto target close, early-lock when Cap% ≥ Time% + {earlylock}."),
                html.Li("If Cap% ≥ Time% + 5 → you’re ahead."),
                html.Li(f"Pacing: {stat} (Cap {c_avg:.0f}% vs Time {t_avg:.0f}%)."),
                html.Li(f"Goal progress: {pctd:.0f}% of daily target.")
            ],style={"paddingLeft":"18px","margin":"4px 0"})
        ]

        # Equity sparkline
        perf=runtime_state["performance"][-20:]
        xs=[p["time"] for p in perf]; ys=[p["value"] for p in perf]
        eq_fig=go.Figure(go.Scatter(x=xs,y=ys,mode="lines+markers",line=dict(width=2),marker=dict(size=4)))
        eq_fig.update_layout(
            title_text="Equity (Sparkline, last 20 points)",
            margin=dict(l=30,r=10,t=30,b=25),height=180,
            xaxis_title="Time", yaxis_title="Equity ($)", template="plotly_white"
        )

        return (toast_data, rows, hp, ps, bar_fig, gp, eff_fig, ap, alog, gpnl, eq_fig)

    except Exception:
        traceback.print_exc()
        return tuple(dash.no_update for _ in range(11))
@app.callback(
    Output("actions-download", "data"),
    Input("btn-export", "n_clicks"),
    prevent_initial_call=True
)
def export_actions_csv(n):
    import io, csv
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["timestamp_iso", "level", "message"])  # header

    rows = sorted(runtime_state.get("action_queue", []), key=lambda x: x.get("epoch", 0))
    for e in rows:
        if e.get("type") != "toast":
            continue
        ts_iso = datetime.datetime.fromtimestamp(e.get("epoch", time.time())).isoformat()
        w.writerow([ts_iso, e.get("level", "info"), e.get("msg", "")])

    fname = f"actions_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return dcc.send_string(buf.getvalue(), filename=fname)


# --- Scan & Auto-add Trade callbacks ---
@app.callback(
    Output("candidates-store", "data"),
    Output("toast-store", "data", allow_duplicate=True),
    Output("scan-status", "children"),
    Input("scan-btn", "n_clicks"),
    prevent_initial_call=True
)
def run_scan(n):
    print(f"[SCAN] Button clicked n={n}")
    cands = generate_scan()
    count = len(cands)
    print(f"[SCAN] Generated {count} candidates")
    msg = f"Scan: {count} @ {datetime.datetime.now().strftime('%H:%M:%S')}"
    enqueue_toast(f"Scan: {count}")
    return cands, {"msg": f"Scan: {count}"}, msg

@app.callback(
    Output("trade-table","data", allow_duplicate=True),
    Input("candidates-store","data"),
    State("trade-table","data"),
    prevent_initial_call=True
)
def auto_add(cands, current_rows):
    rows = current_rows or []
    if cands:
        inc = [c for c in cands if c["strategy_type"] == "income"][:2]
        print(f"[AUTO_ADD] candidates in: {len(cands)}; income picked: {len(inc)}")
        for c in inc:
            print(f"[AUTO_ADD] adding trade: {c['symbol']}  dte={c['dte']}  iv={c['iv_rank']}")
            add_trade_from_candidate(c)
        enqueue_toast(f"Added {len(inc)} trades")
    # rebuild rows
    rows = []
    for t in runtime_state["trades"]:
        if t.get("closed"): continue
        cap, tu = t["prem_captured_pct"], t["time_used_pct"]
        prog = f"{cap:.0f}% | {tu:.0f}%"
        rows.append({
            "opened": t["opened"], "symbol": t["symbol"],
            "strategy_type": t["strategy_type"], "strike": t["strike"], "dte": int(max(0, round(t["dte"]))),
            "capture_progress": prog, "unrealized_pnl": round(t["unrealized_pnl"], 2),
            "exit_state": t["exit_state"], "why_summary": t["why_summary"],
            "close_half": "1/2", "close_all": "x", "send_broker": "->",
            "prem_captured_pct": cap, "time_used_pct": tu
        })
    print(f"[AUTO_ADD] table rows now: {len(rows)}")
    return rows

# --- Drilldown & Toast ---
@app.callback(
    Output("drilldown","children"),
    Output("toast-store","data", allow_duplicate=True),
    Input("trade-table","active_cell"),
    State("trade-table","data"),
    prevent_initial_call=True
)
def on_table_click(cell, rows):
    if not cell or not rows:
        return dash.no_update, dash.no_update
    r, col = cell["row"], cell["column_id"]
    row = rows[r]
    print(f"[CLICK] col={col}, symbol={row.get('symbol')}, opened={row.get('opened')}")
    for t in runtime_state["trades"]:
        if t["symbol"] == row["symbol"] and t["opened"] == row["opened"]:
            if col == "close_half":
                close_trade(t["id"], full=False); msg = f"Partially closed {t['symbol']}"
                enqueue_toast(msg); return msg, {"msg": msg}
            if col == "close_all":
                close_trade(t["id"], full=True); msg = f"Fully closed {t['symbol']}"
                enqueue_toast(msg); return msg, {"msg": msg}
            if col == "send_broker":
                print(f"[ACTION] send_broker {t['symbol']}")
                msg = send_short_put_order(t)  # try option order, else equity fallback
                level = "success" if msg.startswith(("Sent", "Order DRY-RUN")) else "error"
                enqueue_toast(msg, level=level)
                return msg, {"msg": msg, "level": level}
    return dash.no_update, dash.no_update

# --- Smart toast color ---
@app.callback(
    Output("toast","children"),
    Output("toast","style"),
    Input("toast-store","data")
)
def show_toast(ts):
    base = {
        "fontWeight":"bold","minHeight":"20px","marginTop":"6px","fontSize":"12px",
        "padding":"6px","border":"1px solid #e5e5e5","borderRadius":"4px","background":"#fafafa"
    }
    if not ts:
        return "", base
    level = (ts.get("level") or "info").lower()
    color = {
        "success": "#237804",  # green
        "info":    "#222",     # neutral/dark
        "warn":    "#a86500",  # amber
        "warning": "#a86500",
        "error":   "#a8071a"   # red
    }.get(level, "#222")
    return ts.get("msg",""), {**base, "color": color}

# --- IVR diagnostics (pinned in top bar) ---
@app.callback(
    Output("diag-panel", "children"),
    Input("ivr-ping", "n_intervals"),
    State("runtime-settings","data"),
    prevent_initial_call=False
)
def diag_ping(_, rt_settings):
    try:
        watch = runtime_state.get("settings", {}).get("watchlist", CONFIG["lists"]["default_watchlist"])
        title = html.Span("Quotes / IVR: ", style={"fontWeight":"bold","marginRight":"6px"})
        if not watch:
            return [title, html.Span("No symbols")]
        sym = watch[0]
        if not USE_LIVE:
            return [title, html.Span(f"{sym}: sim mode — set USE_LIVE=true for IVR")]
        ivr = fetch_iv_rank(sym)
        runtime_state.setdefault("last_ivr", {}); runtime_state["last_ivr"][sym] = {"ivr": ivr, "ts": time.time()}
        save_state()
        ivr_thresh = int((rt_settings or {}).get("ivr_threshold", IVR_ALERT_THRESHOLD))
        if ivr is None:
            return [title, html.Span(f"{sym}: IVR n/a (Sandbox)")]
        if ivr >= ivr_thresh:
            enqueue_toast(f"IVR Alert: {sym} = {ivr:.0f} (≥ {ivr_thresh})")
        return [title, html.Span(f"{sym}: IVR {ivr:.1f} (≥{ivr_thresh})")]
    except Exception as e:
        return [html.Span("Quotes / IVR: ", style={"fontWeight":"bold","marginRight":"6px"}),
                html.Span(f"err: {e}")]

# --- Broker status badge updater ---
_last_ok = {"ok": None}
@app.callback(
    Output("broker-status", "children"),
    Output("broker-status", "style"),
    Input("broker-ping", "n_intervals")
)
def update_broker_badge(_):
    env_mode = "Live" if os.getenv("USE_LIVE", "false").lower() == "true" else "Sandbox"
    base_style = {"marginLeft": "16px","fontSize": "12px","padding": "2px 6px","borderRadius": "4px"}
    try:
        info = broker_whoami()
        if info.get("ok"):
            _last_ok["ok"] = True
            text = f"Broker: Connected ({env_mode})"
            style = {**base_style, "background": "#e6ffed", "border": "1px solid #b7eb8f", "color": "#237804"}
            return text, style
    except Exception:
        pass
    if _last_ok.get("ok") is True:
        text = f"Broker: Connected ({env_mode})"
        style = {**base_style, "background": "#e6ffed", "border": "1px solid #b7eb8f", "color": "#237804"}
    else:
        text = "Broker: Disconnected"
        style = {**base_style, "background": "#fff1f0", "border": "1px solid #ffa39e", "color": "#a8071a"}
    return text, style

# --- Run server ---
if __name__=="__main__":
    print("Starting Smart Options Assistant", APP_VERSION)
    app.run(debug=True)
