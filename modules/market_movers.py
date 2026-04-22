"""Market Movers — biggest weekly price gainers and losers using real eBay data."""

import streamlit as st

from modules.trade_analyzer import get_card_market_value


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_market_data(player: str, sport: str) -> dict | None:
    """Fetch real market data for a player's rookie base card."""
    try:
        result = get_card_market_value(player, sport, "Rookie")
        if result and (result.get("avg_sold", 0) > 0 or result.get("avg_active", 0) > 0):
            return result
    except Exception:
        pass
    return None


def compute_market_movers(
    watchlist_data: list[dict],
    max_players: int = 10,
) -> dict:
    """Compute top gainers and losers from real eBay market data.

    Parameters
    ----------
    watchlist_data : list of dicts with 'name' and 'sport' keys
    max_players : max number of gainers/losers to return

    Returns dict with 'gainers' and 'losers' lists, each containing:
    {name, sport, current_price, prev_price, change_pct}
    """
    movers = []

    for player_data in watchlist_data:
        name = player_data["name"]
        sport = player_data.get("sport", "NBA")
        market = _fetch_market_data(name, sport)

        if not market:
            continue

        current_price = market.get("avg_sold", 0) or market.get("avg_active", 0)
        if current_price <= 0:
            continue

        trend_delta = market.get("trend_delta", 0)
        # Compute previous price from current + trend delta
        prev_price = current_price / (1 + trend_delta / 100) if trend_delta != 0 else current_price

        movers.append({
            "name": name,
            "sport": sport,
            "current_price": round(current_price, 2),
            "prev_price": round(prev_price, 2),
            "change_pct": round(trend_delta, 1),
        })

    # Sort by change percentage
    movers.sort(key=lambda x: x["change_pct"], reverse=True)

    gainers = [m for m in movers if m["change_pct"] > 0][:max_players]
    losers = [m for m in movers if m["change_pct"] < 0]
    losers.sort(key=lambda x: x["change_pct"])
    losers = losers[:max_players]

    return {"gainers": gainers, "losers": losers}
