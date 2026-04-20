"""Demo game data used when live scoreboard APIs are unavailable."""

import hashlib
import random
from datetime import datetime, timedelta


# Subset of real teams per sport for variety
_NBA_TEAMS = [
    ("San Antonio Spurs", "Spurs"), ("Oklahoma City Thunder", "Thunder"),
    ("Minnesota Timberwolves", "Timberwolves"), ("Philadelphia 76ers", "76ers"),
    ("Orlando Magic", "Magic"), ("Houston Rockets", "Rockets"),
    ("Dallas Mavericks", "Mavericks"), ("Miami Heat", "Heat"),
    ("Los Angeles Lakers", "Lakers"), ("Golden State Warriors", "Warriors"),
    ("Boston Celtics", "Celtics"), ("Denver Nuggets", "Nuggets"),
    ("Milwaukee Bucks", "Bucks"), ("Phoenix Suns", "Suns"),
]

_NFL_TEAMS = [
    ("Chicago Bears", "Bears"), ("Washington Commanders", "Commanders"),
    ("Houston Texans", "Texans"), ("Arizona Cardinals", "Cardinals"),
    ("New York Giants", "Giants"), ("Las Vegas Raiders", "Raiders"),
    ("Kansas City Chiefs", "Chiefs"), ("San Francisco 49ers", "49ers"),
    ("Detroit Lions", "Lions"), ("Atlanta Falcons", "Falcons"),
    ("Seattle Seahawks", "Seahawks"), ("Denver Broncos", "Broncos"),
]

_MLB_TEAMS = [
    ("Pittsburgh Pirates", "Pirates"), ("Milwaukee Brewers", "Brewers"),
    ("Cincinnati Reds", "Reds"), ("Baltimore Orioles", "Orioles"),
    ("Texas Rangers", "Rangers"), ("Arizona Diamondbacks", "Diamondbacks"),
    ("New York Yankees", "Yankees"), ("Los Angeles Dodgers", "Dodgers"),
    ("Tampa Bay Rays", "Rays"), ("St. Louis Cardinals", "Cardinals"),
    ("Washington Nationals", "Nationals"), ("Minnesota Twins", "Twins"),
]

_TEAMS_BY_SPORT = {"NBA": _NBA_TEAMS, "NFL": _NFL_TEAMS, "MLB": _MLB_TEAMS}

_BROADCASTS = {
    "NBA": ["ESPN", "TNT", "NBA TV", "League Pass"],
    "NFL": ["ESPN", "FOX", "CBS", "NBC", "NFL Network", "Amazon Prime"],
    "MLB": ["ESPN", "TBS", "FOX", "MLB Network", "Apple TV+"],
}

_STATUS_OPTIONS = ["Scheduled", "In Progress", "Final"]
_STATUS_WEIGHTS = [0.30, 0.35, 0.35]  # mix of game states


def generate_demo_games(sport: str) -> list[dict]:
    """Generate 3-5 deterministic demo games for a sport based on today's date."""
    today = datetime.now().strftime("%Y-%m-%d")
    seed_str = f"{today}-{sport}-games"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    teams = list(_TEAMS_BY_SPORT.get(sport, _NBA_TEAMS))
    rng.shuffle(teams)
    num_games = rng.randint(3, min(5, len(teams) // 2))
    broadcasts = _BROADCASTS.get(sport, ["ESPN"])

    games = []
    for i in range(num_games):
        home_full, home_short = teams[i * 2]
        away_full, away_short = teams[i * 2 + 1]

        status = rng.choices(_STATUS_OPTIONS, weights=_STATUS_WEIGHTS, k=1)[0]

        if status == "Scheduled":
            home_score = 0
            away_score = 0
            hour = rng.choice([13, 15, 17, 19, 20, 21])
            start_time = f"{hour}:00 ET"
            if sport == "NBA":
                status_detail = f"Tip-off at {start_time}"
            elif sport == "NFL":
                status_detail = f"Kickoff at {start_time}"
            else:
                status_detail = f"First Pitch at {start_time}"
        elif status == "In Progress":
            if sport == "NBA":
                home_score = rng.randint(45, 110)
                away_score = rng.randint(45, 110)
                quarter = rng.choice(["1st Qtr", "2nd Qtr", "3rd Qtr", "4th Qtr"])
                mins = rng.randint(0, 11)
                status_detail = f"{quarter} — {mins}:{rng.randint(0,59):02d}"
            elif sport == "NFL":
                home_score = rng.randint(0, 35)
                away_score = rng.randint(0, 35)
                quarter = rng.choice(["1st Qtr", "2nd Qtr", "3rd Qtr", "4th Qtr"])
                mins = rng.randint(0, 14)
                status_detail = f"{quarter} — {mins}:{rng.randint(0,59):02d}"
            else:
                home_score = rng.randint(0, 9)
                away_score = rng.randint(0, 9)
                inning = rng.choice(["Top", "Bot"])
                inn_num = rng.randint(1, 9)
                status_detail = f"{inning} {inn_num}{'th' if inn_num > 3 else ['st','nd','rd'][inn_num-1]}"
        else:  # Final
            if sport == "NBA":
                home_score = rng.randint(85, 135)
                away_score = rng.randint(85, 135)
            elif sport == "NFL":
                home_score = rng.randint(7, 42)
                away_score = rng.randint(7, 42)
            else:
                home_score = rng.randint(0, 12)
                away_score = rng.randint(0, 12)
            status_detail = "Final"

        sport_path = {"NBA": "nba", "NFL": "nfl", "MLB": "mlb"}.get(sport, "nba")
        game_id = f"DEMO-{sport}-{today}-{i}"

        games.append({
            "game_id": game_id,
            "status": status,
            "status_detail": status_detail,
            "home_team": home_full,
            "away_team": away_full,
            "home_score": home_score,
            "away_score": away_score,
            "start_time": status_detail if status == "Scheduled" else "",
            "broadcast": rng.choice(broadcasts),
            "espn_link": f"https://www.espn.com/{sport_path}/game/_/gameId/{game_id}",
            "sport": sport,
        })

    return games
