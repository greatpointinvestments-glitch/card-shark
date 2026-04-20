"""Trade Checker — evaluate multi-card trades using eBay market data."""

from modules.ebay_search import search_ebay_cards, search_ebay_sold, get_market_summary, flag_deals
from modules.pokemon_tcg import search_pokemon_cards, get_pokemon_market_price, get_pokemon_market_summary
from data.watchlists import NBA_BREAKOUT_WATCHLIST, NFL_BREAKOUT_WATCHLIST, MLB_BREAKOUT_WATCHLIST


# Players on any breakout watchlist get an upside bonus
_BREAKOUT_NAMES = {p["name"].lower() for wl in (NBA_BREAKOUT_WATCHLIST, NFL_BREAKOUT_WATCHLIST, MLB_BREAKOUT_WATCHLIST) for p in wl}


def get_card_market_value(
    player_name: str,
    sport: str,
    card_type: str,
    year: str | None = None,
    set_name: str | None = None,
) -> dict:
    """Look up a card's market value using eBay (sports) or Pokemon TCG API.

    Optional year and set_name narrow the search for more accurate pricing.

    Returns dict with: avg_sold, avg_active, sold_volume, price_trend,
    trend_delta, market_signal, on_breakout_watchlist.
    """
    result = {
        "player": player_name,
        "sport": sport,
        "card_type": card_type,
        "avg_sold": 0,
        "avg_active": 0,
        "sold_volume": 0,
        "price_trend": "Stable",
        "trend_delta": 0,
        "market_signal": "FAIR VALUE",
        "on_breakout_watchlist": player_name.lower() in _BREAKOUT_NAMES,
    }

    if sport == "Pokemon":
        cards = search_pokemon_cards(player_name, set_name=set_name)
        if cards:
            summary = get_pokemon_market_summary(cards)
            result.update({
                "avg_sold": summary["avg_sold"],
                "avg_active": summary["avg_active"],
                "sold_volume": summary["sold_volume"],
                "price_trend": summary["price_trend"],
                "trend_delta": summary["trend_delta"],
                "market_signal": summary["market_signal"],
            })
        return result

    listings = search_ebay_cards(player_name, sport, card_type, limit=30,
                                 year=year, set_name=set_name)
    listings = flag_deals(listings)
    sold = search_ebay_sold(player_name, sport, card_type, limit=30,
                            year=year, set_name=set_name)

    if listings or sold:
        summary = get_market_summary(listings or [], sold or [])
        result.update({
            "avg_sold": summary["avg_sold"],
            "avg_active": summary["avg_active"],
            "sold_volume": summary["sold_volume"],
            "price_trend": summary["price_trend"],
            "trend_delta": summary["trend_delta"],
            "market_signal": summary["market_signal"],
        })

    return result


def compute_trade_grade(giving_cards: list[dict], getting_cards: list[dict]) -> dict:
    """Grade a trade from your perspective.

    Each card dict: {player, sport, card_type, value (float — manual or from market)}

    Returns: {grade, verdict, your_total, their_total, diff_pct, cards_detail}
    """
    your_total = sum(c.get("value", 0) for c in giving_cards)
    their_total = sum(c.get("value", 0) for c in getting_cards)

    # Upside bonus: cards on breakout watchlist get 10% bump on the receiving side
    breakout_bonus = 0
    for card in getting_cards:
        if card.get("on_breakout_watchlist"):
            breakout_bonus += card.get("value", 0) * 0.10

    adjusted_their_total = their_total + breakout_bonus

    # Calculate difference as percentage of your side
    if your_total > 0:
        diff_pct = round((adjusted_their_total - your_total) / your_total * 100, 1)
    elif adjusted_their_total > 0:
        diff_pct = 100.0  # Getting something for nothing
    else:
        diff_pct = 0.0

    # Assign grade
    if diff_pct >= 20:
        grade, verdict = "A", "You're robbing them. Accept this NOW."
    elif diff_pct >= 10:
        grade, verdict = "B", "Solid W. You're getting the better end."
    elif diff_pct >= -5:
        grade, verdict = "C", "Fair trade. Nobody's getting fleeced."
    elif diff_pct >= -15:
        grade, verdict = "D", "Eh, you're giving up a little too much."
    else:
        grade, verdict = "F", "Hard pass. You're getting cooked."

    return {
        "grade": grade,
        "verdict": verdict,
        "your_total": round(your_total, 2),
        "their_total": round(their_total, 2),
        "adjusted_their_total": round(adjusted_their_total, 2),
        "diff_pct": diff_pct,
        "breakout_bonus": round(breakout_bonus, 2),
    }
