"""Player Comparison — side-by-side player data and investment verdict."""

import streamlit as st

from modules.player_stats import search_players, format_player_info, get_multi_season_stats
from modules.ebay_search import search_ebay_cards, search_ebay_sold, get_market_summary
from modules.breakout_engine import compute_breakout_score


def fetch_player_comparison_data(player_name: str, sport: str) -> dict | None:
    """Fetch all comparison data for a single player.

    Calls existing functions: search_players, format_player_info,
    get_multi_season_stats, search_ebay_cards, search_ebay_sold,
    get_market_summary, compute_breakout_score.

    Returns
    -------
    dict with info, stats, market_summary, breakout, listings_count, sold_count.
    None if player not found.
    """
    players = search_players(player_name, sport)
    if not players:
        return None

    player = players[0]
    info = format_player_info(player, sport)
    stats = get_multi_season_stats(info["id"], sport, num_seasons=3)

    # eBay data
    active = search_ebay_cards(player_name, sport, "Rookie", limit=20)
    sold = search_ebay_sold(player_name, sport, "Rookie", limit=20)
    market_summary = get_market_summary(active, sold) if active and sold else None

    # Breakout score
    breakout = compute_breakout_score(info, stats or [], active or [])

    return {
        "info": info,
        "stats": stats or [],
        "market_summary": market_summary,
        "breakout": breakout,
        "listings_count": len(active) if active else 0,
        "sold_count": len(sold) if sold else 0,
    }


def generate_verdict(data_a: dict, data_b: dict, name_a: str, name_b: str) -> str:
    """Generate a human-readable investment verdict comparing two players.

    Point system:
    - Breakout score: direct comparison
    - Market signal bonus: BUY WINDOW +15, FAIR VALUE +5, OVERPRICED -10
    - Price trend bonus: Rising +10, Stable +5, Falling 0

    Returns a verdict string.
    """
    def _score_player(data: dict) -> int:
        points = 0

        # Breakout score (0-100)
        points += data["breakout"].get("score", 0)

        # Market signal bonus
        if data["market_summary"]:
            signal = data["market_summary"].get("market_signal", "")
            if signal == "BUY WINDOW":
                points += 15
            elif signal == "FAIR VALUE":
                points += 5
            elif signal == "OVERPRICED":
                points -= 10

            # Trend bonus
            trend = data["market_summary"].get("price_trend", "")
            if trend == "Rising":
                points += 10
            elif trend == "Stable":
                points += 5

        return points

    score_a = _score_player(data_a)
    score_b = _score_player(data_b)

    diff = abs(score_a - score_b)

    if diff <= 5:
        return f"It's a coin flip. Both {name_a} and {name_b} are neck-and-neck as investments right now. Go with your gut."
    elif score_a > score_b:
        if diff > 20:
            return f"{name_a} is the clear winner here. Stronger breakout score, better market position. Not close."
        else:
            return f"{name_a} has the edge — slightly better numbers and market signal. But {name_b} isn't far behind."
    else:
        if diff > 20:
            return f"{name_b} is the clear winner here. Stronger breakout score, better market position. Not close."
        else:
            return f"{name_b} has the edge — slightly better numbers and market signal. But {name_a} isn't far behind."
