"""Trend Indicators — market trend arrows for the Breakout Leaderboard."""

import streamlit as st
from modules.ebay_search import search_ebay_cards, search_ebay_sold, get_market_summary


@st.cache_data(ttl=900)
def get_leaderboard_trends(player_names: tuple, sport: str, max_players: int = 10) -> dict:
    """Fetch market trends for top leaderboard players.

    Parameters
    ----------
    player_names : tuple of str
        Tuple (for caching) of player names from the leaderboard.
    sport : str
        NBA / NFL / MLB.
    max_players : int
        Only fetch trends for this many players (ranked by position).

    Returns
    -------
    dict of {player_name: {"trend": str, "delta": float}}
    """
    trends = {}

    for name in player_names[:max_players]:
        try:
            active = search_ebay_cards(name, sport, "Rookie", limit=20)
            sold = search_ebay_sold(name, sport, "Rookie", limit=20)
            summary = get_market_summary(active or [], sold or [])

            delta = summary.get("trend_delta", 0.0)
            if delta > 5:
                trend = "Rising"
            elif delta < -5:
                trend = "Falling"
            else:
                trend = "Stable"

            trends[name] = {"trend": trend, "delta": delta}
        except Exception:
            trends[name] = {"trend": "Stable", "delta": 0.0}

    return trends


def trend_indicator(trend: str, delta: float) -> str:
    """Return an HTML snippet with a colored trend arrow and delta percentage.

    - Rising (>5%): green up triangle
    - Falling (<-5%): red down triangle
    - Stable: gray dash
    """
    if trend == "Rising":
        return f'<span style="color:#22c55e;font-weight:bold">▲ {delta:+.1f}%</span>'
    elif trend == "Falling":
        return f'<span style="color:#ef4444;font-weight:bold">▼ {delta:+.1f}%</span>'
    else:
        return '<span style="color:#6b7280;font-weight:bold">— Stable</span>'
