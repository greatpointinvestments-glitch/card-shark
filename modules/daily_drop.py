"""Daily Drop Challenge — vote BUY/PASS on a daily card, build streaks, compete."""

import json
import os
from datetime import datetime, date, timedelta

from modules.card_of_day import get_card_of_the_day
from auth import _get_user_dir, _atomic_json_write, _safe_json_load


# --- Paths ---

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_LEADERBOARD_PATH = os.path.join(_DATA_DIR, "daily_drop_leaderboard.json")
_HISTORY_PATH = os.path.join(_DATA_DIR, "daily_drop_history.json")


def _votes_path(username: str) -> str:
    return os.path.join(_get_user_dir(username), "votes.json")


# --- Core Functions ---

def get_daily_card() -> dict | None:
    """Get today's daily drop card. Wraps card_of_day with drop metadata."""
    cotd = get_card_of_the_day()
    if not cotd:
        return None
    return {
        **cotd,
        "drop_date": str(date.today()),
        "drop_price": cotd["listing"]["total"] if cotd.get("listing") else 0,
    }


def cast_vote(username: str, drop_date: str, vote: str) -> bool:
    """Save a user's BUY or PASS vote for a given drop date."""
    if vote not in ("BUY", "PASS"):
        return False

    path = _votes_path(username)
    votes = _safe_json_load(path, dict)

    if drop_date in votes:
        return False  # already voted

    card = get_daily_card()
    votes[drop_date] = {
        "vote": vote,
        "voted_at": datetime.now().isoformat(),
        "player_name": card["player_name"] if card else "Unknown",
        "sport": card["sport"] if card else "",
        "drop_price": card["drop_price"] if card else 0,
    }
    _atomic_json_write(path, votes)

    # Update global vote counts
    _record_global_vote(drop_date, vote, card)
    return True


def get_user_vote(username: str, drop_date: str) -> str | None:
    """Get the user's vote for a specific drop date."""
    votes = _safe_json_load(_votes_path(username), dict)
    entry = votes.get(drop_date)
    return entry["vote"] if entry else None


def get_user_votes(username: str) -> dict:
    """Get all votes for a user."""
    return _safe_json_load(_votes_path(username), dict)


def _record_global_vote(drop_date: str, vote: str, card: dict | None) -> None:
    """Track global vote counts for community split display."""
    history = _safe_json_load(_HISTORY_PATH, dict)
    if drop_date not in history:
        history[drop_date] = {
            "player_name": card["player_name"] if card else "Unknown",
            "sport": card["sport"] if card else "",
            "drop_price": card["drop_price"] if card else 0,
            "result_price": None,
            "correct_vote": None,
            "total_buy_votes": 0,
            "total_pass_votes": 0,
        }
    if vote == "BUY":
        history[drop_date]["total_buy_votes"] += 1
    else:
        history[drop_date]["total_pass_votes"] += 1
    _atomic_json_write(_HISTORY_PATH, history)


def get_community_split(drop_date: str) -> dict:
    """Get the BUY/PASS vote split for a drop date."""
    history = _safe_json_load(_HISTORY_PATH, dict)
    entry = history.get(drop_date, {})
    buy = entry.get("total_buy_votes", 0)
    pas = entry.get("total_pass_votes", 0)
    total = buy + pas
    return {
        "buy_votes": buy,
        "pass_votes": pas,
        "total_votes": total,
        "buy_pct": round(buy / total * 100) if total > 0 else 50,
        "pass_pct": round(pas / total * 100) if total > 0 else 50,
    }


def check_drop_result(drop_date: str) -> dict | None:
    """Check if a drop's 7-day result is available. Returns result dict or None."""
    history = _safe_json_load(_HISTORY_PATH, dict)
    entry = history.get(drop_date)
    if not entry:
        return None

    # Already resolved
    if entry.get("result_price") is not None:
        return entry

    # Check if 30 days have passed
    try:
        drop_dt = datetime.strptime(drop_date, "%Y-%m-%d").date()
    except ValueError:
        return None

    if date.today() < drop_dt + timedelta(days=30):
        return None  # not enough time

    # Try to get current price for the player
    try:
        from modules.trade_analyzer import get_card_market_value
        result = get_card_market_value(
            entry["player_name"], entry.get("sport", "NBA"), "Any"
        )
        result_price = result.get("avg_sold", entry["drop_price"])
    except Exception:
        result_price = entry["drop_price"]  # fallback: no change

    # Determine correct vote
    price_change = result_price - entry["drop_price"]
    correct_vote = "BUY" if price_change > 0 else "PASS"

    entry["result_price"] = round(result_price, 2)
    entry["correct_vote"] = correct_vote
    entry["price_change_pct"] = round(
        (price_change / entry["drop_price"] * 100) if entry["drop_price"] > 0 else 0, 1
    )
    history[drop_date] = entry
    _atomic_json_write(_HISTORY_PATH, history)
    return entry


def compute_user_streak(username: str) -> dict:
    """Compute voting streak stats for a user."""
    votes = _safe_json_load(_votes_path(username), dict)
    history = _safe_json_load(_HISTORY_PATH, dict)

    total_correct = 0
    total_resolved = 0
    current_streak = 0
    best_streak = 0
    temp_streak = 0

    # Sort dates chronologically
    sorted_dates = sorted(votes.keys())

    for d in sorted_dates:
        user_vote = votes[d]["vote"]
        drop = history.get(d, {})
        correct_vote = drop.get("correct_vote")

        if correct_vote is None:
            continue  # not resolved yet

        total_resolved += 1
        if user_vote == correct_vote:
            total_correct += 1
            temp_streak += 1
            best_streak = max(best_streak, temp_streak)
        else:
            temp_streak = 0

    current_streak = temp_streak
    accuracy = round(total_correct / total_resolved * 100, 1) if total_resolved > 0 else 0

    return {
        "current_streak": current_streak,
        "best_streak": best_streak,
        "total_correct": total_correct,
        "total_votes": len(votes),
        "total_resolved": total_resolved,
        "accuracy_pct": accuracy,
    }


def get_leaderboard(limit: int = 20) -> list[dict]:
    """Build the Daily Drop leaderboard from all users' votes."""
    users_dir = os.path.join(_DATA_DIR, "users")
    if not os.path.isdir(users_dir):
        return []

    entries = []
    for username in os.listdir(users_dir):
        user_dir = os.path.join(users_dir, username)
        if not os.path.isdir(user_dir):
            continue
        votes_file = os.path.join(user_dir, "votes.json")
        if not os.path.exists(votes_file):
            continue
        stats = compute_user_streak(username)
        if stats["total_votes"] == 0:
            continue
        entries.append({
            "username": username,
            "current_streak": stats["current_streak"],
            "best_streak": stats["best_streak"],
            "accuracy_pct": stats["accuracy_pct"],
            "total_votes": stats["total_votes"],
        })

    # Sort by current streak (desc), then accuracy (desc)
    entries.sort(key=lambda x: (x["current_streak"], x["accuracy_pct"]), reverse=True)
    return entries[:limit]


def get_recent_drops(days: int = 7) -> list[dict]:
    """Get resolved drops from the last N days."""
    history = _safe_json_load(_HISTORY_PATH, dict)
    cutoff = str(date.today() - timedelta(days=days))

    results = []
    for d, entry in sorted(history.items(), reverse=True):
        if d < cutoff:
            break
        # Try to resolve if not already
        check_drop_result(d)
        # Reload entry
        updated = _safe_json_load(_HISTORY_PATH, dict).get(d, entry)
        results.append({"date": d, **updated})

    return results
