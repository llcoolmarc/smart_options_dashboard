"""
utils/broker.py

Tastytrade Broker Integration (Phase 19+20)
Supports SIM | SANDBOX | LIVE modes.
Default: SANDBOX (cert environment).
"""

import requests
import logging
from utils import preferences

logging.basicConfig(level=logging.DEBUG, format="[BROKER] %(message)s")


class BrokerSession:
    def __init__(self, base_url: str, paper: bool = True):
        self.base_url = base_url
        self.session = requests.Session()
        self.session_token = None
        self.logged_in = False
        self.paper = paper
        self.accounts = []

    def login(self, username: str, password: str) -> bool:
        """
        Login to Tastytrade (sandbox or live).
        Returns True if successful.
        """
        try:
            url = f"{self.base_url}/sessions"
            payload = {"login": username, "password": password}
            resp = self.session.post(url, json=payload, timeout=10)

            if resp.status_code == 201:
                data = resp.json()
                self.session_token = data.get("data", {}).get("session-token")
                self.session.headers.update({"Authorization": f"Bearer {self.session_token}"})
                self.logged_in = True
                logging.info("✅ Logged in to Tastytrade (%s)", "SANDBOX" if self.paper else "LIVE")
                return True
            else:
                logging.error("❌ Login failed (%s): %s", resp.status_code, resp.text)
                return False
        except Exception as e:
            logging.error("❌ Exception during login: %s", e)
            return False

    def get_accounts(self):
        """
        Fetch account list + balances.
        """
        if not self.logged_in:
            logging.error("❌ Not logged in")
            return []

        try:
            url = f"{self.base_url}/customers/me/accounts"
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self.accounts = []
                for acc in data.get("data", []):
                    acct_num = acc["account"]["account-number"]
                    balances = acc["account"].get("balances", {})
                    self.accounts.append({
                        "number": acct_num,
                        "cash-balance": balances.get("cash-balance"),
                        "margin-balance": balances.get("margin-balance"),
                        "buying-power": balances.get("margin-usable-trading-balance")
                    })
                logging.info("✅ Accounts: %s", [a["number"] for a in self.accounts])
                return self.accounts
            else:
                logging.error("❌ Failed to fetch accounts (%s): %s", resp.status_code, resp.text)
                return []
        except Exception as e:
            logging.error("❌ Exception fetching accounts: %s", e)
            return []

    def get_positions(self, account: str):
        """
        Fetch open positions for an account.
        """
        if not self.logged_in:
            logging.error("❌ Not logged in")
            return []

        try:
            url = f"{self.base_url}/accounts/{account}/positions"
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                positions = resp.json().get("data", [])
                logging.info("✅ Positions for %s: %s", account, len(positions))
                return positions
            else:
                logging.error("❌ Failed to fetch positions (%s): %s", resp.status_code, resp.text)
                return []
        except Exception as e:
            logging.error("❌ Exception fetching positions: %s", e)
            return []

    def place_order(self, account: str, order: dict):
        """
        Place a defined-risk spread order.
        Order dict must follow Tastytrade schema.
        """
        if not self.logged_in:
            logging.error("❌ Not logged in")
            return None

        try:
            url = f"{self.base_url}/accounts/{account}/orders"
            resp = self.session.post(url, json={"data": order}, timeout=10)
            if resp.status_code in (200, 201):
                logging.info("✅ Order placed successfully")
                return resp.json()
            else:
                logging.error("❌ Order failed (%s): %s", resp.status_code, resp.text)
                return None
        except Exception as e:
            logging.error("❌ Exception placing order: %s", e)
            return None

    def disconnect(self):
        """
        Disconnect session.
        """
        self.session.close()
        self.logged_in = False
        self.session_token = None
        logging.info("🔒 Disconnected from broker")


# === Safe Wrappers (Cockpit compliance) ===

def init_broker_session() -> BrokerSession:
    """
    Initialize broker session using preferences + .env.
    """
    prefs = preferences.load_preferences()
    broker_cfg = prefs.get("broker", {})
    base_url = broker_cfg.get("base_url", "https://api.cert.tastyworks.com")
    paper = "cert" in base_url  # sandbox if cert endpoint

    session = BrokerSession(base_url=base_url, paper=paper)
    if session.login(broker_cfg.get("username"), broker_cfg.get("password")):
        return session
    return session  # returns session, even if not logged in (cockpit handles it)


def safe_fetch_portfolio(session: BrokerSession):
    try:
        accounts = session.get_accounts()
        if not accounts:
            return {}
        positions = session.get_positions(accounts[0]["number"])
        return {"accounts": accounts, "positions": positions}
    except Exception as e:
        logging.error("❌ safe_fetch_portfolio failed: %s", e)
        return {}


def safe_fetch_marketdata(session: BrokerSession, symbol: str = "SPY"):
    try:
        url = f"{session.base_url}/market-metrics/{symbol}"
        resp = session.session.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            logging.error("❌ Marketdata failed (%s): %s", resp.status_code, resp.text)
            return {}
    except Exception as e:
        logging.error("❌ Exception fetching marketdata: %s", e)
        return {}


def broker_status(session: BrokerSession = None) -> str:
    """
    Return human-readable broker connection status.
    Used by graduation and cockpit UI.
    """
    if session is None:
        return "❌ No broker session"
    if not session.logged_in:
        return "❌ Not connected"
    mode = "SANDBOX" if session.paper else "LIVE"
    return f"✅ Connected ({mode})"
