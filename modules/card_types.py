"""Card variation definitions and display helpers."""

from config.card_keywords import CARD_TYPES, SPORT_CARD_BRANDS, ICONIC_SETS


def get_card_type_options() -> list[str]:
    """Return list of card types for dropdown."""
    return list(CARD_TYPES.keys())


def get_brand_options(sport: str) -> list[str]:
    """Return sport-specific card brands."""
    return SPORT_CARD_BRANDS.get(sport.upper(), [])


def get_iconic_set_options() -> list[str]:
    """Return list of iconic set names for legend searches."""
    return list(ICONIC_SETS.keys())


def get_iconic_set_query(set_name: str) -> str:
    """Return eBay search string for an iconic set."""
    return ICONIC_SETS.get(set_name, set_name)
