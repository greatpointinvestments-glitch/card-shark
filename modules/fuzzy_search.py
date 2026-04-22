"""Fuzzy player name search — typo tolerance using rapidfuzz.

Builds a name database from:
1. Live sports APIs (NBA, MLB, NFL) — covers every active player
2. Watchlists as fallback if APIs fail
3. Pokemon watchlist (no all-players API)

Cached with Streamlit's @st.cache_data so API calls happen once per day.
"""

import streamlit as st
from rapidfuzz import fuzz, process

from data.watchlists import (
    NBA_BREAKOUT_WATCHLIST, NFL_BREAKOUT_WATCHLIST, MLB_BREAKOUT_WATCHLIST,
    LEGENDS_WATCHLIST, POKEMON_LEGENDS_WATCHLIST,
)


def _watchlist_names(sport: str) -> list[str]:
    """Fallback: get names from watchlists."""
    if sport == "NBA":
        return [p["name"] for p in NBA_BREAKOUT_WATCHLIST]
    elif sport == "NFL":
        return [p["name"] for p in NFL_BREAKOUT_WATCHLIST]
    elif sport == "MLB":
        return [p["name"] for p in MLB_BREAKOUT_WATCHLIST]
    elif sport == "Pokemon":
        return [p.get("name", p.get("player_name", "")) for p in POKEMON_LEGENDS_WATCHLIST if p.get("name") or p.get("player_name")]
    return []


@st.cache_data(ttl=86400, show_spinner=False)
def _fetch_nba_players() -> list[str]:
    """Fetch all active NBA player names from nba_api."""
    try:
        from nba_api.stats.static import players
        active = players.get_active_players()
        return [p["full_name"] for p in active]
    except Exception:
        return _watchlist_names("NBA")


@st.cache_data(ttl=86400, show_spinner=False)
def _fetch_mlb_players() -> list[str]:
    """Fetch all active MLB player names from MLB Stats API."""
    try:
        import requests
        from datetime import datetime
        season = datetime.now().year
        url = f"https://statsapi.mlb.com/api/v1/sports/1/players?season={season}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return [p["fullName"] for p in data.get("people", [])]
    except Exception:
        return _watchlist_names("MLB")


@st.cache_data(ttl=86400, show_spinner=False)
def _fetch_nfl_players() -> list[str]:
    """Fetch NFL player names from ESPN teams/roster API."""
    try:
        import requests
        from concurrent.futures import ThreadPoolExecutor

        # Get all team IDs first
        teams_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"
        resp = requests.get(teams_url, timeout=10)
        resp.raise_for_status()
        teams = resp.json().get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])
        team_ids = [t["team"]["id"] for t in teams]

        def _get_roster(team_id):
            try:
                url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/roster"
                r = requests.get(url, timeout=8)
                r.raise_for_status()
                names = []
                for group in r.json().get("athletes", []):
                    for athlete in group.get("items", []):
                        name = athlete.get("fullName", "")
                        if name:
                            names.append(name)
                return names
            except Exception:
                return []

        all_names = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(_get_roster, team_ids))
        for names in results:
            all_names.extend(names)
        return all_names if all_names else _watchlist_names("NFL")
    except Exception:
        return _watchlist_names("NFL")


def _build_name_db() -> dict[str, list[str]]:
    """Build sport -> [player names] database from APIs + watchlists."""
    db = {
        "NBA": _fetch_nba_players(),
        "NFL": _fetch_nfl_players(),
        "MLB": _fetch_mlb_players(),
        "Pokemon": _watchlist_names("Pokemon"),
    }

    # Add legends to all sports (they're popular search targets)
    legend_names = [p.get("name", "") for p in LEGENDS_WATCHLIST if p.get("name")]
    for sport in ("NBA", "NFL", "MLB"):
        db[sport] = list(dict.fromkeys(db[sport] + legend_names))

    # Deduplicate each sport
    for sport in db:
        db[sport] = list(dict.fromkeys(db[sport]))

    return db


def _get_name_db() -> dict[str, list[str]]:
    """Get or build the name database. Uses session state to avoid rebuilding."""
    if "fuzzy_name_db" not in st.session_state:
        st.session_state.fuzzy_name_db = _build_name_db()
    return st.session_state.fuzzy_name_db


def _get_all_names() -> list[str]:
    """Get all player names across all sports."""
    db = _get_name_db()
    return list(dict.fromkeys(
        name for names in db.values() for name in names
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

    db = _get_name_db()
    all_names = _get_all_names()
    pool = db.get(sport, all_names) if sport else all_names
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
    db = _get_name_db()
    all_names = _get_all_names()
    pool = db.get(sport, all_names) if sport else all_names
    query_lower = query.lower().strip()
    return any(name.lower() == query_lower for name in pool)
