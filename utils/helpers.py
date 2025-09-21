import json
import os

STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "state.json")


def load_state() -> dict:
    """Load state.json safely; return empty dict if missing/corrupt."""
    try:
        if not os.path.exists(STATE_FILE):
            return {}
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(new_state: dict) -> None:
    """Merge and save state.json safely."""
    try:
        current = load_state()
        current.update(new_state)
        with open(STATE_FILE, "w") as f:
            json.dump(current, f, indent=2)
    except Exception:
        pass


def append_analytics_run(run: dict) -> None:
    """
    Append an analytics run to history.
    """
    state = load_state()
    history = state.get("analytics_history", [])
    history.append(run)
    state["analytics_history"] = history
    save_state(state)


def get_analytics_history() -> list:
    """
    Retrieve saved analytics runs.
    """
    state = load_state()
    return state.get("analytics_history", [])
