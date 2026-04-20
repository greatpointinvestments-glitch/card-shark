"""Live game tracker — ESPN/MLB scoreboard fetching, player-to-game matching."""

import streamlit as st
import requests
from datetime import datetime

from config.settings import (
    ESPN_NBA_SCOREBOARD, ESPN_NFL_SCOREBOARD, MLB_SCHEDULE_URL,
    GAME_TRACKER_TTL, TEAM_NAME_ALIASES,
)
from data.watchlists import (
    NBA_BREAKOUT_WATCHLIST, NFL_BREAKOUT_WATCHLIST, MLB_BREAKOUT_WATCHLIST,
)
from data.demo_games import generate_demo_games


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_player_team_lookup() -> dict:
    """Build name.lower() -> (team, sport) from all breakout watchlists.

    Legends are excluded (retired = no live games).
    """
    lookup = {}
    for player in NBA_BREAKOUT_WATCHLIST:
        lookup[player["name"].lower()] = (player["team"], "NBA")
    for player in NFL_BREAKOUT_WATCHLIST:
        lookup[player["name"].lower()] = (player["team"], "NFL")
    for player in MLB_BREAKOUT_WATCHLIST:
        lookup[player["name"].lower()] = (player["team"], "MLB")
    return lookup


def _resolve_team_name(team_name: str) -> str:
    """Resolve aliases so watchlist team names match API team names."""
    return TEAM_NAME_ALIASES.get(team_name, team_name)


def _fetch_espn_scoreboard(sport_path_url: str, sport: str) -> list[dict]:
    """Fetch today's games from ESPN's free scoreboard API (NBA/NFL)."""
    try:
        resp = requests.get(sport_path_url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    games = []
    sport_path = "nba" if "basketball" in sport_path_url else "nfl"

    for event in data.get("events", []):
        competition = event.get("competitions", [{}])[0]
        competitors = competition.get("competitors", [])
        if len(competitors) < 2:
            continue

        home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
        away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

        status_obj = event.get("status", {})
        status_type = status_obj.get("type", {}).get("name", "STATUS_SCHEDULED")
        status_detail = status_obj.get("type", {}).get("shortDetail", "")

        if status_type == "STATUS_FINAL":
            status = "Final"
        elif status_type == "STATUS_IN_PROGRESS":
            status = "In Progress"
        else:
            status = "Scheduled"

        broadcasts_list = competition.get("broadcasts", [])
        broadcast = ""
        if broadcasts_list:
            names = broadcasts_list[0].get("names", [])
            broadcast = names[0] if names else ""

        game_id = event.get("id", "")

        games.append({
            "game_id": game_id,
            "status": status,
            "status_detail": status_detail,
            "home_team": home.get("team", {}).get("displayName", ""),
            "away_team": away.get("team", {}).get("displayName", ""),
            "home_score": int(home.get("score", 0)),
            "away_score": int(away.get("score", 0)),
            "start_time": event.get("date", ""),
            "broadcast": broadcast,
            "espn_link": f"https://www.espn.com/{sport_path}/game/_/gameId/{game_id}",
            "sport": sport,
        })

    return games


def _fetch_mlb_schedule() -> list[dict]:
    """Fetch today's MLB games from the free MLB Stats API."""
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        resp = requests.get(
            MLB_SCHEDULE_URL,
            params={"sportId": 1, "date": today, "hydrate": "team,linescore"},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    games = []
    for date_entry in data.get("dates", []):
        for game in date_entry.get("games", []):
            status_code = game.get("status", {}).get("abstractGameCode", "P")
            detail_state = game.get("status", {}).get("detailedState", "Scheduled")

            if status_code == "F":
                status = "Final"
            elif status_code == "L":
                status = "In Progress"
            else:
                status = "Scheduled"

            teams = game.get("teams", {})
            home_team = teams.get("home", {}).get("team", {}).get("name", "")
            away_team = teams.get("away", {}).get("team", {}).get("name", "")

            linescore = game.get("linescore", {})
            home_score = linescore.get("teams", {}).get("home", {}).get("runs", 0) or 0
            away_score = linescore.get("teams", {}).get("away", {}).get("runs", 0) or 0

            game_pk = game.get("gamePk", "")

            games.append({
                "game_id": str(game_pk),
                "status": status,
                "status_detail": detail_state,
                "home_team": home_team,
                "away_team": away_team,
                "home_score": int(home_score),
                "away_score": int(away_score),
                "start_time": game.get("gameDate", ""),
                "broadcast": "",
                "espn_link": f"https://www.espn.com/mlb/game/_/gameId/{game_pk}",
                "sport": "MLB",
            })

    return games


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@st.cache_data(ttl=GAME_TRACKER_TTL)
def get_todays_games(sport: str) -> list[dict]:
    """Fetch today's games for a sport. Falls back to demo data on failure."""
    if sport == "NBA":
        games = _fetch_espn_scoreboard(ESPN_NBA_SCOREBOARD, "NBA")
    elif sport == "NFL":
        games = _fetch_espn_scoreboard(ESPN_NFL_SCOREBOARD, "NFL")
    elif sport == "MLB":
        games = _fetch_mlb_schedule()
    else:
        games = []

    if not games:
        games = generate_demo_games(sport)

    return games


def match_players_to_games(players: list[dict], games: list[dict]) -> list[dict]:
    """Match portfolio/watchlist players to today's games by team name.

    Args:
        players: list of dicts with at least {player_name, sport} and optionally {team, card_type}.
        games: list of game dicts from get_todays_games().

    Returns:
        list of dicts with player info + game match data.
    """
    team_lookup = _build_player_team_lookup()

    # Build a team -> game index (resolve aliases)
    team_to_game = {}
    for game in games:
        team_to_game[_resolve_team_name(game["home_team"]).lower()] = game
        team_to_game[_resolve_team_name(game["away_team"]).lower()] = game

    results = []
    for player in players:
        name = player.get("player_name", player.get("name", ""))
        sport = player.get("sport", "")
        card_type = player.get("card_type", "")

        # Resolve team — use explicit team if provided, else look up in watchlists
        team = player.get("team", "")
        if not team:
            wl_entry = team_lookup.get(name.lower())
            if wl_entry:
                team = wl_entry[0]

        if not team:
            results.append({
                "player_name": name,
                "team": "Unknown",
                "sport": sport,
                "card_type": card_type,
                "game": None,
                "is_playing_today": False,
                "opponent": "",
                "game_status": "",
            })
            continue

        resolved_team = _resolve_team_name(team).lower()
        game = team_to_game.get(resolved_team)

        if game:
            if resolved_team == _resolve_team_name(game["home_team"]).lower():
                opponent = game["away_team"]
            else:
                opponent = game["home_team"]

            results.append({
                "player_name": name,
                "team": team,
                "sport": sport,
                "card_type": card_type,
                "game": game,
                "is_playing_today": True,
                "opponent": opponent,
                "game_status": game["status"],
            })
        else:
            results.append({
                "player_name": name,
                "team": team,
                "sport": sport,
                "card_type": card_type,
                "game": None,
                "is_playing_today": False,
                "opponent": "",
                "game_status": "",
            })

    return results


def build_watch_links(game: dict) -> dict:
    """Build gamecast, YouTube highlights, and DraftKings links for a game."""
    sport = game.get("sport", "NBA")
    game_id = game.get("game_id", "")
    today = datetime.now().strftime("%Y-%m-%d")

    home = game.get("home_team", "")
    away = game.get("away_team", "")
    yt_query = f"{away}+vs+{home}+highlights+{today}".replace(" ", "+")

    # DraftKings search by team names
    dk_query = f"{away} vs {home}".replace(" ", "+")

    # ESPN gamecast link — NBA/NFL use ESPN game IDs directly.
    # MLB uses gamePk from the MLB Stats API which doesn't match ESPN IDs,
    # so link to MLB.com Gameday instead.
    if sport == "MLB":
        gamecast = f"https://www.mlb.com/gameday/{game_id}"
    else:
        sport_path = {"NBA": "nba", "NFL": "nfl"}.get(sport, "nba")
        gamecast = f"https://www.espn.com/{sport_path}/game/_/gameId/{game_id}"

    return {
        "gamecast": gamecast,
        "youtube_highlights": f"https://www.youtube.com/results?search_query={yt_query}",
        "draftkings": f"https://sportsbook.draftkings.com/search/{dk_query}",
    }


def get_game_card_impact(player_name: str, game: dict) -> str:
    """Return a card-market context line based on game status and score."""
    if not game:
        return "No game today — prices tend to be quieter on off days"

    status = game.get("status", "Scheduled")
    home_score = game.get("home_score", 0)
    away_score = game.get("away_score", 0)
    diff = abs(home_score - away_score)

    if status == "Scheduled":
        return "Game day — prices often spike after big performances"

    if status == "In Progress":
        return "Game in progress — check back for final stats"

    # Final
    if diff >= 20 and game.get("sport") == "NBA":
        return "Dominant win — breakout performances drive card spikes"
    elif diff >= 14 and game.get("sport") == "NFL":
        return "Dominant win — breakout performances drive card spikes"
    elif diff >= 5 and game.get("sport") == "MLB":
        return "Dominant win — breakout performances drive card spikes"
    elif home_score > away_score or away_score > home_score:
        # Close game
        return "Close game — standout individual performances can still move markets"

    return "Loss — could create a buying dip opportunity"
