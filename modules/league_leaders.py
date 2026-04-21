"""League leaders data — NBA, NFL, MLB stat leaders from free public APIs.

NBA: nba_api library (LeagueLeaders endpoint)
NFL: ESPN Core API (sports.core.api.espn.com) with concurrent athlete resolution
MLB: MLB Stats API (statsapi.mlb.com)
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import requests
import streamlit as st


# --- Season helpers ---
# Each sport: detect if currently in-season, return the right year/label.
# In-season  → current season, no banner
# Off-season → most recent completed season, with "(Final)" banner

# NBA: regular season Oct–Apr, playoffs Apr–Jun, offseason Jul–Sep
def is_nba_offseason() -> bool:
    return datetime.now().month in (7, 8, 9)


def get_nba_display_season() -> tuple[str, str]:
    """Return (season_string, label). Season string like '2025-26'."""
    now = datetime.now()
    if now.month >= 10:
        start = now.year
    else:
        start = now.year - 1
    end_short = str(start + 1)[-2:]
    season = f"{start}-{end_short}"
    if is_nba_offseason():
        return season, f"{start}-{start + 1} Season (Final)"
    return season, f"{start}-{start + 1} Season"


def get_current_nba_season() -> str:
    return get_nba_display_season()[0]


# MLB: regular season Apr–Oct (roughly), offseason Nov–Mar
def is_mlb_offseason() -> bool:
    return datetime.now().month in (11, 12, 1, 2, 3)


def get_mlb_display_season() -> tuple[int, str]:
    """Return (year, label)."""
    now = datetime.now()
    if is_mlb_offseason():
        # Nov–Dec: just-finished season is this year
        # Jan–Mar: just-finished season is last year
        year = now.year if now.month >= 11 else now.year - 1
        return year, f"{year} Season (Final)"
    return now.year, f"{now.year} Season"


def get_current_mlb_season() -> int:
    return get_mlb_display_season()[0]


# NFL: regular season Sep–Jan (Super Bowl early Feb), offseason Feb–Aug
def is_nfl_offseason() -> bool:
    month = datetime.now().month
    return 2 <= month <= 8


def get_nfl_display_season() -> tuple[int, str]:
    """Return (year, label). NFL season named by start year (e.g. 2025 season)."""
    now = datetime.now()
    if is_nfl_offseason():
        year = now.year - 1 if now.month <= 8 else now.year
        return year, f"{year} Season (Final)"
    else:
        year = now.year if now.month >= 9 else now.year - 1
        return year, f"{year} Season"


# --- Stat category configs ---

NBA_CATEGORIES = {
    "Points": "PTS",
    "Rebounds": "REB",
    "Assists": "AST",
    "Steals": "STL",
    "Blocks": "BLK",
}

NFL_CATEGORIES = {
    "Passing Yards": "passingYards",
    "Rushing Yards": "rushingYards",
    "Receiving Yards": "receivingYards",
    "Total Touchdowns": "totalTouchdowns",
    "Sacks": "sacks",
    "Interceptions": "interceptions",
}

# MLB categories: (api_category, statGroup) — statGroup filters hitters vs pitchers
MLB_CATEGORIES = {
    "Batting Average": ("battingAverage", "hitting"),
    "Home Runs": ("homeRuns", "hitting"),
    "RBI": ("runsBattedIn", "hitting"),
    "ERA": ("earnedRunAverage", "pitching"),
    "Strikeouts": ("strikeouts", "pitching"),
}

SPORT_CATEGORIES = {
    "NBA": NBA_CATEGORIES,
    "NFL": NFL_CATEGORIES,
    "MLB": MLB_CATEGORIES,
}


# --- NBA Leaders (nba_api) ---

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_nba_leaders(stat_category: str = "PTS", season: str = "", limit: int = 20) -> list[dict]:
    """Fetch NBA league leaders using nba_api. Returns list of dicts."""
    try:
        from nba_api.stats.endpoints import LeagueLeaders
        if not season:
            season = get_current_nba_season()
        data = LeagueLeaders(
            season=season,
            stat_category_abbreviation=stat_category,
            per_mode48="PerGame",
        )
        rows = data.get_dict()["resultSet"]["rowSet"]
        headers = data.get_dict()["resultSet"]["headers"]

        # Find column indices
        player_idx = headers.index("PLAYER") if "PLAYER" in headers else 2
        team_idx = headers.index("TEAM") if "TEAM" in headers else 4
        rank_idx = headers.index("RANK") if "RANK" in headers else 0

        # Stat value column — the stat_category maps to a column name
        stat_col = stat_category
        stat_idx = headers.index(stat_col) if stat_col in headers else len(headers) - 1

        results = []
        for row in rows[:limit]:
            results.append({
                "rank": row[rank_idx],
                "player": row[player_idx],
                "team": row[team_idx],
                "value": row[stat_idx],
            })
        return results
    except Exception:
        return []


# --- NFL Leaders (ESPN Core API) ---

def _resolve_athlete(ref_url: str) -> dict:
    """Resolve an ESPN athlete $ref URL to {name, team, position}."""
    try:
        resp = requests.get(ref_url, timeout=8)
        data = resp.json()
        # Team is also a $ref — resolve it
        team_ref = data.get("team", {}).get("$ref", "")
        team_abbr = ""
        if team_ref:
            try:
                t = requests.get(team_ref, timeout=5).json()
                team_abbr = t.get("abbreviation", "")
            except Exception:
                pass
        return {
            "name": data.get("displayName", "Unknown"),
            "team": team_abbr,
        }
    except Exception:
        return {"name": "Unknown", "team": ""}


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_nfl_leaders(season: int = 0, limit: int = 20) -> dict[str, list[dict]]:
    """Fetch NFL leaders from ESPN Core API. Returns dict of category -> list.
    Uses concurrent requests to resolve athlete $ref links."""
    try:
        if not season:
            season = get_nfl_display_season()[0]
        url = (
            f"https://sports.core.api.espn.com/v2/sports/football/"
            f"leagues/nfl/seasons/{season}/types/2/leaders"
        )
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        # Target categories we care about
        target_cats = set(NFL_CATEGORIES.values())

        # Collect all athlete refs we need to resolve
        all_refs = set()
        cat_raw = {}  # category_name -> [(value, ref_url), ...]
        for cat in data.get("categories", []):
            cat_name = cat.get("name", "")
            if cat_name not in target_cats:
                continue
            entries = []
            for leader in cat.get("leaders", [])[:limit]:
                ref = leader.get("athlete", {}).get("$ref", "")
                value = leader.get("displayValue", leader.get("value", ""))
                entries.append((value, ref))
                if ref:
                    all_refs.add(ref)
            cat_raw[cat_name] = entries

        # Batch-resolve all athlete refs concurrently
        ref_map = {}
        refs_list = list(all_refs)
        with ThreadPoolExecutor(max_workers=20) as executor:
            resolved = list(executor.map(_resolve_athlete, refs_list))
        for ref_url, athlete_data in zip(refs_list, resolved):
            ref_map[ref_url] = athlete_data

        # Build final results
        results = {}
        for cat_name, entries in cat_raw.items():
            leaders_list = []
            for i, (value, ref) in enumerate(entries):
                athlete = ref_map.get(ref, {"name": "Unknown", "team": ""})
                leaders_list.append({
                    "rank": i + 1,
                    "player": athlete["name"],
                    "team": athlete["team"],
                    "value": value,
                })
            results[cat_name] = leaders_list
        return results
    except Exception:
        return {}


# --- MLB Leaders (MLB Stats API) ---

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_mlb_leaders(season: int = 0, limit: int = 20) -> dict[str, list[dict]]:
    """Fetch MLB leaders from MLB Stats API. Returns dict keyed by 'category|statGroup'."""
    try:
        if not season:
            season = get_current_mlb_season()
        categories = ",".join(cat for cat, _group in MLB_CATEGORIES.values())
        url = (
            f"https://statsapi.mlb.com/api/v1/stats/leaders"
            f"?leaderCategories={categories}&season={season}&limit={limit}"
        )
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = {}
        for cat_data in data.get("leagueLeaders", []):
            cat_name = cat_data.get("leaderCategory", "")
            stat_group = cat_data.get("statGroup", "")
            leaders_list = []
            for leader in cat_data.get("leaders", [])[:limit]:
                person = leader.get("person", {})
                team_info = leader.get("team", {})
                leaders_list.append({
                    "rank": leader.get("rank", 0),
                    "player": person.get("fullName", "Unknown"),
                    "team": team_info.get("abbreviation", team_info.get("name", "")),
                    "value": leader.get("value", ""),
                })
            # Key by "category|statGroup" so we can pick the right group later
            key = f"{cat_name}|{stat_group}"
            if cat_name:
                results[key] = leaders_list
        return results
    except Exception:
        return {}


# --- Unified entry point ---

def get_leaders(sport: str, category_display: str, limit: int = 20) -> list[dict]:
    """Unified entry point. Returns list of {rank, player, team, value}."""
    cats = SPORT_CATEGORIES.get(sport, {})
    api_key = cats.get(category_display, "")

    if sport == "NBA":
        return fetch_nba_leaders(stat_category=api_key, limit=limit)

    elif sport == "NFL":
        all_nfl = fetch_nfl_leaders(limit=limit)
        # ESPN category names may differ slightly — try exact match first, then fuzzy
        if api_key in all_nfl:
            return all_nfl[api_key]
        for k, v in all_nfl.items():
            if api_key.lower() in k.lower():
                return v
        return []

    elif sport == "MLB":
        # api_key is (category, statGroup) tuple
        api_category, stat_group = api_key
        all_mlb = fetch_mlb_leaders(limit=limit)
        # Exact match: "battingAverage|hitting"
        exact_key = f"{api_category}|{stat_group}"
        if exact_key in all_mlb:
            return all_mlb[exact_key]
        # Fuzzy fallback: match category and group separately
        for k, v in all_mlb.items():
            if api_category.lower() in k.lower() and stat_group.lower() in k.lower():
                return v
        return []

    return []
