"""Retired player investment scoring and analysis."""

from config.settings import LEGEND_WEIGHTS


def compute_legend_score(player: dict) -> dict:
    """
    Compute a 0-100 investment score for a retired legend.

    Components:
      - hof_legacy (30%): HOF status + career significance
      - iconic_card (25%): How iconic their key cards are
      - market_value (25%): Are they underpriced vs. significance?
      - cultural (20%): Cultural relevance today
    """
    hof = _score_hof(player)
    iconic = _score_iconic_card(player)
    market = _score_market_value(player)
    cultural = _score_cultural(player)

    total = (
        hof * LEGEND_WEIGHTS["hof_legacy"]
        + iconic * LEGEND_WEIGHTS["iconic_card"]
        + market * LEGEND_WEIGHTS["market_value"]
        + cultural * LEGEND_WEIGHTS["cultural"]
    )

    score = round(min(100, max(0, total)), 1)

    if score >= 80:
        rating = "STRONG BUY"
    elif score >= 65:
        rating = "BUY"
    elif score >= 50:
        rating = "HOLD"
    else:
        rating = "PASS"

    return {
        "score": score,
        "rating": rating,
        "hof_score": round(hof, 1),
        "iconic_score": round(iconic, 1),
        "market_score": round(market, 1),
        "cultural_score": round(cultural, 1),
    }


def _score_hof(player: dict) -> float:
    """Score based on HOF status and career significance."""
    base = 80.0 if player.get("hof") else 50.0
    significance = player.get("significance", 5)
    return min(100, base + (significance - 5) * 4)


def _score_iconic_card(player: dict) -> float:
    """Score based on how iconic their key cards are."""
    cards = player.get("iconic_cards", [])
    if not cards:
        return 30.0

    # More iconic cards = higher score, capped at 3
    card_count = min(len(cards), 3)
    base = 50.0 + card_count * 15

    # Bonus for classic sets mentioned in card names
    classic_keywords = ["fleer", "topps chrome", "upper deck", "bowman chrome", "sp"]
    for card in cards:
        lower = card.lower()
        for kw in classic_keywords:
            if kw in lower:
                base += 5
                break

    return min(100, base)


def _score_market_value(player: dict) -> float:
    """
    Score how undervalued the player's cards are vs. significance.
    High significance + low perceived price = high score (opportunity).
    """
    significance = player.get("significance", 5)

    # Players with significance 8+ but cultural_score < 8 are likely undervalued
    cultural = player.get("cultural_score", 5)
    gap = significance - cultural

    base = 50.0 + gap * 10

    # Extra bonus for significance 9-10 (these should always be worth owning)
    if significance >= 9:
        base += 10

    return min(100, max(20, base))


def _score_cultural(player: dict) -> float:
    """Score based on current cultural relevance."""
    return min(100, player.get("cultural_score", 5) * 10)


def build_legends_table(watchlist: list[dict]) -> list[dict]:
    """Build a scored and ranked table from the legends watchlist."""
    results = []
    for player in watchlist:
        scores = compute_legend_score(player)
        results.append({
            "name": player["name"],
            "sport": player["sport"],
            "hof": "HOF" if player.get("hof") else "Active/Eligible",
            "iconic_cards": ", ".join(player.get("iconic_cards", [])),
            "notes": player.get("notes", ""),
            **scores,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1

    return results


def get_hidden_gems(legends_table: list[dict], top_n: int = 10) -> list[dict]:
    """
    Find 'hidden gems' — players whose market_score is high
    (meaning underpriced vs. significance) and overall score is decent.
    """
    gems = [p for p in legends_table if p["market_score"] >= 60 and p["score"] >= 55]
    gems.sort(key=lambda x: x["market_score"], reverse=True)
    return gems[:top_n]
