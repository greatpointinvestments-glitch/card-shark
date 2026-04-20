"""Price Alerts — alert CRUD, threshold checking, JSON persistence."""

import json
import os
import tempfile
import uuid
from datetime import datetime

from config.settings import ALERTS_PATH


def _get_alerts_path() -> str:
    """Get the alerts path for the current user, or default."""
    try:
        import streamlit as st
        username = st.session_state.get("username")
        if username:
            from auth import get_user_alerts_path
            return get_user_alerts_path(username)
    except Exception:
        pass
    return ALERTS_PATH


def _load_alerts() -> list[dict]:
    """Read alerts from disk."""
    path = _get_alerts_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        backup = path + ".corrupt"
        try:
            os.replace(path, backup)
        except OSError:
            pass
        return []
    except IOError:
        return []


def _save_alerts(alerts: list[dict]) -> None:
    """Write alerts to disk atomically."""
    path = _get_alerts_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(alerts, f, indent=2)
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def add_alert(
    player_name: str,
    sport: str,
    card_type: str,
    alert_type: str,
    threshold_price: float,
    note: str = "",
) -> dict:
    """Add a new price alert. alert_type is 'below' or 'above'."""
    alerts = _load_alerts()
    new_alert = {
        "id": str(uuid.uuid4()),
        "player_name": player_name,
        "sport": sport,
        "card_type": card_type,
        "alert_type": alert_type,
        "threshold_price": threshold_price,
        "note": note,
        "created_at": datetime.now().isoformat(),
        "triggered": False,
        "last_price": None,
    }
    alerts.append(new_alert)
    _save_alerts(alerts)
    return new_alert


def remove_alert(alert_id: str) -> bool:
    """Remove an alert by UUID."""
    alerts = _load_alerts()
    original_len = len(alerts)
    alerts = [a for a in alerts if a["id"] != alert_id]
    if len(alerts) < original_len:
        _save_alerts(alerts)
        return True
    return False


def get_alerts() -> list[dict]:
    """Return all alerts."""
    return _load_alerts()


def check_alerts(market_values: dict) -> list[dict]:
    """Check which alerts are triggered based on current market values.

    Parameters
    ----------
    market_values : dict mapping "player_name|sport|card_type" -> current price

    Returns list of triggered alert dicts (with last_price updated).
    Also persists triggered state to disk.
    """
    triggered = []
    all_alerts = _load_alerts()
    changed = False

    for alert in all_alerts:
        key = f"{alert['player_name']}|{alert['sport']}|{alert['card_type']}"
        current_price = market_values.get(key)
        if current_price is None:
            continue

        alert["last_price"] = current_price
        was_triggered = alert["triggered"]

        if alert["alert_type"] == "below" and current_price <= alert["threshold_price"]:
            alert["triggered"] = True
        elif alert["alert_type"] == "above" and current_price >= alert["threshold_price"]:
            alert["triggered"] = True

        if alert["triggered"] and not was_triggered:
            triggered.append(alert)
            changed = True
        elif alert["last_price"] != current_price:
            changed = True

    if changed:
        _save_alerts(all_alerts)

    return triggered
