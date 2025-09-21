"""
utils/preferences.py
--------------------------------
Manages loading and saving of preferences.json
Adds .env overrides for broker credentials and mode (SANDBOX vs LIVE).
"""

import json
import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

PREFS_PATH = os.path.join("smart_options_dashboard", "preferences.json")


def load_preferences(path=PREFS_PATH):
    """
    Load preferences from JSON file, applying .env overrides for sensitive fields.
    Returns dict.
    """
    prefs = default_preferences()

    # Load from JSON if available
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                prefs.update(json.load(f))
        except Exception as e:
            print(f"[PREFERENCES] ⚠️ Failed to parse {path}: {e}")

    # Broker settings with environment overrides
    broker = prefs.get("broker", {})

    broker["username"] = os.getenv("TT_SANDBOX_USER", broker.get("username"))
    broker["password"] = os.getenv("TT_SANDBOX_PASS", broker.get("password"))

    # Mode selection (SANDBOX default unless USE_LIVE=true)
    use_live = os.getenv("USE_LIVE", "false").lower() == "true"
    broker["base_url"] = "https://api.tastyworks.com" if use_live else "https://api.cert.tastyworks.com"

    prefs["broker"] = broker
    return prefs


def save_preferences(prefs, path=PREFS_PATH):
    """
    Save preferences dict back to JSON file.
    """
    try:
        with open(path, "w") as f:
            json.dump(prefs, f, indent=2)
        print(f"[PREFERENCES] ✅ Saved to {path}")
    except Exception as e:
        print(f"[PREFERENCES] ❌ Failed to save {path}: {e}")


def default_preferences():
    """
    Return default preferences dict.
    """
    return {
        "target_expectancy": 1.0,
        "discipline_threshold": 50,
        "risk_limits": {
            "max_symbol_allocation": 0.3,
            "max_expiry_cluster": 5
        },
        "scaling_rules": {
            "base_contracts": 1,
            "scaling_factor": 2
        },
        "mode_default": "SIM",
        "broker": {
            "username": "",
            "password": "",
            "base_url": "https://api.cert.tastyworks.com",
            "login_endpoint": "/sessions"
        },
        "notifications": {
            "email_alerts": False,
            "slack_alerts": False
        }
    }
