"""Deterministic synthetic price history for demo mode."""

import hashlib
import math
from datetime import datetime, timedelta


def _seed_from_key(key: str) -> int:
    """Deterministic seed from a string key."""
    return int(hashlib.md5(key.encode()).hexdigest()[:8], 16)


def generate_demo_price_history(
    player: str,
    sport: str = "NBA",
    card_type: str = "Any",
    days: int = 365,
) -> list[dict]:
    """Generate deterministic price history using a seeded random walk.

    Returns list of dicts with keys: date (str), price (float), volume (int).
    """
    import random

    key = f"{player}|{sport}|{card_type}"
    seed = _seed_from_key(key)
    rng = random.Random(seed)

    # Base price derived from seed (range $5 - $500)
    base_price = 5 + (seed % 495)

    # Drift: slight upward bias for breakout players
    drift = 0.0002
    volatility = 0.03

    prices = []
    current = float(base_price)
    today = datetime.now().date()
    start_date = today - timedelta(days=days)

    for i in range(days + 1):
        date = start_date + timedelta(days=i)

        # Random walk with drift
        shock = rng.gauss(0, 1)
        current *= math.exp(drift + volatility * shock)

        # Add seasonal effects (slight bump around holidays)
        day_of_year = date.timetuple().tm_yday
        seasonal = 1.0 + 0.05 * math.sin(2 * math.pi * day_of_year / 365)
        price = max(current * seasonal, 0.50)

        # Volume: 1-20 sales per day, higher on weekends
        weekday = date.weekday()
        base_vol = 8 if weekday < 5 else 12
        volume = max(1, int(rng.gauss(base_vol, 3)))

        prices.append({
            "date": date.strftime("%Y-%m-%d"),
            "price": round(price, 2),
            "volume": volume,
        })

    return prices
