"""Card of the Day — algorithmically-picked undervalued card, refreshes daily.

Uses the same quality-filtered pipeline as Flip Finder so the pick is always
apples-to-apples: same variation, same grading status, seller-vetted, with
enough matched comps to trust the signal.
"""

import hashlib
from datetime import date

import streamlit as st

from modules.flip_finder import find_flip_opportunities


@st.cache_data(ttl=86400)
def get_card_of_the_day() -> dict | None:
    """Pick one undervalued card per day, deterministically.

    Returns a dict with the same shape the UI expects:
        player_name, sport, source, listing (best deal), summary (market),
        why (explanation string), image_url.
    """
    # Run the full Flip Finder with a medium confidence bar — these are real flips
    flips = find_flip_opportunities(
        sports=["NBA", "NFL", "MLB"],
        card_type="Any",
        max_players_per_sport=8,
        max_results=30,
        min_confidence=60,
    )

    if not flips:
        return None

    # Deterministic daily pick from today's date so everyone sees the same one
    seed = int(hashlib.md5(str(date.today()).encode()).hexdigest(), 16)
    pick = flips[seed % len(flips)]

    # Build the legacy listing/summary shape the UI uses
    listing = {
        "title": pick["title"],
        "total": pick["active_price"],
        "url": pick["url"],
        "image_url": pick["image_url"],
        "vs_median": -pick["spread_pct"],  # negative = below median
    }
    summary = {
        "avg_sold": pick["median_sold"],
        "sold_volume": pick["matched_comps"],
        "avg_active": pick["active_price"],
        "price_trend": "Stable",
        "trend_delta": 0,
        "market_signal": "BUY WINDOW" if pick["spread_pct"] >= 10 else "FAIR VALUE",
        "active_vs_sold_pct": -pick["spread_pct"],
    }

    parallel = pick.get("parallel", "base").replace("_", " ").title()
    grade = pick.get("grade") or ("Raw" if not pick.get("is_graded") else "Graded")
    why = (
        f"Priced {pick['spread_pct']:.0f}% below the median of {pick['matched_comps']} "
        f"recent sales of the same {parallel} {grade} card. "
        f"{pick.get('confidence_label', 'Medium')} confidence."
    )

    return {
        "player_name": pick["player"],
        "sport": pick["sport"],
        "source": "Breakout" if pick["sport"] in ("NBA", "NFL", "MLB") else "Legend",
        "listing": listing,
        "summary": summary,
        "why": why,
        "image_url": pick["image_url"],
    }
