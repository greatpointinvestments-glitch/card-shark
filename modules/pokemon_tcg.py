"""Pokemon TCG API client — card search and TCGPlayer pricing.

Uses the free Pokemon TCG API (https://pokemontcg.io) which embeds
TCGPlayer market prices in every card response. No API key required.

Usage:
    from modules.pokemon_tcg import search_pokemon_cards, get_pokemon_sets
    cards = search_pokemon_cards("Charizard")
"""

import requests
import streamlit as st

POKEMON_TCG_BASE_URL = "https://api.pokemontcg.io/v2"


# ------------------------------------------------------------------
# Card search
# ------------------------------------------------------------------

@st.cache_data(ttl=300)
def search_pokemon_cards(
    card_name: str,
    set_name: str | None = None,
    rarity: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search for Pokemon cards by name with optional set/rarity filters.

    Returns parsed card dicts with embedded TCGPlayer market prices.
    """
    if not card_name or not card_name.strip():
        return []

    # Build query — pokemontcg.io uses Lucene-style syntax
    q_parts = [f'name:"{card_name.strip()}"']
    if set_name:
        q_parts.append(f'set.name:"{set_name.strip()}"')
    if rarity:
        q_parts.append(f'rarity:"{rarity.strip()}"')

    params = {
        "q": " ".join(q_parts),
        "pageSize": min(limit, 250),
        "orderBy": "-set.releaseDate",  # newest sets first
    }

    try:
        resp = requests.get(
            f"{POKEMON_TCG_BASE_URL}/cards",
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return [_parse_card(c) for c in data.get("data", [])]
    except requests.RequestException:
        return []


@st.cache_data(ttl=300)
def get_pokemon_card_by_id(card_id: str) -> dict | None:
    """Fetch a single Pokemon card by its API id (e.g. 'base1-4')."""
    if not card_id:
        return None
    try:
        resp = requests.get(
            f"{POKEMON_TCG_BASE_URL}/cards/{card_id}",
            timeout=10,
        )
        resp.raise_for_status()
        return _parse_card(resp.json().get("data", {}))
    except requests.RequestException:
        return None


# ------------------------------------------------------------------
# Sets
# ------------------------------------------------------------------

@st.cache_data(ttl=3600)
def get_pokemon_sets() -> list[dict]:
    """Return all Pokemon TCG sets, sorted newest-first."""
    try:
        resp = requests.get(
            f"{POKEMON_TCG_BASE_URL}/sets",
            params={"orderBy": "-releaseDate", "pageSize": 250},
            timeout=15,
        )
        resp.raise_for_status()
        sets_data = resp.json().get("data", [])
        return [
            {
                "id": s.get("id", ""),
                "name": s.get("name", ""),
                "series": s.get("series", ""),
                "release_date": s.get("releaseDate", ""),
                "total_cards": s.get("total", 0),
                "logo_url": s.get("images", {}).get("logo", ""),
                "symbol_url": s.get("images", {}).get("symbol", ""),
            }
            for s in sets_data
        ]
    except requests.RequestException:
        return []


# ------------------------------------------------------------------
# Pricing helpers
# ------------------------------------------------------------------

def get_pokemon_market_price(card: dict) -> float:
    """Extract the best TCGPlayer market price from a parsed card.

    Priority: holofoil > reverseHolofoil > normal > 1stEditionHolofoil > 0.
    """
    prices = card.get("tcgplayer_prices", {})
    for variant in ("holofoil", "reverseHolofoil", "normal", "1stEditionHolofoil",
                     "1stEditionNormal", "unlimitedHolofoil", "unlimited"):
        vp = prices.get(variant, {})
        market = vp.get("market") or vp.get("mid") or 0
        if market and market > 0:
            return round(market, 2)
    return 0.0


def get_pokemon_market_summary(cards: list[dict]) -> dict:
    """Build a market summary dict matching the shape of ebay_search.get_market_summary().

    This lets the UI render Pokemon pricing with the same render_market_summary() helper.
    """
    prices = [get_pokemon_market_price(c) for c in cards]
    valid_prices = [p for p in prices if p > 0]

    avg_price = round(sum(valid_prices) / len(valid_prices), 2) if valid_prices else 0
    volume = len(valid_prices)

    return {
        "avg_sold": avg_price,
        "sold_volume": volume,
        "avg_active": avg_price,
        "price_trend": "Stable",
        "trend_delta": 0.0,
        "market_signal": "FAIR VALUE" if avg_price > 0 else "N/A",
        "active_vs_sold_pct": 0.0,
    }


# ------------------------------------------------------------------
# Internal parsers
# ------------------------------------------------------------------

def _parse_card(card: dict) -> dict:
    """Parse a raw Pokemon TCG API card object into a clean dict."""
    images = card.get("images", {})
    set_info = card.get("set", {})
    tcgp = card.get("tcgplayer", {})
    tcgp_prices = tcgp.get("prices", {})

    return {
        "id": card.get("id", ""),
        "name": card.get("name", ""),
        "supertype": card.get("supertype", ""),  # Pokemon, Trainer, Energy
        "subtypes": card.get("subtypes", []),
        "hp": card.get("hp", ""),
        "types": card.get("types", []),
        "rarity": card.get("rarity", ""),
        "number": card.get("number", ""),
        "artist": card.get("artist", ""),
        # Set info
        "set_id": set_info.get("id", ""),
        "set_name": set_info.get("name", ""),
        "set_series": set_info.get("series", ""),
        "set_release_date": set_info.get("releaseDate", ""),
        # Images
        "image_small": images.get("small", ""),
        "image_large": images.get("large", ""),
        # TCGPlayer pricing
        "tcgplayer_url": tcgp.get("url", ""),
        "tcgplayer_updated": tcgp.get("updatedAt", ""),
        "tcgplayer_prices": tcgp_prices,
        # Convenience: best market price
        "market_price": 0.0,  # filled below
    }
