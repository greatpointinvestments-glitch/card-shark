"""eBay search templates for different card types.

CARD_TYPES order matters — the UI renders this as a flat dropdown and users
read top-down. Ordered by: most-used first, then grouped by category.
"""

# Each value is the eBay keyword suffix appended to the player name
CARD_TYPES = {
    # --- Quick picks ---
    "Any": "",
    "Rookie": "rookie RC",
    "Rookie Auto": "rookie auto autograph",
    "Auto": "autograph auto",
    "Patch Auto": "patch auto RPA",
    "Numbered": "numbered",
    "1st Bowman": "bowman 1st chrome",

    # --- Grading (raw and graded) ---
    "Raw (Ungraded)": "raw ungraded",
    "PSA 10": "PSA 10",
    "PSA 9.5": "PSA 9.5",
    "PSA 9": "PSA 9",
    "PSA 8": "PSA 8",
    "BGS 10": "BGS 10 pristine",
    "BGS 9.5": "BGS 9.5 gem mint",
    "BGS 9": "BGS 9",
    "SGC 10": "SGC 10",
    "SGC 9.5": "SGC 9.5",
    "CGC 10": "CGC 10",

    # --- Prizm parallels ---
    "Prizm (Base)": "prizm",
    "Prizm Silver": "prizm silver",
    "Prizm Red White Blue": "prizm red white blue",
    "Prizm Blue": "prizm blue",
    "Prizm Red": "prizm red",
    "Prizm Green": "prizm green",
    "Prizm Orange": "prizm orange",
    "Prizm Pink": "prizm pink",
    "Prizm Gold /10": "prizm gold /10",
    "Prizm Black 1/1": "prizm black 1/1",
    "Prizm Blue Wave": "prizm blue wave",
    "Prizm Pink Ice": "prizm pink ice",
    "Prizm Mojo": "prizm mojo",

    # --- Refractors (Topps Chrome, Bowman Chrome) ---
    "Refractor (Base)": "refractor",
    "X-Fractor": "xfractor x-fractor",
    "Blue Refractor": "blue refractor",
    "Red Refractor": "red refractor",
    "Orange Refractor": "orange refractor",
    "Gold Refractor /50": "gold refractor /50",
    "Red Refractor /5": "red refractor /5",
    "Superfractor 1/1": "superfractor 1/1",
    "Atomic Refractor": "atomic refractor",

    # --- Optic / Select / Mosaic ---
    "Optic Holo": "optic holo",
    "Optic Silver": "optic silver holo",
    "Optic Gold /10": "optic gold /10",
    "Select Concourse": "select concourse",
    "Select Premier": "select premier",
    "Select Courtside": "select courtside",
    "Select Tie-Dye": "select tie dye",
    "Mosaic": "mosaic",
    "Mosaic Silver": "mosaic silver",

    # --- Inserts & hits ---
    "Patch / Jersey": "patch jersey relic",
    "Logoman 1/1": "logoman 1/1",
    "Shield 1/1": "shield 1/1",

    # --- Serial numbered tiers ---
    "/99": "/99",
    "/25": "/25",
    "/10": "/10",
    "/5": "/5",
    "1/1": "1/1 one of one",

    # --- Pokemon card types ---
    "Holo Rare": "holo rare",
    "Reverse Holo": "reverse holo",
    "Full Art": "full art",
    "Alt Art": "alt art alternative",
    "Rainbow Rare": "rainbow rare",
    "VMAX": "VMAX",
    "VSTAR": "VSTAR",
    "EX": "ex",
    "GX": "GX",
    "1st Edition": "1st edition first",
    "Shadowless": "shadowless",
    "Gold Star": "gold star",
    "Secret Rare": "secret rare",
    "Illustration Rare": "illustration rare",
    "Special Art Rare": "special art rare SAR",
}

# Sport-specific card brand keywords
SPORT_CARD_BRANDS = {
    "NBA": [
        "Panini Prizm", "Topps Chrome", "Donruss Optic", "Select", "Mosaic",
        "Contenders", "National Treasures", "Immaculate", "Flawless", "Hoops",
        "Court Kings", "Crown Royale", "Obsidian", "Origins", "Spectra",
        "Fleer", "Upper Deck",
    ],
    "NFL": [
        "Panini Prizm", "Donruss Optic", "Select", "Mosaic", "Contenders",
        "National Treasures", "Immaculate", "Flawless", "Topps Chrome",
        "Obsidian", "Spectra", "Score", "Absolute", "Phoenix",
    ],
    "MLB": [
        "Topps Chrome", "Bowman Chrome", "Bowman Draft", "Panini Prizm",
        "Topps Heritage", "Topps Finest", "Topps Update", "Donruss Optic",
        "Upper Deck", "Topps Allen & Ginter", "Stadium Club",
        "Bowman Sterling", "Topps Tier One",
    ],
    "Pokemon": [
        "Base Set", "Jungle", "Fossil", "Team Rocket", "Gym Heroes",
        "Gym Challenge", "Neo Genesis", "Neo Discovery", "Neo Revelation",
        "Neo Destiny", "Expedition", "Aquapolis", "Skyridge",
        "EX Ruby & Sapphire", "EX FireRed & LeafGreen",
        "Diamond & Pearl", "Platinum", "HeartGold SoulSilver",
        "Black & White", "XY", "Sun & Moon", "Sword & Shield",
        "Scarlet & Violet", "Obsidian Flames", "Paldea Evolved",
        "151", "Surging Sparks", "Prismatic Evolutions",
    ],
}

# Iconic card sets for retired player searches
ICONIC_SETS = {
    "1986 Fleer (Basketball)": "1986 fleer basketball",
    "1986-87 Fleer": "1986-87 fleer",
    "1989 Upper Deck (Baseball)": "1989 upper deck baseball",
    "1996 Topps Chrome": "1996 topps chrome",
    "1998 Topps Chrome": "1998 topps chrome",
    "2003 Topps Chrome": "2003 topps chrome",
    "2003-04 Topps Chrome": "2003-04 topps chrome",
    "1984 Topps (Football)": "1984 topps football",
    "1984 Donruss (Baseball)": "1984 donruss baseball",
    "1993 SP (Baseball)": "1993 SP baseball",
    "1993-94 SP (Basketball)": "1993-94 SP basketball",
    "2009 Topps Chrome": "2009 topps chrome",
    "2009 Bowman Chrome": "2009 bowman chrome draft",
    "1957 Topps (Football)": "1957 topps football",
    "1952 Topps (Baseball)": "1952 topps baseball",
    "1989 Score (Football)": "1989 score football",
    "2000 Playoff Contenders": "2000 playoff contenders",
    "2012 Topps Chrome (Football)": "2012 topps chrome football",
    "2017 Panini Prizm (Football)": "2017 panini prizm football",
    "2018 Panini Prizm (Basketball)": "2018 panini prizm basketball",
    # --- Pokemon ---
    "Base Set (1999)": "base set 1999 pokemon",
    "Base Set Shadowless": "base set shadowless pokemon",
    "Base Set 1st Edition": "base set 1st edition pokemon",
    "Jungle (1999)": "jungle 1999 pokemon",
    "Fossil (1999)": "fossil 1999 pokemon",
    "Team Rocket (2000)": "team rocket 2000 pokemon",
    "Neo Genesis (2000)": "neo genesis 2000 pokemon",
    "Skyridge (2003)": "skyridge 2003 pokemon",
    "EX FireRed & LeafGreen (2004)": "ex firered leafgreen 2004 pokemon",
    "Scarlet & Violet 151 (2023)": "scarlet violet 151 2023 pokemon",
}


def build_search_query(
    player_name: str,
    sport: str,
    card_type: str = "Any",
    year: str | None = None,
    set_name: str | None = None,
) -> str:
    """Build an eBay search query string for a player + card type.

    Optional year and set_name narrow the search significantly.
    """
    parts = [player_name]
    if year:
        parts.append(year.strip())
    if set_name:
        parts.append(set_name.strip())
    parts.append("pokemon card" if sport == "Pokemon" else "card")
    suffix = CARD_TYPES.get(card_type, "")
    if suffix:
        parts.append(suffix)
    return " ".join(parts)
