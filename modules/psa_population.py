"""PSA Population Reports — public API wrapper + fallback demo data."""

import hashlib
import time

import requests

from config.settings import PSA_API_BASE_URL, PSA_CACHE_TTL
from data.demo_psa_pop import generate_demo_psa_pop

# Simple in-memory cache: key -> (timestamp, data)
_psa_cache: dict[str, tuple[float, dict]] = {}


def _cache_key(player: str, year: str, set_name: str, card_number: str) -> str:
    raw = f"{player}|{year}|{set_name}|{card_number}"
    return hashlib.md5(raw.encode()).hexdigest()


def lookup_psa_population(
    player: str,
    year: str = "",
    set_name: str = "",
    card_number: str = "",
) -> dict:
    """Look up PSA population data.

    Tries the PSA public API first, falls back to demo data.
    Results are cached for PSA_CACHE_TTL seconds.
    """
    key = _cache_key(player, year, set_name, card_number)

    # Check cache
    if key in _psa_cache:
        ts, data = _psa_cache[key]
        if time.time() - ts < PSA_CACHE_TTL:
            return data

    # Try PSA public API
    data = _try_psa_api(player, year, set_name, card_number)
    if data is None:
        # Fallback to demo data
        card_type = set_name if set_name else "Any"
        data = generate_demo_psa_pop(player, card_type)
        data["source"] = "demo"
    else:
        data["source"] = "psa_api"

    _psa_cache[key] = (time.time(), data)
    return data


def _try_psa_api(
    player: str,
    year: str,
    set_name: str,
    card_number: str,
) -> dict | None:
    """Attempt to fetch from PSA public API. Returns None on failure."""
    try:
        params = {"playerName": player}
        if year:
            params["year"] = year
        if set_name:
            params["setName"] = set_name
        if card_number:
            params["cardNumber"] = card_number

        response = requests.get(
            f"{PSA_API_BASE_URL}/pop/search",
            params=params,
            timeout=5,
        )

        if response.status_code != 200:
            return None

        api_data = response.json()
        if not api_data or not isinstance(api_data, dict):
            return None

        # Parse API response into our standard format
        items = api_data.get("items", [])
        if not items:
            return None

        item = items[0]
        grade_distribution = {}
        total_pop = 0
        for grade_info in item.get("grades", []):
            grade = str(grade_info.get("grade", ""))
            count = grade_info.get("count", 0)
            if grade and count:
                grade_distribution[grade] = count
                total_pop += count

        if not grade_distribution:
            return None

        gem_count = grade_distribution.get("10", 0)
        gem_rate = round(gem_count / total_pop * 100, 1) if total_pop > 0 else 0

        # Pop higher: cumulative
        pop_higher = {}
        cumulative = 0
        for grade in ["10", "9", "8", "7", "6", "5", "4", "3", "2", "1"]:
            cumulative += grade_distribution.get(grade, 0)
            pop_higher[grade] = cumulative

        return {
            "total_pop": total_pop,
            "grade_distribution": grade_distribution,
            "gem_rate": gem_rate,
            "pop_higher": pop_higher,
            "player": player,
            "card_type": set_name or "Any",
        }

    except Exception:
        return None
