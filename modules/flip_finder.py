"""Flip Finder — arbitrage scanner for BIN listings below recent sold prices.

Quality rules enforced (this is where trust lives):
- Never compare a listing to comps of a different parallel/variation
- Never compare raw to graded (and vice versa)
- Never compare rookies to non-rookies
- Drop listings with suspect titles (reprint, custom, damaged, lot, etc.)
- Drop sellers below reputation bar (< 98% feedback or < 25 transactions)
- Drop flips with too few matched comps (< 3 same-variation sales)
- Attach a confidence score + label to every flip so users can filter
"""

import statistics

import streamlit as st

from modules.breakout_engine import build_leaderboard
from modules.ebay_search import search_ebay_cards, search_ebay_sold
from modules.listing_quality import (
    is_suspect, listings_match, confidence_score, confidence_label,
    extract_parallel, is_graded, is_rookie, extract_grade,
)
from data.watchlists import (
    NBA_BREAKOUT_WATCHLIST,
    NFL_BREAKOUT_WATCHLIST,
    MLB_BREAKOUT_WATCHLIST,
)

_WATCHLISTS = {
    "NBA": NBA_BREAKOUT_WATCHLIST,
    "NFL": NFL_BREAKOUT_WATCHLIST,
    "MLB": MLB_BREAKOUT_WATCHLIST,
}

# Minimum seller bar — below this, a listing never qualifies as a flip
_MIN_SELLER_FEEDBACK_PCT = 98.0
_MIN_SELLER_FEEDBACK_COUNT = 25
# Minimum matched comp volume for a flip to be shown at all
_MIN_MATCHED_COMPS = 3


def _seller_passes(listing: dict) -> bool:
    pct = listing.get("seller_feedback_pct")
    count = listing.get("seller_feedback_count")
    # If eBay didn't return seller data at all:
    # - Demo/fallback mode (DEMO- prefix item_id) → allow through
    # - Live mode → reject (unknown seller = cautious)
    if pct is None and count is None:
        return str(listing.get("item_id", "")).startswith("DEMO")
    if pct is None:
        pct = 100.0
    if count is None:
        count = 100
    return pct >= _MIN_SELLER_FEEDBACK_PCT and count >= _MIN_SELLER_FEEDBACK_COUNT


def _matched_comps_for(listing_title: str, sold: list[dict]) -> list[dict]:
    """Return the sold comps that genuinely match the listing's variation/rookie/grade."""
    return [s for s in sold if listings_match(listing_title, s.get("title", ""))]


def _trim_outliers(prices: list[float]) -> list[float]:
    """Drop the top 10% and bottom 10% of prices to neutralize shill/error sales.
    Only trims when we have 5+ comps — below that, every point is signal."""
    if len(prices) < 5:
        return prices
    sorted_prices = sorted(prices)
    k = max(1, len(sorted_prices) // 10)
    return sorted_prices[k:-k]


@st.cache_data(ttl=600)
def find_flip_opportunities(
    sports: list[str],
    card_type: str = "Rookie",
    max_players_per_sport: int = 5,
    max_results: int = 20,
    min_confidence: int = 60,
) -> list[dict]:
    """Find active BIN listings priced below same-variation sold comps.

    Parameters
    ----------
    sports : list of sport names ("NBA", "NFL", "MLB")
    card_type : eBay card type filter
    max_players_per_sport : top N players per sport to scan
    max_results : max flip opportunities to return
    min_confidence : 0-100 — drop flips with confidence below this threshold

    Returns
    -------
    list of dicts sorted by confidence-weighted spread descending, each with:
        player, sport, title, active_price, avg_sold, median_sold,
        spread, spread_pct, url, image_url, matched_comps, parallel, grade,
        seller_feedback_pct, seller_feedback_count, confidence, confidence_label
    """
    flips = []

    for sport in sports:
        watchlist = _WATCHLISTS.get(sport)
        if not watchlist:
            continue

        leaderboard = build_leaderboard(watchlist, sport)
        top_players = [p["name"] for p in leaderboard[:max_players_per_sport]]

        for player_name in top_players:
            active = search_ebay_cards(player_name, sport, card_type, limit=20)
            sold = search_ebay_sold(player_name, sport, card_type, limit=40)

            if not sold or not active:
                continue

            # Filter suspect comps up-front too — a reprint sale shouldn't drag the median
            clean_sold = [s for s in sold if not is_suspect(s.get("title", ""))]
            if not clean_sold:
                continue

            # Only consider BIN, non-suspect active listings from reputable sellers
            candidates = [
                l for l in active
                if l.get("buying_format") == "BIN"
                and l.get("total", 0) > 0
                and not is_suspect(l.get("title", ""))
                and _seller_passes(l)
            ]

            for listing in candidates:
                matched = _matched_comps_for(listing["title"], clean_sold)
                matched_prices = [m["total"] for m in matched if m.get("total", 0) >= 1.00]

                if len(matched_prices) < _MIN_MATCHED_COMPS:
                    continue

                # Trim outliers (shill sales, typo prices) before computing median
                trimmed_prices = _trim_outliers(matched_prices)
                avg_sold = sum(trimmed_prices) / len(trimmed_prices)
                median_sold = statistics.median(trimmed_prices)
                active_price = listing["total"]

                # Use median as anchor — robust to outliers
                if active_price >= median_sold:
                    continue

                spread = median_sold - active_price
                spread_pct = (spread / active_price * 100) if active_price > 0 else 0

                score = confidence_score(
                    listing,
                    matched_comp_count=len(matched_prices),
                    seller_feedback_pct=listing.get("seller_feedback_pct"),
                    seller_feedback_count=listing.get("seller_feedback_count"),
                )

                if score < min_confidence:
                    continue

                flips.append({
                    "player": player_name,
                    "sport": sport,
                    "title": listing["title"],
                    "active_price": round(active_price, 2),
                    "avg_sold": round(avg_sold, 2),
                    "median_sold": round(median_sold, 2),
                    "spread": round(spread, 2),
                    "spread_pct": round(spread_pct, 1),
                    "url": listing["url"],
                    "image_url": listing.get("image_url", ""),
                    "matched_comps": len(matched_prices),
                    "parallel": extract_parallel(listing["title"]),
                    "is_graded": is_graded(listing["title"]),
                    "grade": extract_grade(listing["title"]),
                    "is_rookie": is_rookie(listing["title"]),
                    "seller_feedback_pct": listing.get("seller_feedback_pct"),
                    "seller_feedback_count": listing.get("seller_feedback_count"),
                    "confidence": score,
                    "confidence_label": confidence_label(score),
                })

    # Sort by confidence-weighted spread so high-confidence flips win ties
    flips.sort(key=lambda x: (x["confidence"] / 100.0) * x["spread_pct"], reverse=True)
    return flips[:max_results]
