"""Player stats: nba_api (NBA), ESPN API (NFL), MLB Stats API (MLB). All free, no keys needed."""

import requests
import streamlit as st
from nba_api.stats.static import players as nba_players
from nba_api.stats.endpoints import playercareerstats, commonplayerinfo


# =====================================================================
# NBA — nba_api (free, no key)
# =====================================================================

def _nba_search(query: str) -> list[dict]:
    """Search NBA players using nba_api static data."""
    query_lower = query.strip().lower()
    all_players = nba_players.get_players()

    matches = [p for p in all_players if p["full_name"].lower() == query_lower]
    if not matches:
        matches = [p for p in all_players if query_lower in p["full_name"].lower()]

    matches.sort(key=lambda p: (not p.get("is_active", False)))
    return matches[:10]


def _nba_career_stats(player_id: int, num_seasons: int) -> list[dict]:
    """Fetch NBA career stats via nba_api."""
    try:
        career = playercareerstats.PlayerCareerStats(player_id=player_id, timeout=15)
        df = career.get_data_frames()[0]
    except Exception:
        return []

    if df.empty:
        return []

    df = df.tail(num_seasons).copy()
    results = []
    for _, row in df.iterrows():
        gp = row.get("GP", 0)
        if gp == 0:
            continue

        season_id = str(row.get("SEASON_ID", ""))
        try:
            season_year = int(season_id.split("-")[0])
        except (ValueError, IndexError):
            continue

        results.append({
            "season": season_year,
            "pts": round(row.get("PTS", 0) / gp, 1),
            "reb": round(row.get("REB", 0) / gp, 1),
            "ast": round(row.get("AST", 0) / gp, 1),
            "stl": round(row.get("STL", 0) / gp, 1),
            "blk": round(row.get("BLK", 0) / gp, 1),
            "fg_pct": round(row.get("FG_PCT", 0), 3),
            "gp": int(gp),
            "min": round(row.get("MIN", 0) / gp, 1),
        })

    return results


def _format_nba_player(player: dict) -> dict:
    """Format NBA player info with details from NBA API."""
    info = {
        "id": player.get("id"),
        "name": player.get("full_name")
            or f"{player.get('first_name', '')} {player.get('last_name', '')}".strip(),
        "team": "Unknown",
        "position": "N/A",
        "height": "N/A",
        "draft_year": None,
        "draft_number": None,
    }

    try:
        details = commonplayerinfo.CommonPlayerInfo(player_id=player["id"], timeout=10)
        df = details.get_data_frames()[0]
        if not df.empty:
            row = df.iloc[0]
            info["team"] = str(row.get("TEAM_NAME", "Unknown"))
            info["position"] = str(row.get("POSITION", "N/A"))
            info["height"] = str(row.get("HEIGHT", "N/A"))
            try:
                info["draft_year"] = int(row.get("DRAFT_YEAR"))
            except (TypeError, ValueError):
                pass
            try:
                info["draft_number"] = int(row.get("DRAFT_NUMBER"))
            except (TypeError, ValueError):
                pass
    except Exception:
        pass

    return info


# =====================================================================
# NFL — ESPN API (free, no key)
# =====================================================================

_ESPN_SEARCH_URL = "https://site.web.api.espn.com/apis/search/v2"
_ESPN_NFL_ATHLETE_URL = "https://site.api.espn.com/apis/common/v3/sports/football/nfl/athletes"
_ESPN_NFL_STATS_URL = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/athletes"

# ESPN league IDs: 28=NFL, 10=MLB
_ESPN_NFL_LEAGUE = "28"

# Stat extraction: (category_name, display_name) -> our key
_NFL_STAT_MAP = [
    ("Passing", "Passing Yards", "pass_yds"),
    ("Passing", "Passing Touchdowns", "pass_td"),
    ("Rushing", "Rushing Yards", "rush_yds"),
    ("Rushing", "Rushing Touchdowns", "rush_td"),
    ("Receiving", "Receiving Yards", "rec_yds"),
    ("Receiving", "Receiving Touchdowns", "rec_td"),
    ("General", "Games Played", "gp"),
]


def _espn_search(query: str, league_id: str) -> list[dict]:
    """Search ESPN for athletes, filtered by league."""
    try:
        resp = requests.get(_ESPN_SEARCH_URL, params={"query": query, "limit": 10, "page": 1}, timeout=10)
        resp.raise_for_status()
    except requests.RequestException:
        return []

    results = []
    for section in resp.json().get("results", []):
        if section.get("type") != "player":
            continue
        for item in section.get("contents", []):
            uid = item.get("uid", "")
            # uid format: s:XX~l:LEAGUE~a:ATHLETE_ID
            if f"~l:{league_id}~" not in uid:
                continue
            athlete_id = uid.split("~a:")[1] if "~a:" in uid else None
            if not athlete_id:
                continue

            name = item.get("displayName", "")
            parts = name.split(" ", 1)
            results.append({
                "id": int(athlete_id),
                "first_name": parts[0] if parts else name,
                "last_name": parts[1] if len(parts) > 1 else "",
                "full_name": name,
                "source": "espn",
            })

    return results


def _nfl_search(query: str) -> list[dict]:
    """Search NFL players via ESPN."""
    players = _espn_search(query, _ESPN_NFL_LEAGUE)
    if not players:
        return players

    # Enrich first result with team/position from ESPN athlete API
    for p in players[:1]:
        try:
            resp = requests.get(f"{_ESPN_NFL_ATHLETE_URL}/{p['id']}", timeout=10)
            if resp.status_code == 200:
                athlete = resp.json().get("athlete", {})
                p["team"] = athlete.get("team", {}).get("displayName", "Unknown")
                p["position"] = athlete.get("position", {}).get("abbreviation", "N/A")
        except requests.RequestException:
            pass

    return players


def _nfl_season_stats(athlete_id: int, num_seasons: int) -> list[dict]:
    """Fetch NFL season stats from ESPN."""
    try:
        resp = requests.get(f"{_ESPN_NFL_STATS_URL}/{athlete_id}/statisticslog", timeout=10)
        resp.raise_for_status()
    except requests.RequestException:
        return []

    entries = resp.json().get("entries", [])
    results = []

    for entry in entries[:num_seasons]:
        season_ref = entry.get("season", {}).get("$ref", "")
        try:
            year = int(season_ref.split("/seasons/")[1].split("?")[0])
        except (ValueError, IndexError):
            continue

        for stat_item in entry.get("statistics", []):
            if stat_item.get("type") != "total":
                continue

            stats_ref = stat_item.get("statistics", {}).get("$ref", "")
            if not stats_ref:
                continue

            try:
                resp2 = requests.get(stats_ref, timeout=10)
                resp2.raise_for_status()
            except requests.RequestException:
                continue

            cats = resp2.json().get("splits", {}).get("categories", [])
            stat_map = {"season": year}

            for cat in cats:
                cat_name = cat.get("displayName", "")
                for s in cat.get("stats", []):
                    dn = s.get("displayName", "")
                    val = s.get("value", 0)
                    for expected_cat, expected_dn, key in _NFL_STAT_MAP:
                        if cat_name == expected_cat and dn == expected_dn:
                            stat_map[key] = int(val)

            results.append(stat_map)
            break

    return results


def _format_nfl_player(player: dict) -> dict:
    """Format NFL player info."""
    info = {
        "id": player.get("id"),
        "name": player.get("full_name")
            or f"{player.get('first_name', '')} {player.get('last_name', '')}".strip(),
        "team": player.get("team", "Unknown"),
        "position": player.get("position", "N/A"),
    }

    # Fetch from ESPN if not already enriched
    if info["team"] == "Unknown":
        try:
            resp = requests.get(f"{_ESPN_NFL_ATHLETE_URL}/{player['id']}", timeout=10)
            if resp.status_code == 200:
                athlete = resp.json().get("athlete", {})
                info["team"] = athlete.get("team", {}).get("displayName", "Unknown")
                info["position"] = athlete.get("position", {}).get("abbreviation", "N/A")
        except requests.RequestException:
            pass

    return info


# =====================================================================
# MLB — MLB Stats API (free, no key, official)
# =====================================================================

_MLB_BASE_URL = "https://statsapi.mlb.com/api/v1"


def _mlb_search(query: str) -> list[dict]:
    """Search MLB players using official MLB Stats API."""
    try:
        resp = requests.get(
            f"{_MLB_BASE_URL}/people/search",
            params={"names": query, "sportIds": 1, "hydrate": "currentTeam"},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException:
        return []

    results = []
    for p in resp.json().get("people", []):
        name = p.get("fullName", "")
        parts = name.split(" ", 1)
        results.append({
            "id": p.get("id"),
            "first_name": parts[0] if parts else name,
            "last_name": parts[1] if len(parts) > 1 else "",
            "full_name": name,
            "team": p.get("currentTeam", {}).get("name", "Unknown"),
            "position": p.get("primaryPosition", {}).get("abbreviation", "N/A"),
            "active": p.get("active", False),
            "source": "mlb",
        })

    # Active players first
    results.sort(key=lambda x: (not x.get("active", False)))
    return results[:10]


def _mlb_season_stats(player_id: int, num_seasons: int) -> list[dict]:
    """Fetch MLB stats from official API — tries hitting first, then pitching."""

    def safe_float(val, default=0.0):
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    def _fetch_group(group: str) -> list[dict]:
        try:
            resp = requests.get(
                f"{_MLB_BASE_URL}/people/{player_id}/stats",
                params={"stats": "yearByYear", "group": group, "sportId": 1},
                timeout=10,
            )
            resp.raise_for_status()
        except requests.RequestException:
            return []
        stats_list = resp.json().get("stats", [])
        if not stats_list:
            return []
        return stats_list[0].get("splits", [])

    # Try hitting first
    splits = _fetch_group("hitting")
    if splits:
        results = []
        for s in splits[-num_seasons:]:
            stat = s.get("stat", {})
            try:
                season = int(s.get("season", 0))
            except (ValueError, TypeError):
                continue
            results.append({
                "season": season,
                "avg": safe_float(stat.get("avg"), 0),
                "hr": int(stat.get("homeRuns", 0)),
                "rbi": int(stat.get("rbi", 0)),
                "ops": safe_float(stat.get("ops"), 0),
                "sb": int(stat.get("stolenBases", 0)),
                "gp": int(stat.get("gamesPlayed", 0)),
            })
        return results

    # Fall back to pitching
    splits = _fetch_group("pitching")
    if splits:
        results = []
        for s in splits[-num_seasons:]:
            stat = s.get("stat", {})
            try:
                season = int(s.get("season", 0))
            except (ValueError, TypeError):
                continue
            results.append({
                "season": season,
                "era": safe_float(stat.get("era"), 0),
                "w": int(stat.get("wins", 0)),
                "l": int(stat.get("losses", 0)),
                "so": int(stat.get("strikeOuts", 0)),
                "whip": safe_float(stat.get("whip"), 0),
                "ip": safe_float(stat.get("inningsPitched"), 0),
                "gp": int(stat.get("gamesPlayed", 0)),
                "_is_pitcher": True,
            })
        return results

    return []


def _format_mlb_player(player: dict) -> dict:
    """Format MLB player info."""
    return {
        "id": player.get("id"),
        "name": player.get("full_name")
            or f"{player.get('first_name', '')} {player.get('last_name', '')}".strip(),
        "team": player.get("team", "Unknown"),
        "position": player.get("position", "N/A"),
    }


# =====================================================================
# Public API (used by app.py and breakout_engine.py)
# =====================================================================

@st.cache_data(ttl=300)
def search_players(query: str, sport: str = "NBA") -> list[dict]:
    """Search for players by name."""
    sport = sport.upper()
    if sport == "NBA":
        return _nba_search(query)
    elif sport == "NFL":
        return _nfl_search(query)
    elif sport == "MLB":
        return _mlb_search(query)
    return []


@st.cache_data(ttl=300)
def get_season_averages(player_id: int, season: int, sport: str = "NBA") -> dict | None:
    """Get a player's season averages for a given year."""
    all_seasons = get_multi_season_stats(player_id, sport, num_seasons=10)
    for s in all_seasons:
        if s.get("season") == season:
            return s
    return None


@st.cache_data(ttl=300)
def get_multi_season_stats(player_id: int, sport: str = "NBA", num_seasons: int = 5) -> list[dict]:
    """Get a player's stats across multiple recent seasons."""
    sport = sport.upper()
    if sport == "NBA":
        return _nba_career_stats(player_id, num_seasons)
    elif sport == "NFL":
        return _nfl_season_stats(player_id, num_seasons)
    elif sport == "MLB":
        return _mlb_season_stats(player_id, num_seasons)
    return []


def format_player_info(player: dict, sport: str = "NBA") -> dict:
    """Extract a clean summary from a raw player dict."""
    sport = sport.upper()
    if sport == "NBA":
        return _format_nba_player(player)
    elif sport == "NFL":
        return _format_nfl_player(player)
    elif sport == "MLB":
        return _format_mlb_player(player)
    return {"id": player.get("id"), "name": "Unknown", "team": "Unknown"}
