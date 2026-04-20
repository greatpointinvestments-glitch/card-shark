"""Curated player watchlists for breakout detection and legend investment."""

# --- NBA Breakout Candidates (Young players, 1-5 seasons) ---
# Each entry: name, team, age, draft_year, draft_pick, seasons_played
NBA_BREAKOUT_WATCHLIST = [
    # 2024 Draft Class
    {"name": "Zaccharie Risacher", "team": "Atlanta Hawks", "age": 19, "draft_year": 2024, "draft_pick": 1, "seasons": 1},
    {"name": "Alex Sarr", "team": "Washington Wizards", "age": 19, "draft_year": 2024, "draft_pick": 2, "seasons": 1},
    {"name": "Reed Sheppard", "team": "Houston Rockets", "age": 20, "draft_year": 2024, "draft_pick": 3, "seasons": 1},
    {"name": "Stephon Castle", "team": "San Antonio Spurs", "age": 20, "draft_year": 2024, "draft_pick": 4, "seasons": 1},
    {"name": "Ron Holland", "team": "Detroit Pistons", "age": 19, "draft_year": 2024, "draft_pick": 5, "seasons": 1},
    {"name": "Donovan Clingan", "team": "Portland Trail Blazers", "age": 21, "draft_year": 2024, "draft_pick": 7, "seasons": 1},
    {"name": "Zach Edey", "team": "Memphis Grizzlies", "age": 22, "draft_year": 2024, "draft_pick": 9, "seasons": 1},
    {"name": "Cody Williams", "team": "Utah Jazz", "age": 19, "draft_year": 2024, "draft_pick": 10, "seasons": 1},
    {"name": "Matas Buzelis", "team": "Chicago Bulls", "age": 20, "draft_year": 2024, "draft_pick": 11, "seasons": 1},
    {"name": "Nikola Topic", "team": "Oklahoma City Thunder", "age": 19, "draft_year": 2024, "draft_pick": 12, "seasons": 1},
    {"name": "Jared McCain", "team": "Philadelphia 76ers", "age": 21, "draft_year": 2024, "draft_pick": 16, "seasons": 1},
    {"name": "Dalton Knecht", "team": "Los Angeles Lakers", "age": 23, "draft_year": 2024, "draft_pick": 17, "seasons": 1},
    {"name": "Yves Missi", "team": "New Orleans Pelicans", "age": 20, "draft_year": 2024, "draft_pick": 21, "seasons": 1},
    # 2023 Draft Class
    {"name": "Victor Wembanyama", "team": "San Antonio Spurs", "age": 21, "draft_year": 2023, "draft_pick": 1, "seasons": 2},
    {"name": "Brandon Miller", "team": "Charlotte Hornets", "age": 22, "draft_year": 2023, "draft_pick": 2, "seasons": 2},
    {"name": "Scoot Henderson", "team": "Portland Trail Blazers", "age": 21, "draft_year": 2023, "draft_pick": 3, "seasons": 2},
    {"name": "Amen Thompson", "team": "Houston Rockets", "age": 21, "draft_year": 2023, "draft_pick": 4, "seasons": 2},
    {"name": "Ausar Thompson", "team": "Detroit Pistons", "age": 21, "draft_year": 2023, "draft_pick": 5, "seasons": 2},
    {"name": "Jarace Walker", "team": "Indiana Pacers", "age": 20, "draft_year": 2023, "draft_pick": 8, "seasons": 2},
    {"name": "Taylor Hendricks", "team": "Utah Jazz", "age": 21, "draft_year": 2023, "draft_pick": 9, "seasons": 2},
    {"name": "Dereck Lively II", "team": "Dallas Mavericks", "age": 20, "draft_year": 2023, "draft_pick": 12, "seasons": 2},
    {"name": "Gradey Dick", "team": "Toronto Raptors", "age": 21, "draft_year": 2023, "draft_pick": 13, "seasons": 2},
    {"name": "Keyonte George", "team": "Utah Jazz", "age": 21, "draft_year": 2023, "draft_pick": 16, "seasons": 2},
    {"name": "Jaime Jaquez Jr", "team": "Miami Heat", "age": 24, "draft_year": 2023, "draft_pick": 18, "seasons": 2},
    {"name": "Cam Whitmore", "team": "Houston Rockets", "age": 21, "draft_year": 2023, "draft_pick": 20, "seasons": 2},
    {"name": "Brice Sensabaugh", "team": "Utah Jazz", "age": 21, "draft_year": 2023, "draft_pick": 28, "seasons": 2},
    {"name": "Trayce Jackson-Davis", "team": "Golden State Warriors", "age": 24, "draft_year": 2023, "draft_pick": 57, "seasons": 2},
    # 2022 Draft Class
    {"name": "Paolo Banchero", "team": "Orlando Magic", "age": 22, "draft_year": 2022, "draft_pick": 1, "seasons": 3},
    {"name": "Chet Holmgren", "team": "Oklahoma City Thunder", "age": 22, "draft_year": 2022, "draft_pick": 2, "seasons": 2},
    {"name": "Evan Mobley", "team": "Cleveland Cavaliers", "age": 23, "draft_year": 2021, "draft_pick": 3, "seasons": 4},
    {"name": "Scottie Barnes", "team": "Toronto Raptors", "age": 23, "draft_year": 2021, "draft_pick": 4, "seasons": 4},
    {"name": "Franz Wagner", "team": "Orlando Magic", "age": 23, "draft_year": 2021, "draft_pick": 8, "seasons": 4},
    # Young Stars (2-5 seasons)
    {"name": "Anthony Edwards", "team": "Minnesota Timberwolves", "age": 23, "draft_year": 2020, "draft_pick": 1, "seasons": 5},
    {"name": "Tyrese Maxey", "team": "Philadelphia 76ers", "age": 24, "draft_year": 2020, "draft_pick": 21, "seasons": 5},
    {"name": "Tyrese Haliburton", "team": "Indiana Pacers", "age": 24, "draft_year": 2020, "draft_pick": 12, "seasons": 5},
    {"name": "Jalen Green", "team": "Houston Rockets", "age": 23, "draft_year": 2021, "draft_pick": 2, "seasons": 4},
    {"name": "Ja Morant", "team": "Memphis Grizzlies", "age": 25, "draft_year": 2019, "draft_pick": 2, "seasons": 5},
    {"name": "Trae Young", "team": "Atlanta Hawks", "age": 26, "draft_year": 2018, "draft_pick": 5, "seasons": 7},
    {"name": "Shai Gilgeous-Alexander", "team": "Oklahoma City Thunder", "age": 26, "draft_year": 2018, "draft_pick": 11, "seasons": 7},
    {"name": "Lauri Markkanen", "team": "Utah Jazz", "age": 27, "draft_year": 2017, "draft_pick": 7, "seasons": 8},
]


# --- NFL Breakout Candidates (Young players, 1-3 seasons) ---
NFL_BREAKOUT_WATCHLIST = [
    # 2024 Draft Class
    {"name": "Caleb Williams", "team": "Chicago Bears", "age": 23, "draft_year": 2024, "draft_pick": 1, "seasons": 1},
    {"name": "Jayden Daniels", "team": "Washington Commanders", "age": 24, "draft_year": 2024, "draft_pick": 2, "seasons": 1},
    {"name": "Drake Maye", "team": "New England Patriots", "age": 22, "draft_year": 2024, "draft_pick": 3, "seasons": 1},
    {"name": "Marvin Harrison Jr", "team": "Arizona Cardinals", "age": 22, "draft_year": 2024, "draft_pick": 4, "seasons": 1},
    {"name": "Malik Nabers", "team": "New York Giants", "age": 21, "draft_year": 2024, "draft_pick": 6, "seasons": 1},
    {"name": "Rome Odunze", "team": "Chicago Bears", "age": 22, "draft_year": 2024, "draft_pick": 9, "seasons": 1},
    {"name": "Bo Nix", "team": "Denver Broncos", "age": 25, "draft_year": 2024, "draft_pick": 12, "seasons": 1},
    {"name": "Brock Bowers", "team": "Las Vegas Raiders", "age": 22, "draft_year": 2024, "draft_pick": 13, "seasons": 1},
    {"name": "Adonai Mitchell", "team": "Indianapolis Colts", "age": 23, "draft_year": 2024, "draft_pick": 52, "seasons": 1},
    {"name": "Trey Benson", "team": "Arizona Cardinals", "age": 22, "draft_year": 2024, "draft_pick": 66, "seasons": 1},
    # 2023 Draft Class
    {"name": "Bryce Young", "team": "Carolina Panthers", "age": 23, "draft_year": 2023, "draft_pick": 1, "seasons": 2},
    {"name": "CJ Stroud", "team": "Houston Texans", "age": 23, "draft_year": 2023, "draft_pick": 2, "seasons": 2},
    {"name": "Anthony Richardson", "team": "Indianapolis Colts", "age": 22, "draft_year": 2023, "draft_pick": 4, "seasons": 2},
    {"name": "Bijan Robinson", "team": "Atlanta Falcons", "age": 22, "draft_year": 2023, "draft_pick": 8, "seasons": 2},
    {"name": "Jahmyr Gibbs", "team": "Detroit Lions", "age": 22, "draft_year": 2023, "draft_pick": 12, "seasons": 2},
    {"name": "Jaxon Smith-Njigba", "team": "Seattle Seahawks", "age": 22, "draft_year": 2023, "draft_pick": 20, "seasons": 2},
    {"name": "Puka Nacua", "team": "Los Angeles Rams", "age": 23, "draft_year": 2023, "draft_pick": 177, "seasons": 2},
    {"name": "Sam LaPorta", "team": "Detroit Lions", "age": 24, "draft_year": 2023, "draft_pick": 34, "seasons": 2},
    # Young Stars (2-4 seasons)
    {"name": "Joe Burrow", "team": "Cincinnati Bengals", "age": 28, "draft_year": 2020, "draft_pick": 1, "seasons": 5},
    {"name": "Trevor Lawrence", "team": "Jacksonville Jaguars", "age": 25, "draft_year": 2021, "draft_pick": 1, "seasons": 4},
    {"name": "Garrett Wilson", "team": "New York Jets", "age": 24, "draft_year": 2022, "draft_pick": 10, "seasons": 3},
    {"name": "Chris Olave", "team": "New Orleans Saints", "age": 24, "draft_year": 2022, "draft_pick": 11, "seasons": 3},
    {"name": "Tank Dell", "team": "Houston Texans", "age": 25, "draft_year": 2023, "draft_pick": 69, "seasons": 2},
    {"name": "Nico Collins", "team": "Houston Texans", "age": 26, "draft_year": 2021, "draft_pick": 89, "seasons": 4},
]


# --- MLB Breakout Candidates (Young players, 1-3 seasons) ---
MLB_BREAKOUT_WATCHLIST = [
    {"name": "Paul Skenes", "team": "Pittsburgh Pirates", "age": 22, "draft_year": 2023, "draft_pick": 1, "seasons": 1},
    {"name": "Jackson Chourio", "team": "Milwaukee Brewers", "age": 21, "draft_year": None, "draft_pick": None, "seasons": 2},
    {"name": "Elly De La Cruz", "team": "Cincinnati Reds", "age": 22, "draft_year": None, "draft_pick": None, "seasons": 2},
    {"name": "Jackson Holliday", "team": "Baltimore Orioles", "age": 21, "draft_year": 2022, "draft_pick": 1, "seasons": 2},
    {"name": "Junior Caminero", "team": "Tampa Bay Rays", "age": 21, "draft_year": None, "draft_pick": None, "seasons": 2},
    {"name": "Evan Carter", "team": "Texas Rangers", "age": 22, "draft_year": 2020, "draft_pick": 50, "seasons": 2},
    {"name": "Corbin Carroll", "team": "Arizona Diamondbacks", "age": 24, "draft_year": 2019, "draft_pick": 16, "seasons": 3},
    {"name": "Gunnar Henderson", "team": "Baltimore Orioles", "age": 24, "draft_year": 2019, "draft_pick": 42, "seasons": 3},
    {"name": "Jasson Dominguez", "team": "New York Yankees", "age": 22, "draft_year": None, "draft_pick": None, "seasons": 2},
    {"name": "Dylan Crews", "team": "Washington Nationals", "age": 22, "draft_year": 2023, "draft_pick": 2, "seasons": 1},
    {"name": "Wyatt Langford", "team": "Texas Rangers", "age": 23, "draft_year": 2023, "draft_pick": 4, "seasons": 1},
    {"name": "Jordan Walker", "team": "St. Louis Cardinals", "age": 22, "draft_year": 2020, "draft_pick": 21, "seasons": 2},
    {"name": "James Wood", "team": "Washington Nationals", "age": 22, "draft_year": 2021, "draft_pick": 62, "seasons": 1},
    {"name": "Colton Cowser", "team": "Baltimore Orioles", "age": 24, "draft_year": 2021, "draft_pick": 5, "seasons": 2},
    {"name": "Brooks Lee", "team": "Minnesota Twins", "age": 23, "draft_year": 2022, "draft_pick": 8, "seasons": 1},
    # Young Stars (2-4 seasons)
    {"name": "Julio Rodriguez", "team": "Seattle Mariners", "age": 24, "draft_year": None, "draft_pick": None, "seasons": 4},
    {"name": "Bobby Witt Jr", "team": "Kansas City Royals", "age": 24, "draft_year": 2019, "draft_pick": 2, "seasons": 4},
    {"name": "Adley Rutschman", "team": "Baltimore Orioles", "age": 26, "draft_year": 2019, "draft_pick": 1, "seasons": 4},
    {"name": "Pete Crow-Armstrong", "team": "Chicago Cubs", "age": 22, "draft_year": 2020, "draft_pick": 19, "seasons": 2},
    {"name": "Marcelo Mayer", "team": "Boston Red Sox", "age": 22, "draft_year": 2021, "draft_pick": 4, "seasons": 1},
    {"name": "Corey Seager", "team": "Texas Rangers", "age": 31, "draft_year": 2012, "draft_pick": 18, "seasons": 10},
    {"name": "Luis Robert Jr", "team": "Chicago White Sox", "age": 27, "draft_year": None, "draft_pick": None, "seasons": 5},
]


# --- Pokemon Legends (Iconic Cards) ---
POKEMON_LEGENDS_WATCHLIST = [
    {
        "name": "Charizard", "sport": "Pokemon", "hof": True,
        "iconic_cards": ["Base Set #4", "Base Set 1st Edition #4", "Shadowless #4"],
        "significance": 10, "cultural_score": 10,
        "notes": "The grail of Pokemon cards — Base Set Charizard defines the hobby",
    },
    {
        "name": "Pikachu", "sport": "Pokemon", "hof": True,
        "iconic_cards": ["Base Set #58", "Illustrator Promo", "VMAX Rainbow"],
        "significance": 10, "cultural_score": 10,
        "notes": "The face of Pokemon — Illustrator Pikachu is the most valuable card in existence",
    },
    {
        "name": "Mewtwo", "sport": "Pokemon", "hof": True,
        "iconic_cards": ["Base Set #10", "Shadowless #10", "EX Full Art"],
        "significance": 9, "cultural_score": 9,
        "notes": "Iconic legendary — Base Set Mewtwo is a staple of vintage collections",
    },
    {
        "name": "Lugia", "sport": "Pokemon", "hof": True,
        "iconic_cards": ["Neo Genesis #9", "1st Edition Neo Genesis #9"],
        "significance": 9, "cultural_score": 9,
        "notes": "Neo Genesis Lugia is the most sought-after card outside Base Set",
    },
    {
        "name": "Umbreon", "sport": "Pokemon", "hof": True,
        "iconic_cards": ["Neo Discovery #13", "Skyridge #H30", "VMAX Alt Art"],
        "significance": 8, "cultural_score": 9,
        "notes": "Fan favorite Eeveelution — modern Alt Art Umbreon is a chase card",
    },
    {
        "name": "Blastoise", "sport": "Pokemon", "hof": True,
        "iconic_cards": ["Base Set #2", "1st Edition Base Set #2"],
        "significance": 9, "cultural_score": 8,
        "notes": "Part of the original starter trio — always in demand",
    },
    {
        "name": "Venusaur", "sport": "Pokemon", "hof": True,
        "iconic_cards": ["Base Set #15", "1st Edition Base Set #15"],
        "significance": 8, "cultural_score": 7,
        "notes": "Undervalued vs. Charizard/Blastoise — starter trio completionists drive demand",
    },
    {
        "name": "Rayquaza", "sport": "Pokemon", "hof": True,
        "iconic_cards": ["EX Deoxys Gold Star #107", "VMAX Alt Art"],
        "significance": 8, "cultural_score": 8,
        "notes": "Gold Star Rayquaza is a top-tier chase card across all eras",
    },
    {
        "name": "Gengar", "sport": "Pokemon", "hof": True,
        "iconic_cards": ["Fossil #5", "Skyridge #H9", "VMAX Alt Art"],
        "significance": 7, "cultural_score": 8,
        "notes": "Cult following — Skyridge Gengar and modern Alt Arts are highly collectible",
    },
    {
        "name": "Mew", "sport": "Pokemon", "hof": True,
        "iconic_cards": ["Ancient Mew Promo", "Celebrations Gold Mew"],
        "significance": 8, "cultural_score": 8,
        "notes": "Mysterious legendary — Ancient Mew promo is pure nostalgia",
    },
]


# --- Retired Legends (1980-Present) ---
# hof: Hall of Fame status, iconic_cards: key cards to search, significance: 1-10
LEGENDS_WATCHLIST = [
    # --- NBA ---
    {
        "name": "Michael Jordan", "sport": "NBA", "hof": True,
        "iconic_cards": ["1986 Fleer #57", "1997 Topps Chrome Refractor"],
        "significance": 10, "cultural_score": 10,
        "notes": "GOAT debate keeps cards forever relevant",
    },
    {
        "name": "Kobe Bryant", "sport": "NBA", "hof": True,
        "iconic_cards": ["1996 Topps Chrome #138", "1996 Topps Chrome Refractor"],
        "significance": 10, "cultural_score": 10,
        "notes": "Legacy continues to grow post-passing",
    },
    {
        "name": "LeBron James", "sport": "NBA", "hof": False,
        "iconic_cards": ["2003 Topps Chrome #111", "2003 Bowman Chrome"],
        "significance": 10, "cultural_score": 10,
        "notes": "Still active but nearing retirement — prices may surge on retirement",
    },
    {
        "name": "Stephen Curry", "sport": "NBA", "hof": False,
        "iconic_cards": ["2009 Topps Chrome #101", "2009 Panini Prizm"],
        "significance": 10, "cultural_score": 10,
        "notes": "Changed the game — still active, HOF lock. Cards will spike on retirement.",
    },
    {
        "name": "Kevin Durant", "sport": "NBA", "hof": False,
        "iconic_cards": ["2007 Topps Chrome #131", "2007 Bowman Chrome"],
        "significance": 9, "cultural_score": 9,
        "notes": "Still active, HOF lock. Underpriced vs. Curry/LeBron for similar legacy.",
    },
    {
        "name": "Dwyane Wade", "sport": "NBA", "hof": True,
        "iconic_cards": ["2003 Topps Chrome #115", "2003 Bowman Chrome"],
        "significance": 9, "cultural_score": 9,
        "notes": "HOF inducted — 3x champ, cultural icon. Cards still reasonable.",
    },
    {
        "name": "Magic Johnson", "sport": "NBA", "hof": True,
        "iconic_cards": ["1980 Topps #139"],
        "significance": 9, "cultural_score": 8,
        "notes": "Undervalued vs. Jordan/Kobe — HOF + cultural icon",
    },
    {
        "name": "Larry Bird", "sport": "NBA", "hof": True,
        "iconic_cards": ["1980 Topps #34"],
        "significance": 9, "cultural_score": 8,
        "notes": "80s nostalgia + rivalry with Magic keeps interest alive",
    },
    {
        "name": "Shaquille O'Neal", "sport": "NBA", "hof": True,
        "iconic_cards": ["1992 Topps Stadium Club", "1992 Shaq Rookie"],
        "significance": 9, "cultural_score": 9,
        "notes": "Media personality keeps name in spotlight — cards still affordable",
    },
    {
        "name": "Tim Duncan", "sport": "NBA", "hof": True,
        "iconic_cards": ["1997 Topps Chrome #115"],
        "significance": 9, "cultural_score": 6,
        "notes": "UNDERVALUED — greatest PF ever, quiet personality hurts card prices",
    },
    {
        "name": "Allen Iverson", "sport": "NBA", "hof": True,
        "iconic_cards": ["1996 Topps Chrome #171"],
        "significance": 8, "cultural_score": 9,
        "notes": "Cultural icon — cards below where significance suggests",
    },
    {
        "name": "Hakeem Olajuwon", "sport": "NBA", "hof": True,
        "iconic_cards": ["1986 Fleer #82"],
        "significance": 9, "cultural_score": 7,
        "notes": "Hidden gem — top 15 ever, 1986 Fleer still affordable",
    },
    {
        "name": "Charles Barkley", "sport": "NBA", "hof": True,
        "iconic_cards": ["1986 Fleer #7"],
        "significance": 8, "cultural_score": 9,
        "notes": "TV personality + HOF = undervalued cards",
    },
    {
        "name": "Patrick Ewing", "sport": "NBA", "hof": True,
        "iconic_cards": ["1986 Fleer #32"],
        "significance": 8, "cultural_score": 7,
        "notes": "1986 Fleer Ewing still relatively affordable for HOFer",
    },
    {
        "name": "David Robinson", "sport": "NBA", "hof": True,
        "iconic_cards": ["1989 Fleer #138"],
        "significance": 8, "cultural_score": 6,
        "notes": "Undervalued — 2x champ, MVP, HOF",
    },
    {
        "name": "Dirk Nowitzki", "sport": "NBA", "hof": True,
        "iconic_cards": ["1998 Topps Chrome #154"],
        "significance": 9, "cultural_score": 7,
        "notes": "International icon — cards affordable for his legacy",
    },
    {
        "name": "Kevin Garnett", "sport": "NBA", "hof": True,
        "iconic_cards": ["1995 Topps Chrome #115"],
        "significance": 8, "cultural_score": 7,
        "notes": "MVP + champion — underpriced relative to achievements",
    },
    # --- MLB ---
    {
        "name": "Ken Griffey Jr", "sport": "MLB", "hof": True,
        "iconic_cards": ["1989 Upper Deck #1"],
        "significance": 10, "cultural_score": 10,
        "notes": "THE iconic baseball card of the era — always in demand",
    },
    {
        "name": "Derek Jeter", "sport": "MLB", "hof": True,
        "iconic_cards": ["1993 SP #279"],
        "significance": 9, "cultural_score": 10,
        "notes": "Yankees legend — 1993 SP is blue chip",
    },
    {
        "name": "Mike Trout", "sport": "MLB", "hof": False,
        "iconic_cards": ["2011 Topps Update #US175", "2011 Bowman Chrome"],
        "significance": 10, "cultural_score": 8,
        "notes": "Best of his generation — injuries created buying window. HOF lock.",
    },
    {
        "name": "Ichiro Suzuki", "sport": "MLB", "hof": True,
        "iconic_cards": ["2001 Topps Chrome #151", "2001 Bowman Chrome"],
        "significance": 9, "cultural_score": 10,
        "notes": "International icon — huge following in Japan and US. Cards undervalued.",
    },
    {
        "name": "Pedro Martinez", "sport": "MLB", "hof": True,
        "iconic_cards": ["1991 Bowman #272", "1992 Donruss"],
        "significance": 9, "cultural_score": 8,
        "notes": "Most dominant pitching stretch ever — cards very affordable for his legacy",
    },
    {
        "name": "Mariano Rivera", "sport": "MLB", "hof": True,
        "iconic_cards": ["1992 Bowman #302"],
        "significance": 9, "cultural_score": 8,
        "notes": "Unanimous HOF — greatest closer ever. 1992 Bowman is the key card.",
    },
    {
        "name": "Cal Ripken Jr", "sport": "MLB", "hof": True,
        "iconic_cards": ["1982 Topps Traded #98T"],
        "significance": 9, "cultural_score": 8,
        "notes": "Iron Man — cards undervalued vs. significance",
    },
    {
        "name": "Nolan Ryan", "sport": "MLB", "hof": True,
        "iconic_cards": ["1968 Topps #177"],
        "significance": 9, "cultural_score": 8,
        "notes": "Pre-1980 rookie but career extended deep into 90s",
    },
    {
        "name": "Randy Johnson", "sport": "MLB", "hof": True,
        "iconic_cards": ["1989 Fleer #381"],
        "significance": 8, "cultural_score": 7,
        "notes": "Dominant pitcher — cards very affordable for HOFer",
    },
    {
        "name": "Greg Maddux", "sport": "MLB", "hof": True,
        "iconic_cards": ["1987 Donruss #36"],
        "significance": 8, "cultural_score": 6,
        "notes": "4 straight Cy Youngs — undervalued legend",
    },
    {
        "name": "Tony Gwynn", "sport": "MLB", "hof": True,
        "iconic_cards": ["1983 Topps #482"],
        "significance": 8, "cultural_score": 7,
        "notes": "Mr. Padre — legacy appreciated more over time",
    },
    # --- NFL ---
    {
        "name": "Joe Montana", "sport": "NFL", "hof": True,
        "iconic_cards": ["1981 Topps #216"],
        "significance": 10, "cultural_score": 9,
        "notes": "Top 3 QB ever — 1981 Topps is iconic",
    },
    {
        "name": "Jerry Rice", "sport": "NFL", "hof": True,
        "iconic_cards": ["1986 Topps #161"],
        "significance": 10, "cultural_score": 8,
        "notes": "GOAT WR — cards underpriced vs. Montana/Marino",
    },
    {
        "name": "Tom Brady", "sport": "NFL", "hof": False,
        "iconic_cards": ["2000 Bowman Chrome #236", "2000 Playoff Contenders Auto"],
        "significance": 10, "cultural_score": 10,
        "notes": "GOAT QB — prices spiked on retirement, may settle for buying window",
    },
    {
        "name": "Lawrence Taylor", "sport": "NFL", "hof": True,
        "iconic_cards": ["1982 Topps #434"],
        "significance": 10, "cultural_score": 8,
        "notes": "Changed the game — greatest defensive player ever. Cards undervalued.",
    },
    {
        "name": "Ray Lewis", "sport": "NFL", "hof": True,
        "iconic_cards": ["1996 Topps Chrome #55"],
        "significance": 9, "cultural_score": 9,
        "notes": "Iconic leader — HOF + cultural presence. Cards still affordable.",
    },
    {
        "name": "Emmitt Smith", "sport": "NFL", "hof": True,
        "iconic_cards": ["1990 Score Supplemental #101T", "1990 Topps Traded #27T"],
        "significance": 9, "cultural_score": 8,
        "notes": "All-time rushing leader — 90s Cowboys nostalgia. Cards underpriced.",
    },
    {
        "name": "Dan Marino", "sport": "NFL", "hof": True,
        "iconic_cards": ["1984 Topps #123"],
        "significance": 9, "cultural_score": 9,
        "notes": "Iconic career + Ace Ventura keeps cultural relevance alive",
    },
    {
        "name": "John Elway", "sport": "NFL", "hof": True,
        "iconic_cards": ["1984 Topps #63"],
        "significance": 9, "cultural_score": 7,
        "notes": "2x SB champ — cards affordable for his status",
    },
    {
        "name": "Barry Sanders", "sport": "NFL", "hof": True,
        "iconic_cards": ["1989 Score #257", "1989 Topps Traded #83T"],
        "significance": 9, "cultural_score": 8,
        "notes": "Mystique of early retirement keeps interest high",
    },
    {
        "name": "Walter Payton", "sport": "NFL", "hof": True,
        "iconic_cards": ["1976 Topps #148"],
        "significance": 10, "cultural_score": 8,
        "notes": "Pre-1980 rookie but career extended into mid-80s — man of the year award",
    },
    {
        "name": "Peyton Manning", "sport": "NFL", "hof": True,
        "iconic_cards": ["1998 Topps Chrome #165"],
        "significance": 9, "cultural_score": 9,
        "notes": "Media presence keeps name top of mind — cards still accessible",
    },
    {
        "name": "Brett Favre", "sport": "NFL", "hof": True,
        "iconic_cards": ["1991 Upper Deck #13"],
        "significance": 8, "cultural_score": 7,
        "notes": "Ironman streak + gunslinger mystique — affordable HOF cards",
    },
]
