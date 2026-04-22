"""Rip Battles — head-to-head pack rip challenges.

Same code-sharing pattern as Collection Battles (6-char code, 1hr expiry).
User A picks product + creates challenge -> User B enters code ->
both rip same product -> compare total value, best pull, hit count.
"""

import json
import os
import random
import string
from datetime import datetime, timedelta

from auth import _get_user_dir, _atomic_json_write, _safe_json_load
from modules.pack_simulator import rip_pack


_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_RIP_BATTLES_DIR = os.path.join(_DATA_DIR, "rip_battles")
_PENDING_DIR = os.path.join(_RIP_BATTLES_DIR, "pending")
_RESULTS_DIR = os.path.join(_RIP_BATTLES_DIR, "results")


def _ensure_dirs():
    os.makedirs(_PENDING_DIR, exist_ok=True)
    os.makedirs(_RESULTS_DIR, exist_ok=True)


def create_rip_challenge(username: str, product_key: str) -> str:
    """Create a rip battle challenge. Returns 6-char code."""
    _ensure_dirs()
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    pending = {
        "code": code,
        "initiator": username,
        "product_key": product_key,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
    }
    _atomic_json_write(os.path.join(_PENDING_DIR, f"{code}.json"), pending)
    return code


def accept_rip_battle(code: str, challenger: str) -> dict | None:
    """Accept a rip battle. Both players rip the same product. Returns result or None."""
    _ensure_dirs()
    pending_path = os.path.join(_PENDING_DIR, f"{code.upper()}.json")
    pending = _safe_json_load(pending_path, dict)

    if not pending:
        return None

    try:
        expires = datetime.fromisoformat(pending["expires_at"])
        if datetime.now() > expires:
            _cleanup(code)
            return None
    except (ValueError, KeyError):
        return None

    initiator = pending["initiator"]
    if initiator == challenger:
        return None

    product_key = pending["product_key"]

    # Both rip the same product
    cards_a = rip_pack(product_key)
    cards_b = rip_pack(product_key)

    if not cards_a or not cards_b:
        return None

    result = _score_rip_battle(initiator, challenger, product_key, cards_a, cards_b)

    # Save result
    path = os.path.join(_RESULTS_DIR, f"{result['battle_id']}.json")
    _atomic_json_write(path, result)

    _cleanup(code)
    return result


def _score_rip_battle(user_a: str, user_b: str, product_key: str,
                       cards_a: list[dict], cards_b: list[dict]) -> dict:
    """Score a rip battle across 3 categories."""
    val_a = sum(c["value"] for c in cards_a)
    val_b = sum(c["value"] for c in cards_b)
    best_a = max(cards_a, key=lambda c: c["value"])
    best_b = max(cards_b, key=lambda c: c["value"])
    hits_a = sum(1 for c in cards_a if c["is_hit"])
    hits_b = sum(1 for c in cards_b if c["is_hit"])

    score_a = 0
    score_b = 0

    # Total value
    if val_a > val_b:
        score_a += 1
    elif val_b > val_a:
        score_b += 1

    # Best pull
    if best_a["value"] > best_b["value"]:
        score_a += 1
    elif best_b["value"] > best_a["value"]:
        score_b += 1

    # Hit count
    if hits_a > hits_b:
        score_a += 1
    elif hits_b > hits_a:
        score_b += 1

    winner = user_a if score_a > score_b else user_b if score_b > score_a else "TIE"

    import uuid
    return {
        "battle_id": str(uuid.uuid4())[:8],
        "user_a": user_a,
        "user_b": user_b,
        "product_key": product_key,
        "cards_a": cards_a,
        "cards_b": cards_b,
        "total_value_a": round(val_a, 2),
        "total_value_b": round(val_b, 2),
        "best_pull_a": {"player": best_a["player_name"], "value": best_a["value"], "card_type": best_a["card_type"]},
        "best_pull_b": {"player": best_b["player_name"], "value": best_b["value"], "card_type": best_b["card_type"]},
        "hits_a": hits_a,
        "hits_b": hits_b,
        "score_a": score_a,
        "score_b": score_b,
        "winner": winner,
        "battled_at": datetime.now().isoformat(),
    }


def get_rip_hall_of_fame() -> dict:
    """Aggregate rip stats across all users for the Hall of Fame leaderboard."""
    _ensure_dirs()
    best_single_pull = {"player": "—", "value": 0, "user": "—", "card_type": ""}
    most_profitable = {"user": "—", "pl": -999}
    most_packs = {"user": "—", "count": 0}

    # Scan all user rip histories
    users_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "users")
    if not os.path.exists(users_dir):
        return {"best_pull": best_single_pull, "most_profitable": most_profitable, "most_packs": most_packs}

    try:
        for username in os.listdir(users_dir):
            user_dir = os.path.join(users_dir, username)
            rip_path = os.path.join(user_dir, "rip_history.json")
            if not os.path.exists(rip_path):
                continue
            history = _safe_json_load(rip_path, dict)

            # Most packs
            packs = history.get("total_packs", 0)
            if packs > most_packs["count"]:
                most_packs = {"user": username, "count": packs}

            # Most profitable
            total_val = history.get("total_value_pulled", 0)
            total_spent = history.get("total_spent_virtual", 0)
            pl = total_val - total_spent
            if pl > most_profitable["pl"]:
                most_profitable = {"user": username, "pl": round(pl, 2)}

            # Best single pull
            bp = history.get("best_pull")
            if bp and bp.get("value", 0) > best_single_pull["value"]:
                best_single_pull = {
                    "player": bp.get("player_name", "Unknown"),
                    "value": bp["value"],
                    "user": username,
                    "card_type": bp.get("card_type", ""),
                }
    except Exception:
        pass

    return {
        "best_pull": best_single_pull,
        "most_profitable": most_profitable,
        "most_packs": most_packs,
    }


def _cleanup(code: str):
    path = os.path.join(_PENDING_DIR, f"{code.upper()}.json")
    try:
        os.remove(path)
    except OSError:
        pass
