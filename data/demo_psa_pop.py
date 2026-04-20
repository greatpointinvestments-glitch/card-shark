"""Deterministic demo PSA population data."""

import hashlib


def _seed_from_key(key: str) -> int:
    return int(hashlib.md5(key.encode()).hexdigest()[:8], 16)


def generate_demo_psa_pop(player: str, card_type: str = "Any") -> dict:
    """Generate deterministic demo PSA population data.

    Returns dict with total_pop, grade_distribution (dict grade -> count),
    gem_rate (PSA 10 percentage), and pop_higher (total at each grade+).
    """
    import random

    seed = _seed_from_key(f"{player}|{card_type}|psa")
    rng = random.Random(seed)

    # Total population: 50 - 50,000 depending on player popularity
    total_pop = 50 + (seed % 49950)

    # Realistic grade distribution:
    # PSA 10: ~15%, PSA 9: ~35%, PSA 8: ~25%, PSA 7: ~12%, PSA 6: ~7%, <=5: ~6%
    ratios = {
        "10": 0.15 + rng.uniform(-0.05, 0.05),
        "9": 0.35 + rng.uniform(-0.05, 0.05),
        "8": 0.25 + rng.uniform(-0.03, 0.03),
        "7": 0.12 + rng.uniform(-0.03, 0.03),
        "6": 0.07 + rng.uniform(-0.02, 0.02),
        "5": 0.03 + rng.uniform(-0.01, 0.01),
        "4": 0.02 + rng.uniform(-0.005, 0.005),
        "3": 0.01,
    }

    # Normalize
    total_ratio = sum(ratios.values())
    grade_distribution = {}
    for grade, ratio in ratios.items():
        grade_distribution[grade] = max(1, round(total_pop * ratio / total_ratio))

    # Adjust total to match
    actual_total = sum(grade_distribution.values())
    gem_rate = round(grade_distribution["10"] / actual_total * 100, 1) if actual_total > 0 else 0

    # Pop higher: cumulative from top
    pop_higher = {}
    cumulative = 0
    for grade in ["10", "9", "8", "7", "6", "5", "4", "3"]:
        cumulative += grade_distribution.get(grade, 0)
        pop_higher[grade] = cumulative

    return {
        "total_pop": actual_total,
        "grade_distribution": grade_distribution,
        "gem_rate": gem_rate,
        "pop_higher": pop_higher,
        "player": player,
        "card_type": card_type,
    }
