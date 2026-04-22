"""Fuzzy player name search — typo tolerance using rapidfuzz.

Builds a name database from existing watchlists and provides "Did you mean:"
suggestions when a search query doesn't exactly match.
"""

from rapidfuzz import fuzz, process

from data.watchlists import (
    NBA_BREAKOUT_WATCHLIST, NFL_BREAKOUT_WATCHLIST, MLB_BREAKOUT_WATCHLIST,
    LEGENDS_WATCHLIST, POKEMON_LEGENDS_WATCHLIST,
)


def _build_name_db() -> dict[str, list[str]]:
    """Build a sport -> [player names] database from all watchlists."""
    db = {
        "NBA": [],
        "NFL": [],
        "MLB": [],
        "Pokemon": [],
    }

    for p in NBA_BREAKOUT_WATCHLIST:
        db["NBA"].append(p["name"])
    for p in NFL_BREAKOUT_WATCHLIST:
        db["NFL"].append(p["name"])
    for p in MLB_BREAKOUT_WATCHLIST:
        db["MLB"].append(p["name"])
    for p in POKEMON_LEGENDS_WATCHLIST:
        name = p.get("name", p.get("player_name", ""))
        if name:
            db["Pokemon"].append(name)
    for p in LEGENDS_WATCHLIST:
        # Legends span sports — add to all sports
        name = p.get("name", "")
        if name:
            for sport in ("NBA", "NFL", "MLB"):
                db[sport].append(name)

    # Deduplicate
    for sport in db:
        db[sport] = list(dict.fromkeys(db[sport]))

    return db


_NAME_DB = _build_name_db()
_ALL_NAMES = list(dict.fromkeys(
    name for names in _NAME_DB.values() for name in names
))


def suggest_players(
    query: str,
    sport: str | None = None,
    limit: int = 5,
    min_score: int = 50,
) -> list[dict]:
    """Return fuzzy-matched player suggestions for a query.

    Args:
        query: The user's search input.
        sport: Optionally filter to a specific sport's player pool.
        limit: Max suggestions to return.
        min_score: Minimum match score (0-100) to include.

    Returns:
        List of {"name": str, "score": int} dicts, sorted by score descending.
    """
    if not query or len(query) < 2:
        return []

    pool = _NAME_DB.get(sport, _ALL_NAMES) if sport else _ALL_NAMES
    if not pool:
        return []

    results = process.extract(
        query,
        pool,
        scorer=fuzz.token_sort_ratio,
        limit=limit,
    )

    suggestions = []
    for name, score, _idx in results:
        if score >= min_score and name.lower() != query.lower():
            suggestions.append({"name": name, "score": int(score)})

    return suggestions


def has_exact_match(query: str, sport: str | None = None) -> bool:
    """Return True if the query exactly matches a known player name (case-insensitive)."""
    pool = _NAME_DB.get(sport, _ALL_NAMES) if sport else _ALL_NAMES
    query_lower = query.lower().strip()
    return any(name.lower() == query_lower for name in pool)
