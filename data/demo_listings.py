"""Demo eBay listings used when API keys are not yet configured."""

import random
import hashlib

# Card templates per player — realistic titles, price ranges
# Format: (title_template, price_low, price_high)
_CARD_TEMPLATES = {
    # --- NBA ---
    "Victor Wembanyama": [
        ("2023-24 Panini Prizm #{num} Victor Wembanyama RC Rookie", 25, 80),
        ("2023-24 Donruss Optic #{num} Victor Wembanyama Rookie Rated", 15, 55),
        ("2023-24 Panini Select #{num} Victor Wembanyama Concourse RC", 20, 65),
        ("2023-24 Panini Prizm Silver #{num} Victor Wembanyama RC", 80, 250),
        ("2023-24 Panini Mosaic #{num} Victor Wembanyama RC Rookie", 12, 40),
        ("2023-24 Hoops #{num} Victor Wembanyama RC Rookie Card", 5, 20),
        ("2023 Panini Prizm Victor Wembanyama Rookie PSA 10 Gem Mint", 120, 350),
        ("2023-24 Donruss #{num} Victor Wembanyama Rated Rookie RC", 8, 30),
    ],
    "LeBron James": [
        ("2003-04 Topps Chrome #{num} LeBron James RC Rookie", 800, 3500),
        ("2003-04 Upper Deck #{num} LeBron James Rookie Card", 150, 600),
        ("2023-24 Panini Prizm #{num} LeBron James Base", 3, 12),
        ("2003-04 Topps #{num} LeBron James RC Rookie Card", 200, 900),
        ("2019-20 Panini Prizm #{num} LeBron James Silver", 30, 95),
        ("LeBron James 2003 Bowman Chrome Rookie PSA 9", 1200, 4000),
        ("2023-24 Donruss #{num} LeBron James Base Card", 2, 8),
        ("2020-21 Panini Select #{num} LeBron James Concourse", 5, 18),
    ],
    "Michael Jordan": [
        ("1986-87 Fleer #57 Michael Jordan RC Rookie Card", 5000, 25000),
        ("1997-98 Topps Chrome #{num} Michael Jordan Refractor", 200, 800),
        ("1986-87 Fleer #57 Michael Jordan RC PSA 8 NM-MT", 8000, 18000),
        ("1995-96 Topps Chrome #{num} Michael Jordan", 40, 120),
        ("1992-93 Topps Gold #{num} Michael Jordan", 8, 30),
        ("1996-97 Topps Chrome #{num} Michael Jordan", 25, 85),
        ("1986 Fleer Michael Jordan Rookie Sticker #8", 400, 1500),
        ("1993-94 Upper Deck SE #{num} Michael Jordan", 3, 15),
    ],
    "Kobe Bryant": [
        ("1996-97 Topps Chrome #138 Kobe Bryant RC Rookie", 300, 1200),
        ("1996-97 Topps Chrome #138 Kobe Bryant RC Refractor", 3000, 12000),
        ("1996-97 Topps #{num} Kobe Bryant RC Rookie Card", 80, 350),
        ("2012-13 Panini Prizm #{num} Kobe Bryant Base", 15, 50),
        ("1996-97 Topps Chrome Kobe Bryant RC PSA 9", 800, 2500),
        ("2019-20 Panini Mosaic #{num} Kobe Bryant Base", 5, 20),
        ("1996-97 Flair Showcase #{num} Kobe Bryant RC", 60, 200),
        ("2007-08 Topps Chrome #{num} Kobe Bryant Refractor", 40, 150),
    ],
    "Anthony Edwards": [
        ("2020-21 Panini Prizm #{num} Anthony Edwards RC Rookie", 40, 150),
        ("2020-21 Donruss Optic #{num} Anthony Edwards Rated Rookie", 25, 90),
        ("2020-21 Panini Prizm Silver #{num} Anthony Edwards RC", 120, 400),
        ("2020-21 Select #{num} Anthony Edwards Concourse RC", 30, 100),
        ("2020-21 Hoops #{num} Anthony Edwards RC Rookie", 8, 25),
        ("2020-21 Panini Prizm Anthony Edwards RC PSA 10", 200, 500),
        ("2020-21 Donruss #{num} Anthony Edwards Rated Rookie", 10, 35),
        ("2020-21 Panini Mosaic #{num} Anthony Edwards RC", 15, 45),
    ],
    "Chet Holmgren": [
        ("2023-24 Panini Prizm #{num} Chet Holmgren RC Rookie", 8, 30),
        ("2023-24 Donruss Optic #{num} Chet Holmgren Rated Rookie", 5, 20),
        ("2023-24 Panini Prizm Silver #{num} Chet Holmgren RC", 30, 100),
        ("2023-24 Select #{num} Chet Holmgren Concourse RC", 10, 35),
        ("2023-24 Hoops #{num} Chet Holmgren RC Rookie Card", 3, 12),
        ("2023-24 Panini Prizm Chet Holmgren RC PSA 10", 50, 150),
    ],
    "Jared McCain": [
        ("2024-25 Panini Prizm #{num} Jared McCain RC Rookie", 15, 55),
        ("2024-25 Donruss Optic #{num} Jared McCain Rated Rookie", 10, 40),
        ("2024-25 Panini Prizm Silver #{num} Jared McCain RC", 50, 180),
        ("2024-25 Hoops #{num} Jared McCain RC Rookie Card", 4, 15),
        ("2024-25 Panini Mosaic #{num} Jared McCain RC", 8, 28),
    ],
    "Paolo Banchero": [
        ("2022-23 Panini Prizm #{num} Paolo Banchero RC Rookie", 15, 50),
        ("2022-23 Donruss Optic #{num} Paolo Banchero Rated Rookie", 10, 35),
        ("2022-23 Panini Prizm Silver #{num} Paolo Banchero RC", 50, 160),
        ("2022-23 Select #{num} Paolo Banchero Concourse RC", 12, 40),
        ("2022-23 Hoops #{num} Paolo Banchero RC Rookie", 4, 15),
        ("2022-23 Panini Prizm Paolo Banchero RC PSA 10", 80, 200),
    ],
    # --- NFL ---
    "Patrick Mahomes": [
        ("2017 Panini Prizm #{num} Patrick Mahomes RC Rookie", 150, 500),
        ("2017 Donruss Optic #{num} Patrick Mahomes Rated Rookie", 100, 350),
        ("2017 Panini Prizm Silver #{num} Patrick Mahomes RC", 400, 1200),
        ("2017 Topps Chrome #{num} Patrick Mahomes RC Rookie", 80, 250),
        ("2017 Panini Prizm Patrick Mahomes RC PSA 10", 500, 1500),
        ("2023 Panini Prizm #{num} Patrick Mahomes Base", 3, 12),
    ],
    "Tom Brady": [
        ("2000 Bowman Chrome #{num} Tom Brady RC Rookie", 2000, 8000),
        ("2000 Playoff Contenders #{num} Tom Brady Auto RC", 15000, 50000),
        ("2000 Bowman #{num} Tom Brady RC Rookie Card", 500, 2000),
        ("2020 Panini Prizm #{num} Tom Brady Base", 5, 20),
        ("2000 Bowman Chrome Tom Brady RC PSA 9", 5000, 15000),
        ("2023 Panini Prizm #{num} Tom Brady Base Card", 3, 10),
    ],
    "Joe Montana": [
        ("1981 Topps #216 Joe Montana RC Rookie Card", 200, 800),
        ("1981 Topps #216 Joe Montana RC PSA 8", 600, 2000),
        ("1981 Topps #216 Joe Montana RC PSA 7", 300, 900),
        ("1985 Topps #{num} Joe Montana", 5, 20),
        ("1990 Score #{num} Joe Montana", 2, 8),
        ("1981 Topps Joe Montana Rookie PSA 9 Mint", 2000, 6000),
    ],
    "Jerry Rice": [
        ("1986 Topps #161 Jerry Rice RC Rookie Card", 80, 300),
        ("1986 Topps #161 Jerry Rice RC PSA 8", 250, 700),
        ("1986 Topps #161 Jerry Rice RC PSA 9", 600, 2000),
        ("1990 Score #{num} Jerry Rice", 2, 8),
        ("1986 Topps Jerry Rice Rookie Card Raw", 60, 200),
    ],
    # --- MLB ---
    "Ken Griffey Jr": [
        ("1989 Upper Deck #1 Ken Griffey Jr RC Rookie", 80, 300),
        ("1989 Upper Deck #1 Ken Griffey Jr RC PSA 9", 300, 900),
        ("1989 Upper Deck #1 Ken Griffey Jr RC PSA 10", 2000, 6000),
        ("1989 Donruss #{num} Ken Griffey Jr RC Rated Rookie", 15, 50),
        ("1989 Fleer #{num} Ken Griffey Jr RC Rookie", 10, 35),
        ("1989 Topps Traded #{num} Ken Griffey Jr RC", 12, 40),
    ],
    "Derek Jeter": [
        ("1993 SP #279 Derek Jeter RC Rookie Card", 150, 600),
        ("1993 SP #279 Derek Jeter Foil RC PSA 8", 400, 1200),
        ("1993 Upper Deck #{num} Derek Jeter RC Rookie", 15, 50),
        ("1993 Topps #{num} Derek Jeter RC Rookie Card", 10, 30),
        ("1993 SP Derek Jeter Rookie PSA 9", 800, 2500),
        ("2014 Topps Chrome #{num} Derek Jeter Base", 3, 10),
    ],
    "Shohei Ohtani": [
        ("2018 Topps Chrome #{num} Shohei Ohtani RC Rookie", 40, 150),
        ("2018 Bowman Chrome #{num} Shohei Ohtani RC", 30, 100),
        ("2018 Topps Chrome #{num} Shohei Ohtani RC Refractor", 100, 400),
        ("2018 Topps #{num} Shohei Ohtani RC Rookie Card", 15, 55),
        ("2018 Topps Chrome Shohei Ohtani RC PSA 10", 200, 600),
        ("2024 Topps Chrome #{num} Shohei Ohtani Base", 3, 12),
    ],
}

# Generic templates for players not in the specific list
_GENERIC_NBA = [
    ("{name} 2023-24 Panini Prizm #{num} Base Card", 2, 15),
    ("{name} 2023-24 Donruss #{num} Rated Rookie", 3, 20),
    ("{name} 2023-24 Panini Prizm Silver #{num}", 15, 60),
    ("{name} 2023-24 Select #{num} Concourse", 5, 25),
    ("{name} 2023-24 Hoops #{num} Base Card", 1, 8),
    ("{name} 2023-24 Panini Mosaic #{num}", 3, 18),
    ("{name} Panini Prizm Rookie Card PSA 10", 40, 150),
    ("{name} 2023-24 Donruss Optic #{num}", 4, 22),
]

_GENERIC_NFL = [
    ("{name} 2023 Panini Prizm #{num} Base Card", 2, 12),
    ("{name} 2023 Donruss Optic #{num} Rated Rookie", 3, 18),
    ("{name} 2023 Panini Prizm Silver #{num}", 12, 50),
    ("{name} 2023 Select #{num} Concourse", 4, 20),
    ("{name} 2023 Mosaic #{num} Base Card", 2, 10),
    ("{name} Panini Prizm Rookie PSA 10", 35, 120),
]

_GENERIC_MLB = [
    ("{name} 2024 Topps Chrome #{num} Base Card", 2, 12),
    ("{name} 2024 Bowman Chrome #{num} Rookie", 3, 18),
    ("{name} 2024 Topps Chrome #{num} Refractor", 12, 50),
    ("{name} 2024 Topps #{num} Base Card", 1, 8),
    ("{name} 2024 Topps Heritage #{num}", 2, 10),
    ("{name} Topps Chrome Rookie PSA 10", 30, 100),
]

_GENERIC_BY_SPORT = {
    "NBA": _GENERIC_NBA,
    "NFL": _GENERIC_NFL,
    "MLB": _GENERIC_MLB,
}

# Card type price multipliers
_TYPE_MULTIPLIERS = {
    "Any": 1.0,
    "Rookie": 1.2,
    "Prizm": 1.3,
    "Prizm Silver": 2.5,
    "Refractor": 2.0,
    "Auto": 4.0,
    "Numbered": 3.0,
    "PSA 10": 3.5,
    "PSA 9": 2.0,
    "BGS 9.5": 2.2,
    "1st Bowman": 1.8,
}


def _seed_from_name(name: str) -> int:
    """Deterministic seed so the same player always gets the same demo listings."""
    return int(hashlib.md5(name.encode()).hexdigest()[:8], 16)


def generate_demo_listings(player_name: str, sport: str = "NBA", card_type: str = "Any", limit: int = 50) -> list[dict]:
    """Generate realistic demo eBay listings for a player."""
    seed = _seed_from_name(player_name + sport + card_type)
    rng = random.Random(seed)

    # Find templates — check specific list first, then generic
    templates = _CARD_TEMPLATES.get(player_name, [])
    if not templates:
        # Try partial match
        for key in _CARD_TEMPLATES:
            if key.lower() in player_name.lower() or player_name.lower() in key.lower():
                templates = _CARD_TEMPLATES[key]
                break

    if not templates:
        # Use generic templates
        generic = _GENERIC_BY_SPORT.get(sport.upper(), _GENERIC_NBA)
        templates = [(t[0].replace("{name}", player_name), t[1], t[2]) for t in generic]

    multiplier = _TYPE_MULTIPLIERS.get(card_type, 1.0)
    listings = []

    for i in range(min(limit, len(templates) * 3)):
        template = templates[i % len(templates)]
        title_tmpl, price_low, price_high = template

        # Generate card number
        num = rng.randint(1, 350)
        title = title_tmpl.replace("{num}", str(num))

        # Add card type to title if filtering
        if card_type != "Any" and card_type.lower() not in title.lower():
            title = f"{title} {card_type}"

        # Vary price within range
        base_price = rng.uniform(price_low, price_high) * multiplier
        # Add some variance per listing
        price = round(base_price * rng.uniform(0.7, 1.4), 2)
        shipping = rng.choice([0, 0, 0, 3.99, 4.50, 5.00, 5.99])

        # Weighted buying format: ~70% BIN, ~20% Auction, ~10% Best Offer
        fmt_roll = rng.random()
        if fmt_roll < 0.70:
            buying_format = "BIN"
        elif fmt_roll < 0.90:
            buying_format = "Auction"
            # Auction prices reflect current bid (30-60% of BIN price)
            price = round(price * rng.uniform(0.3, 0.6), 2)
        else:
            buying_format = "BIN"  # Best Offer still shows BIN price

        # Build a search URL from the listing title so clicks find the actual card
        search_terms = title.replace("#", "").replace("  ", " ")
        search_query = search_terms.replace(" ", "+")
        ebay_url = f"https://www.ebay.com/sch/i.html?_nkw={search_query}&_sacat=212"

        listings.append({
            "title": title,
            "price": price,
            "shipping": shipping,
            "total": round(price + shipping, 2),
            "condition": rng.choice(["New", "Like New", "Very Good", "Pre-Owned"]),
            "url": ebay_url,
            "image_url": f"https://placehold.co/120x170/1a1f2e/fafafa?text={player_name.split()[0]}",
            "item_id": f"DEMO-{seed}-{i}",
            "buying_format": buying_format,
        })

    # Sort by price (ascending)
    listings.sort(key=lambda x: x["total"])
    return listings[:limit]


def generate_demo_sold_listings(
    player_name: str, sport: str = "NBA", card_type: str = "Any", limit: int = 50
) -> list[dict]:
    """Generate realistic demo sold/completed eBay listings for a player."""
    from datetime import datetime, timedelta

    # Different salt so sold data differs from active data
    seed = _seed_from_name(player_name + sport + card_type + "_sold")
    rng = random.Random(seed)

    templates = _CARD_TEMPLATES.get(player_name, [])
    if not templates:
        for key in _CARD_TEMPLATES:
            if key.lower() in player_name.lower() or player_name.lower() in key.lower():
                templates = _CARD_TEMPLATES[key]
                break

    if not templates:
        generic = _GENERIC_BY_SPORT.get(sport.upper(), _GENERIC_NBA)
        templates = [(t[0].replace("{name}", player_name), t[1], t[2]) for t in generic]

    multiplier = _TYPE_MULTIPLIERS.get(card_type, 1.0)
    listings = []
    now = datetime.now()

    for i in range(min(limit, len(templates) * 3)):
        template = templates[i % len(templates)]
        title_tmpl, price_low, price_high = template

        num = rng.randint(1, 350)
        title = title_tmpl.replace("{num}", str(num))

        if card_type != "Any" and card_type.lower() not in title.lower():
            title = f"{title} {card_type}"

        # Sold prices skew slightly lower than active ask prices
        base_price = rng.uniform(price_low, price_high) * multiplier * 0.85
        sold_price = round(base_price * rng.uniform(0.6, 1.3), 2)
        shipping = rng.choice([0, 0, 0, 3.99, 4.50, 5.00, 5.99])

        # Spread sold dates across the last 90 days
        days_ago = rng.randint(0, 90)
        sold_date = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d")

        listing_type = rng.choice(["Auction", "Auction", "Buy It Now", "Best Offer"])

        search_terms = title.replace("#", "").replace("  ", " ")
        search_query = search_terms.replace(" ", "+")
        sold_url = f"https://www.ebay.com/sch/i.html?_nkw={search_query}&_sacat=212&LH_Complete=1&LH_Sold=1"

        listings.append({
            "title": title,
            "sold_price": sold_price,
            "shipping": shipping,
            "total": round(sold_price + shipping, 2),
            "condition": rng.choice(["New", "Like New", "Very Good", "Pre-Owned"]),
            "sold_date": sold_date,
            "listing_type": listing_type,
            "url": sold_url,
            "item_id": f"DEMO-SOLD-{seed}-{i}",
        })

    listings.sort(key=lambda x: x["sold_date"], reverse=True)
    return listings[:limit]
