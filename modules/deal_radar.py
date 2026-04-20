"""Deal Radar — cached deal scanner for the homepage.

Uses the same quality-filtered pipeline as Flip Finder. No more raw-vs-graded
or base-vs-refractor false steals.
"""

import streamlit as st

from modules.flip_finder import find_flip_opportunities


@st.cache_data(ttl=600)
def get_top_deals(watchlist_data: tuple, max_players_per_sport: int = 5, max_deals: int = 8) -> list[dict]:
    """Scan top breakout players for high-confidence flip deals.

    Parameters
    ----------
    watchlist_data : tuple (kept for caching signature compatibility — unused)
    max_players_per_sport : how deep into each sport's leaderboard to scan
    max_deals : cap on deals returned
    """
    flips = find_flip_opportunities(
        sports=["NBA", "NFL", "MLB"],
        card_type="Any",
        max_players_per_sport=max_players_per_sport,
        max_results=max_deals * 2,
        min_confidence=60,
    )

    deals = []
    for f in flips[:max_deals]:
        deals.append({
            "player": f["player"],
            "sport": f["sport"],
            "title": f["title"],
            "price": f["active_price"],
            "total": f["active_price"],
            "vs_median": -f["spread_pct"],  # negative = below median
            "url": f["url"],
            "image_url": f["image_url"],
            "buying_format": "BIN",
            "confidence": f.get("confidence", 0),
            "confidence_label": f.get("confidence_label", "Medium"),
            "matched_comps": f.get("matched_comps", 0),
            "parallel": f.get("parallel", "base"),
            "is_graded": f.get("is_graded", False),
            "grade": f.get("grade"),
        })
    return deals


def prepare_watchlist_data(watchlists: dict) -> tuple:
    """Kept for caching signature. No longer used internally."""
    result = []
    for sport, wl in watchlists.items():
        wl_tuples = tuple(tuple(sorted(p.items())) for p in wl)
        result.append((sport, wl_tuples))
    return tuple(result)
