"""Market Movers — biggest weekly price gainers and losers."""

from data.demo_price_history import generate_demo_price_history


def _compute_weekly_change(player: str, sport: str, card_type: str = "Any") -> tuple:
    """Compute weekly price change from demo history.

    Returns (current_avg, prev_avg, change_pct).
    """
    history = generate_demo_price_history(player, sport, card_type, days=14)
    if len(history) < 8:
        return (0, 0, 0)

    # Current week = last 7 days, previous week = 7 days before that
    current_week = history[-7:]
    prev_week = history[-14:-7]

    current_avg = sum(h["price"] for h in current_week) / len(current_week)
    prev_avg = sum(h["price"] for h in prev_week) / len(prev_week)

    change_pct = ((current_avg - prev_avg) / prev_avg * 100) if prev_avg > 0 else 0

    return (round(current_avg, 2), round(prev_avg, 2), round(change_pct, 1))


def compute_market_movers(
    watchlist_data: list[dict],
    max_players: int = 10,
) -> dict:
    """Compute top gainers and losers from watchlist data.

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
        current_avg, prev_avg, change_pct = _compute_weekly_change(name, sport)

        if current_avg > 0:
            movers.append({
                "name": name,
                "sport": sport,
                "current_price": current_avg,
                "prev_price": prev_avg,
                "change_pct": change_pct,
            })

    # Sort by change percentage
    movers.sort(key=lambda x: x["change_pct"], reverse=True)

    gainers = [m for m in movers if m["change_pct"] > 0][:max_players]
    losers = [m for m in movers if m["change_pct"] < 0]
    losers.sort(key=lambda x: x["change_pct"])
    losers = losers[:max_players]

    return {"gainers": gainers, "losers": losers}
