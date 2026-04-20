"""Collection Insights — set completion, rarity, projections, diversification."""

from datetime import datetime, timedelta


def compute_set_completion(portfolio: list[dict]) -> list[dict]:
    """Group portfolio by year+set_name and show completion percentage.

    Returns list of dicts with set_key, count, estimated_total, completion_pct.
    """
    set_groups: dict[str, int] = {}

    for card in portfolio:
        year = card.get("year", "Unknown")
        set_name = card.get("set_name", card.get("card_type", "Unknown"))
        sport = card.get("sport", "")
        key = f"{year} {set_name} ({sport})"
        set_groups[key] = set_groups.get(key, 0) + card.get("quantity", 1)

    results = []
    for set_key, count in sorted(set_groups.items()):
        # Estimated set size: typical card sets have 200-400 cards
        estimated_total = 300
        completion_pct = min(round(count / estimated_total * 100, 1), 100)
        results.append({
            "set_key": set_key,
            "count": count,
            "estimated_total": estimated_total,
            "completion_pct": completion_pct,
        })

    return results


def compute_rarity_distribution(portfolio: list[dict]) -> dict:
    """Count cards by card_type for pie chart data."""
    dist: dict[str, int] = {}
    for card in portfolio:
        ct = card.get("card_type", "Other")
        qty = card.get("quantity", 1)
        dist[ct] = dist.get(ct, 0) + qty
    return dist


def compute_investment_timeline(portfolio: list[dict]) -> list[dict]:
    """Compute cumulative spend over time sorted by purchase date.

    Returns list of dicts with date, cumulative_spent.
    """
    dated_spends = []
    for card in portfolio:
        date_str = card.get("purchase_date", "")
        if date_str:
            cost = card["purchase_price"] * card.get("quantity", 1)
            dated_spends.append((date_str, cost))

    if not dated_spends:
        return []

    dated_spends.sort(key=lambda x: x[0])
    cumulative = 0
    timeline = []
    for date_str, cost in dated_spends:
        cumulative += cost
        timeline.append({"date": date_str, "cumulative_spent": round(cumulative, 2)})

    return timeline


def compute_projected_value(
    portfolio: list[dict],
    market_values: dict,
    growth_rate: float = 0.10,
    months: int = 12,
) -> dict:
    """Project portfolio value at a given annual growth rate.

    Parameters
    ----------
    portfolio : card list
    market_values : card_id -> current market value
    growth_rate : annual growth rate (0.10 = 10%)
    months : projection horizon

    Returns dict with current_value, projected_value, projected_gain.
    """
    current_value = sum(
        market_values.get(c["id"], 0) * c.get("quantity", 1) for c in portfolio
    )

    # Compound monthly
    monthly_rate = (1 + growth_rate) ** (1 / 12) - 1
    projected_value = current_value * (1 + monthly_rate) ** months

    return {
        "current_value": round(current_value, 2),
        "projected_value": round(projected_value, 2),
        "projected_gain": round(projected_value - current_value, 2),
        "growth_rate": growth_rate,
        "months": months,
    }


def compute_diversification_score(portfolio: list[dict]) -> dict:
    """Score portfolio diversification 0-100 across sport, era, and card type.

    Returns dict with total_score, sport_score, era_score, type_score, suggestions.
    """
    if not portfolio:
        return {"total_score": 0, "sport_score": 0, "era_score": 0,
                "type_score": 0, "suggestions": ["Add cards to start building your collection"]}

    total_cards = sum(c.get("quantity", 1) for c in portfolio)

    # Sport diversity (max 35 points) — ideal is 3 sports evenly split
    sport_counts: dict[str, int] = {}
    for c in portfolio:
        s = c.get("sport", "Other")
        sport_counts[s] = sport_counts.get(s, 0) + c.get("quantity", 1)
    num_sports = len(sport_counts)
    max_share = max(sport_counts.values()) / total_cards if total_cards else 1
    sport_score = min(35, int(35 * (1 - (max_share - 1 / max(num_sports, 1)))))
    if num_sports >= 3:
        sport_score = min(35, sport_score + 10)

    # Era diversity (max 35 points) — mix of modern and vintage
    era_counts = {"modern": 0, "recent": 0, "vintage": 0}
    for c in portfolio:
        year = c.get("year", "")
        if isinstance(year, str) and year:
            try:
                y = int(year[:4])
            except ValueError:
                y = 2024
        else:
            y = 2024
        if y >= 2020:
            era_counts["modern"] += c.get("quantity", 1)
        elif y >= 2000:
            era_counts["recent"] += c.get("quantity", 1)
        else:
            era_counts["vintage"] += c.get("quantity", 1)
    eras_present = sum(1 for v in era_counts.values() if v > 0)
    era_score = min(35, eras_present * 12)

    # Card type diversity (max 30 points)
    type_counts: dict[str, int] = {}
    for c in portfolio:
        ct = c.get("card_type", "Other")
        type_counts[ct] = type_counts.get(ct, 0) + c.get("quantity", 1)
    num_types = len(type_counts)
    type_score = min(30, num_types * 6)

    total_score = sport_score + era_score + type_score

    # Suggestions
    suggestions = []
    if num_sports < 3:
        missing = [s for s in ["NBA", "NFL", "MLB"] if s not in sport_counts]
        if missing:
            suggestions.append(f"Add {missing[0]} cards for better sport diversity")
    if eras_present < 2:
        suggestions.append("Mix in some vintage/legend cards for era diversity")
    if num_types < 3:
        suggestions.append("Try different card types (Prizm, Refractor, Auto) for variety")
    if not suggestions:
        suggestions.append("Great diversification! Keep building across all dimensions.")

    return {
        "total_score": total_score,
        "sport_score": sport_score,
        "era_score": era_score,
        "type_score": type_score,
        "suggestions": suggestions,
    }
