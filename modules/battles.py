"""Collection Battles — head-to-head collection comparisons."""

import json
import os
import random
import string
import uuid
from datetime import datetime, timedelta

from auth import _get_user_dir, _atomic_json_write, _safe_json_load, _load_users


_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_BATTLES_DIR = os.path.join(_DATA_DIR, "battles")
_PENDING_DIR = os.path.join(_BATTLES_DIR, "pending")
_RESULTS_DIR = os.path.join(_BATTLES_DIR, "results")


def _ensure_dirs():
    os.makedirs(_PENDING_DIR, exist_ok=True)
    os.makedirs(_RESULTS_DIR, exist_ok=True)


def get_portfolio_for_user(username: str) -> list[dict]:
    """Load a specific user's portfolio directly."""
    portfolio_path = os.path.join(_get_user_dir(username), "portfolio.json")
    return _safe_json_load(portfolio_path, list)


def generate_battle_code(username: str) -> str:
    """Generate a 6-char battle code. Saved as pending with 1hr expiry."""
    _ensure_dirs()
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    pending = {
        "code": code,
        "initiator": username,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
    }
    _atomic_json_write(os.path.join(_PENDING_DIR, f"{code}.json"), pending)
    return code


def accept_battle(code: str, challenger: str) -> dict | None:
    """Accept a battle by code. Returns battle result or None if invalid."""
    _ensure_dirs()
    pending_path = os.path.join(_PENDING_DIR, f"{code.upper()}.json")
    pending = _safe_json_load(pending_path, dict)

    if not pending:
        return None

    # Check expiry
    try:
        expires = datetime.fromisoformat(pending["expires_at"])
        if datetime.now() > expires:
            _cleanup_pending(code)
            return None
    except (ValueError, KeyError):
        return None

    initiator = pending["initiator"]
    if initiator == challenger:
        return None  # can't battle yourself

    # Verify both users exist
    users = _load_users()
    if initiator not in users or challenger not in users:
        return None

    # Run the battle
    result = compute_battle(initiator, challenger)

    # Save result
    save_battle_result(result)

    # Record in both users' battle history
    _record_user_battle(initiator, result)
    _record_user_battle(challenger, result)

    # Cleanup pending
    _cleanup_pending(code)

    return result


def compute_battle(user_a: str, user_b: str) -> dict:
    """Compute a head-to-head battle between two users' collections."""
    portfolio_a = get_portfolio_for_user(user_a)
    portfolio_b = get_portfolio_for_user(user_b)

    # Get market values (use purchase_price as fallback)
    stats_a = _compute_portfolio_stats(portfolio_a)
    stats_b = _compute_portfolio_stats(portfolio_b)

    # Score 5 categories (20 points each, 100 total)
    categories = []
    score_a = 0
    score_b = 0

    # 1. Total Value
    cat = _score_category("Total Value", stats_a["total_value"], stats_b["total_value"])
    categories.append(cat)
    score_a += cat["score_a"]
    score_b += cat["score_b"]

    # 2. Best Card
    cat = _score_category("Best Card", stats_a["best_card_value"], stats_b["best_card_value"])
    categories.append(cat)
    score_a += cat["score_a"]
    score_b += cat["score_b"]

    # 3. Biggest Gainer (P&L %)
    cat = _score_category("Biggest Gainer", stats_a["best_gainer_pct"], stats_b["best_gainer_pct"])
    categories.append(cat)
    score_a += cat["score_a"]
    score_b += cat["score_b"]

    # 4. Diversification
    cat = _score_category("Diversification", stats_a["diversity_score"], stats_b["diversity_score"])
    categories.append(cat)
    score_a += cat["score_a"]
    score_b += cat["score_b"]

    # 5. Collection Size
    cat = _score_category("Collection Size", stats_a["total_cards"], stats_b["total_cards"])
    categories.append(cat)
    score_a += cat["score_a"]
    score_b += cat["score_b"]

    winner = user_a if score_a > score_b else user_b if score_b > score_a else "TIE"

    battle_id = str(uuid.uuid4())[:8]

    return {
        "battle_id": battle_id,
        "user_a": user_a,
        "user_b": user_b,
        "score_a": score_a,
        "score_b": score_b,
        "winner": winner,
        "categories": categories,
        "stats_a": stats_a,
        "stats_b": stats_b,
        "battled_at": datetime.now().isoformat(),
    }


def _compute_portfolio_stats(portfolio: list[dict]) -> dict:
    """Compute stats needed for battle scoring. Uses real market data for up to
    10 cards per user to keep API calls manageable."""
    if not portfolio:
        return {
            "total_value": 0,
            "total_cards": 0,
            "best_card_value": 0,
            "best_card_name": "None",
            "best_gainer_pct": 0,
            "best_gainer_name": "None",
            "diversity_score": 0,
            "sports": [],
        }

    # Limit market lookups to first 10 cards
    from modules.trade_analyzer import get_card_market_value

    total_value = 0
    best_card_value = 0
    best_card_name = ""
    best_gainer_pct = 0
    best_gainer_name = ""
    sports = set()

    lookup_cards = portfolio[:10]

    for card in portfolio:
        price = card.get("purchase_price", 0)
        qty = card.get("quantity", 1)
        card_value = price * qty
        total_value += card_value
        sports.add(card.get("sport", ""))

        if card_value > best_card_value:
            best_card_value = card_value
            best_card_name = card.get("player_name", "Unknown")

        # Real market P&L for cards in the lookup set
        if card in lookup_cards:
            try:
                market = get_card_market_value(
                    card.get("player_name", ""), card.get("sport", "NBA"),
                    card.get("card_type", "Base"),
                    year=card.get("year"), set_name=card.get("set_name"),
                )
                market_val = market.get("avg_sold", 0) or market.get("avg_active", 0)
                if market_val > 0 and price > 0:
                    gainer_pct = ((market_val - price) / price) * 100
                    if gainer_pct > best_gainer_pct:
                        best_gainer_pct = gainer_pct
                        best_gainer_name = card.get("player_name", "Unknown")
            except Exception:
                pass

    # Diversification: count unique sports + card types
    card_types = set(c.get("card_type", "") for c in portfolio)
    diversity_score = len(sports) * 15 + min(len(card_types), 5) * 6

    return {
        "total_value": round(total_value, 2),
        "total_cards": len(portfolio),
        "best_card_value": round(best_card_value, 2),
        "best_card_name": best_card_name,
        "best_gainer_pct": round(best_gainer_pct, 1),
        "best_gainer_name": best_gainer_name,
        "diversity_score": min(diversity_score, 100),
        "sports": list(sports),
    }


def _score_category(name: str, val_a: float, val_b: float) -> dict:
    """Score a single category. Winner gets 20 pts, loser 0. Tie: 10 each."""
    if val_a > val_b:
        return {"name": name, "score_a": 20, "score_b": 0, "val_a": val_a, "val_b": val_b}
    elif val_b > val_a:
        return {"name": name, "score_a": 0, "score_b": 20, "val_a": val_a, "val_b": val_b}
    else:
        return {"name": name, "score_a": 10, "score_b": 10, "val_a": val_a, "val_b": val_b}


def save_battle_result(result: dict) -> str:
    """Save a battle result to the results directory."""
    _ensure_dirs()
    path = os.path.join(_RESULTS_DIR, f"{result['battle_id']}.json")
    _atomic_json_write(path, result)
    return result["battle_id"]


def _record_user_battle(username: str, result: dict) -> None:
    """Record a battle in a user's battle history."""
    path = os.path.join(_get_user_dir(username), "battles.json")
    battles = _safe_json_load(path, list)

    opponent = result["user_b"] if result["user_a"] == username else result["user_a"]
    my_score = result["score_a"] if result["user_a"] == username else result["score_b"]
    their_score = result["score_b"] if result["user_a"] == username else result["score_a"]
    won = result["winner"] == username

    battles.insert(0, {
        "battle_id": result["battle_id"],
        "opponent": opponent,
        "result": "W" if won else ("L" if result["winner"] != "TIE" else "T"),
        "my_score": my_score,
        "their_score": their_score,
        "date": result["battled_at"],
    })
    # Keep last 50
    battles = battles[:50]
    _atomic_json_write(path, battles)


def get_user_battles(username: str) -> list[dict]:
    """Get a user's battle history."""
    path = os.path.join(_get_user_dir(username), "battles.json")
    return _safe_json_load(path, list)


def _cleanup_pending(code: str) -> None:
    """Remove a pending battle file."""
    path = os.path.join(_PENDING_DIR, f"{code.upper()}.json")
    try:
        os.remove(path)
    except OSError:
        pass


def render_battle_card_html(result: dict) -> str:
    """Generate a styled HTML battle result card for sharing."""
    winner = result["winner"]
    is_tie = winner == "TIE"

    if is_tie:
        verdict = "IT'S A TIE!"
        verdict_color = "#facc15"
    else:
        verdict = f"{winner} WINS!"
        verdict_color = "#22c55e"

    cats_html = ""
    for cat in result["categories"]:
        a_style = "font-weight:bold;color:#22c55e;" if cat["score_a"] > cat["score_b"] else ""
        b_style = "font-weight:bold;color:#22c55e;" if cat["score_b"] > cat["score_a"] else ""
        cats_html += (
            f'<tr>'
            f'<td style="{a_style}">{_fmt_val(cat["val_a"], cat["name"])}</td>'
            f'<td style="text-align:center;color:#9ca3af;">{cat["name"]}</td>'
            f'<td style="text-align:right;{b_style}">{_fmt_val(cat["val_b"], cat["name"])}</td>'
            f'</tr>'
        )

    return f"""
    <div style="background:linear-gradient(135deg,#1a1f2e,#2d3748);border-radius:16px;
                padding:24px;max-width:500px;margin:auto;border:2px solid #3b4560;">
        <div style="text-align:center;margin-bottom:16px;">
            <div style="font-size:0.8em;color:#9ca3af;text-transform:uppercase;letter-spacing:2px;">
                Collection Battle</div>
            <div style="font-size:1.8em;font-weight:900;color:{verdict_color};margin:8px 0;">
                {verdict}</div>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin:16px 0;">
            <div style="text-align:center;flex:1;">
                <div style="font-size:1.1em;font-weight:bold;">{result['user_a']}</div>
                <div style="font-size:2em;font-weight:900;">{result['score_a']}</div>
            </div>
            <div style="font-size:1.5em;color:#6b7280;font-weight:bold;">VS</div>
            <div style="text-align:center;flex:1;">
                <div style="font-size:1.1em;font-weight:bold;">{result['user_b']}</div>
                <div style="font-size:2em;font-weight:900;">{result['score_b']}</div>
            </div>
        </div>
        <table style="width:100%;border-collapse:collapse;font-size:0.9em;">
            {cats_html}
        </table>
        <div style="text-align:center;margin-top:12px;">
            <a href="https://cardhawk.streamlit.app" target="_blank"
               style="color:#f59e0b;text-decoration:none;font-size:0.8em;font-weight:bold;">
               cardhawk.streamlit.app</a>
        </div>
    </div>
    """


def _fmt_val(val, category: str) -> str:
    """Format a value for display in the battle card."""
    if category in ("Total Value", "Best Card"):
        return f"${val:,.2f}"
    elif category == "Biggest Gainer":
        return f"{val:+.1f}%"
    elif category == "Diversification":
        return f"{val}/100"
    else:
        return str(int(val))
