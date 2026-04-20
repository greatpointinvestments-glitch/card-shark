"""Breakout scoring algorithm for young active players."""

from config.settings import BREAKOUT_WEIGHTS, SIGNAL_BUY, SIGNAL_WATCH
from modules.player_stats import search_players, get_multi_season_stats
from modules.ebay_search import search_ebay_cards


def compute_breakout_score(player_info: dict, stats: list[dict], ebay_listings: list[dict]) -> dict:
    """
    Compute a 0-100 breakout score for a young player.

    Components:
      - trajectory (30%): YoY stat improvement
      - usage (20%): minutes/games trend
      - age (15%): younger = higher
      - draft (15%): high picks delivering = narrative power
      - market (20%): eBay listing count + median price (many listings + low price = buy window)
    """
    trajectory = _score_trajectory(stats)
    usage = _score_usage(stats)
    age = _score_age(player_info.get("age", 25))
    draft = _score_draft(player_info.get("draft_pick", 60))
    market = _score_market(ebay_listings)

    total = (
        trajectory * BREAKOUT_WEIGHTS["trajectory"]
        + usage * BREAKOUT_WEIGHTS["usage"]
        + age * BREAKOUT_WEIGHTS["age"]
        + draft * BREAKOUT_WEIGHTS["draft"]
        + market * BREAKOUT_WEIGHTS["market"]
    )

    score = round(min(100, max(0, total)), 1)

    if score >= SIGNAL_BUY:
        signal = "BUY"
    elif score >= SIGNAL_WATCH:
        signal = "WATCH"
    else:
        signal = "HOLD"

    return {
        "score": score,
        "signal": signal,
        "trajectory": round(trajectory, 1),
        "usage": round(usage, 1),
        "age_score": round(age, 1),
        "draft_score": round(draft, 1),
        "market_score": round(market, 1),
    }


def _score_trajectory(stats: list[dict]) -> float:
    """Score 0-100 based on year-over-year stat improvement."""
    if len(stats) < 2:
        return 50.0  # Rookies get neutral score

    # Look at pts improvement (NBA primary)
    key = "pts"
    values = [s.get(key, 0) for s in stats if s.get(key) is not None]
    if len(values) < 2:
        return 50.0

    # Calculate improvement percentage from first to last
    first, last = values[0], values[-1]
    if first <= 0:
        return 60.0 if last > 0 else 40.0

    pct_change = (last - first) / first * 100

    # Map: -20% or worse = 20, 0% = 50, +30% = 80, +50%+ = 95
    if pct_change >= 50:
        return 95.0
    elif pct_change >= 30:
        return 80.0
    elif pct_change >= 10:
        return 65.0
    elif pct_change >= 0:
        return 50.0
    elif pct_change >= -20:
        return 35.0
    else:
        return 20.0


def _score_usage(stats: list[dict]) -> float:
    """Score 0-100 based on minutes/games trend."""
    if not stats:
        return 50.0

    # Use minutes played as usage proxy
    minutes = [s.get("min", 0) for s in stats]
    # min can come as string "32:10" or float
    parsed = []
    for m in minutes:
        if isinstance(m, str) and ":" in m:
            parts = m.split(":")
            parsed.append(float(parts[0]) + float(parts[1]) / 60)
        elif m:
            try:
                parsed.append(float(m))
            except (ValueError, TypeError):
                pass

    if not parsed:
        return 50.0

    latest = parsed[-1]
    # 30+ min = great usage, 20-30 = good, <20 = limited
    if latest >= 32:
        return 90.0
    elif latest >= 28:
        return 75.0
    elif latest >= 24:
        return 60.0
    elif latest >= 18:
        return 45.0
    else:
        return 30.0


def _score_age(age: int) -> float:
    """Score 0-100 — younger is better for breakout potential."""
    if age <= 19:
        return 95.0
    elif age <= 20:
        return 90.0
    elif age <= 21:
        return 80.0
    elif age <= 22:
        return 70.0
    elif age <= 23:
        return 55.0
    elif age <= 24:
        return 40.0
    else:
        return 25.0


def _score_draft(pick: int) -> float:
    """Score 0-100 based on draft position (narrative value)."""
    if pick is None:
        return 30.0
    if pick <= 3:
        return 95.0
    elif pick <= 7:
        return 80.0
    elif pick <= 14:
        return 65.0
    elif pick <= 30:
        return 50.0
    elif pick <= 45:
        return 35.0
    else:
        return 20.0


def _score_market(listings: list[dict]) -> float:
    """
    Score 0-100 based on eBay market activity.
    High listing count + low median price = buy window (high score).
    Low listings + high price = already hyped (lower score).
    """
    if not listings:
        return 50.0  # No data — neutral

    count = len(listings)
    # Exclude no-bid auctions from price calculations
    prices = [
        l["total"] for l in listings
        if l.get("total", 0) > 0
        and not (l.get("buying_format") == "Auction" and l.get("bid_count", 0) == 0)
    ]

    if not prices:
        return 50.0

    median = sorted(prices)[len(prices) // 2]

    # Many listings + low price = buy window
    # Cap count_score at 70 when fewer than 10 listings to prevent inflated signals
    count_score = min(100, count * 2.5)  # 40 listings = 100
    if count < 10:
        count_score = min(count_score, 70)

    # Low price = more upside (invert: $5 = great, $50 = ok, $200+ = expensive)
    if median <= 5:
        price_score = 90
    elif median <= 15:
        price_score = 75
    elif median <= 40:
        price_score = 60
    elif median <= 100:
        price_score = 40
    else:
        price_score = 20

    return count_score * 0.5 + price_score * 0.5


def build_leaderboard(watchlist: list[dict], sport: str = "NBA") -> list[dict]:
    """
    Build a ranked breakout leaderboard from a watchlist.
    This uses hardcoded player data without API calls for fast loading.
    API-enriched scores are computed on-demand when a player is selected.
    """
    results = []
    for player in watchlist:
        # Quick score from hardcoded data only (no API calls)
        age_score = _score_age(player.get("age", 25))
        draft_score = _score_draft(player.get("draft_pick", 60))

        # Estimate trajectory from seasons played
        seasons = player.get("seasons", 1)
        if seasons == 1:
            trajectory = 55.0  # Rookie — unknown
        elif seasons == 2:
            trajectory = 60.0  # Sophomore — slight bump
        else:
            trajectory = 50.0

        # Rough composite without live data
        quick_score = round(
            trajectory * 0.35
            + age_score * 0.30
            + draft_score * 0.35,
            1,
        )

        if quick_score >= SIGNAL_BUY:
            signal = "BUY"
        elif quick_score >= SIGNAL_WATCH:
            signal = "WATCH"
        else:
            signal = "HOLD"

        results.append({
            "name": player["name"],
            "team": player["team"],
            "age": player["age"],
            "draft_pick": player.get("draft_pick", "N/A"),
            "seasons": player.get("seasons", 1),
            "score": quick_score,
            "signal": signal,
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    for i, r in enumerate(results):
        r["rank"] = i + 1

    return results
