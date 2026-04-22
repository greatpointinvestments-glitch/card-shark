"""Pack Simulator — rip virtual packs with real player pools and market pricing."""

import json
import os
import random
from datetime import datetime

from config.pull_rates import PRODUCTS
from auth import _get_user_dir, _atomic_json_write, _safe_json_load
from data.watchlists import (
    NBA_BREAKOUT_WATCHLIST, NFL_BREAKOUT_WATCHLIST,
    MLB_BREAKOUT_WATCHLIST, LEGENDS_WATCHLIST,
    POKEMON_LEGENDS_WATCHLIST,
)


_PLAYER_POOLS = {
    "NBA": NBA_BREAKOUT_WATCHLIST + [p for p in LEGENDS_WATCHLIST if "Basketball" in p.get("sport_display", "Basketball")],
    "NFL": NFL_BREAKOUT_WATCHLIST,
    "MLB": MLB_BREAKOUT_WATCHLIST,
    "Pokemon": POKEMON_LEGENDS_WATCHLIST,
}

# Fallback value multipliers by rarity (when API pricing fails)
_VALUE_MULTIPLIERS = {
    "Base": 0.50,
    "Common": 0.25,
    "Uncommon": 0.50,
    "Reverse Holo": 1.00,
    "Holo Rare": 3.00,
    "Prizm Silver": 8.00,
    "Refractor": 5.00,
    "Red White Blue": 4.00,
    "Blue Prizm": 6.00,
    "Blue Refractor /199": 8.00,
    "Red Prizm": 10.00,
    "Green Refractor /99": 15.00,
    "ex": 5.00,
    "Full Art": 12.00,
    "Numbered /199": 15.00,
    "Numbered /75": 30.00,
    "Gold Refractor /50": 25.00,
    "Orange Refractor /25": 40.00,
    "Auto": 25.00,
    "Auto Refractor": 40.00,
    "Illustration Rare": 20.00,
    "Special Art Rare": 50.00,
    "Gold Prizm /10": 75.00,
    "Gold Auto /50": 60.00,
    "Green Shimmer /25": 50.00,
    "Red Refractor /5": 100.00,
    "Ultra Rare": 80.00,
    "Hyper Rare": 150.00,
    "Black 1/1": 500.00,
    "Superfractor 1/1": 500.00,
}


def _pick_player(sport: str, rng: random.Random) -> dict:
    """Pick a random player from the sport's pool."""
    pool = _PLAYER_POOLS.get(sport, _PLAYER_POOLS["NBA"])
    if not pool:
        return {"name": "Unknown Player", "team": "N/A"}
    return rng.choice(pool)


def _estimate_card_value(player_name: str, sport: str, card_type: str) -> float:
    """Estimate market value. Tries real API first, falls back to multiplier."""
    try:
        from modules.trade_analyzer import get_card_market_value
        result = get_card_market_value(player_name, sport, card_type)
        if result and result.get("avg_sold", 0) > 0:
            return round(result["avg_sold"], 2)
    except Exception:
        pass

    # Fallback: base value * multiplier
    base_value = 2.00 if sport != "Pokemon" else 1.00
    multiplier = _VALUE_MULTIPLIERS.get(card_type, 1.0)
    # Add some randomness
    return round(base_value * multiplier * random.uniform(0.7, 1.3), 2)


def _fetch_card_image(player_name: str, sport: str, card_type: str = "") -> str:
    """Fetch a card image URL. Pokemon: TCG API. Sports: eBay thumbnail (limit=1)."""
    cache_key = f"img_{player_name}_{sport}_{card_type}"

    # Check session cache
    try:
        import streamlit as st
        if cache_key in st.session_state:
            return st.session_state[cache_key]
    except Exception:
        pass

    image_url = ""
    try:
        if sport == "Pokemon":
            from modules.pokemon_tcg import search_pokemon_cards
            cards = search_pokemon_cards(player_name, limit=1)
            if cards and cards[0].get("image_small"):
                image_url = cards[0]["image_small"]
        else:
            from modules.ebay_search import search_ebay_cards
            listings = search_ebay_cards(player_name, sport, card_type, limit=1)
            if listings and listings[0].get("image_url"):
                image_url = listings[0]["image_url"]
    except Exception:
        pass

    # Cache in session state
    try:
        import streamlit as st
        st.session_state[cache_key] = image_url
    except Exception:
        pass

    return image_url


def _pick_tier(tiers: list[dict], rng: random.Random) -> dict:
    """Weighted random tier selection."""
    weights = [t["weight"] for t in tiers]
    return rng.choices(tiers, weights=weights, k=1)[0]


def rip_pack(product_key: str) -> list[dict]:
    """Rip a single pack. Returns list of card dicts."""
    product = PRODUCTS.get(product_key)
    if not product:
        return []

    rng = random.Random()
    cards = []
    sport = product["sport"]
    tiers = product["tiers"]

    for _ in range(product["cards_per_pack"]):
        tier = _pick_tier(tiers, rng)
        player = _pick_player(sport, rng)
        player_name = player.get("name", player.get("player_name", "Unknown"))

        value = _estimate_card_value(player_name, sport, tier["card_type"])

        # Fetch card image (hits get priority, base cards get images too)
        image_url = _fetch_card_image(player_name, sport, tier["card_type"])

        cards.append({
            "player_name": player_name,
            "team": player.get("team", "N/A"),
            "sport": sport,
            "card_type": tier["card_type"],
            "tier_name": tier["name"],
            "is_hit": tier["is_hit"],
            "value": value,
            "image_url": image_url,
        })

    return cards


def rip_box(product_key: str) -> dict:
    """Rip a full box. Returns summary with all packs."""
    product = PRODUCTS.get(product_key)
    if not product:
        return {}

    packs = []
    total_value = 0
    best_pull = None

    for i in range(product["packs_per_box"]):
        cards = rip_pack(product_key)
        pack_value = sum(c["value"] for c in cards)
        total_value += pack_value

        for card in cards:
            if best_pull is None or card["value"] > best_pull["value"]:
                best_pull = card

        packs.append({
            "pack_number": i + 1,
            "cards": cards,
            "pack_value": round(pack_value, 2),
        })

    return {
        "product": product_key,
        "packs": packs,
        "total_packs": product["packs_per_box"],
        "box_cost": product["box_price"],
        "total_value": round(total_value, 2),
        "profit_loss": round(total_value - product["box_price"], 2),
        "best_pull": best_pull,
    }


def save_rip_result(username: str, product_key: str, cards: list[dict], cost: float) -> None:
    """Append a rip result to the user's history."""
    path = os.path.join(_get_user_dir(username), "rip_history.json")
    history = _safe_json_load(path, dict)

    if "total_packs" not in history:
        history = {
            "total_packs": 0,
            "total_spent_virtual": 0,
            "total_value_pulled": 0,
            "best_pull": None,
            "rips": [],
        }

    pack_value = sum(c["value"] for c in cards)
    best_in_pack = max(cards, key=lambda c: c["value"]) if cards else None

    history["total_packs"] += 1
    history["total_spent_virtual"] = round(history["total_spent_virtual"] + cost, 2)
    history["total_value_pulled"] = round(history["total_value_pulled"] + pack_value, 2)

    if best_in_pack and (
        history["best_pull"] is None or best_in_pack["value"] > history["best_pull"].get("value", 0)
    ):
        history["best_pull"] = {
            "player_name": best_in_pack["player_name"],
            "card_type": best_in_pack["card_type"],
            "value": best_in_pack["value"],
            "date": str(datetime.now().date()),
        }

    # Keep last 50 rips
    history["rips"] = history.get("rips", [])
    history["rips"].insert(0, {
        "date": datetime.now().isoformat(),
        "product": product_key,
        "cards": cards,
        "pack_value": round(pack_value, 2),
        "cost": cost,
    })
    history["rips"] = history["rips"][:50]

    _atomic_json_write(path, history)


def get_rip_stats(username: str) -> dict:
    """Get rip history stats for a user."""
    path = os.path.join(_get_user_dir(username), "rip_history.json")
    history = _safe_json_load(path, dict)
    return {
        "total_packs": history.get("total_packs", 0),
        "total_spent_virtual": history.get("total_spent_virtual", 0),
        "total_value_pulled": history.get("total_value_pulled", 0),
        "best_pull": history.get("best_pull"),
        "virtual_pl": round(
            history.get("total_value_pulled", 0) - history.get("total_spent_virtual", 0), 2
        ),
        "recent_rips": history.get("rips", [])[:5],
    }
