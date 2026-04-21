"""OCR Card Scanner — zero-cost Tesseract-based card identification."""

import re

from config.settings import OCR_CONFIDENCE_THRESHOLD, OCR_MIN_TEXT_LENGTH
from config.card_keywords import SPORT_CARD_BRANDS

# ---------------------------------------------------------------------------
# Popular Pokemon names for detection (covers ~50 most collected)
# ---------------------------------------------------------------------------
_POPULAR_POKEMON = {
    "Charizard", "Pikachu", "Mewtwo", "Blastoise", "Venusaur",
    "Gengar", "Eevee", "Umbreon", "Espeon", "Sylveon",
    "Rayquaza", "Lugia", "Ho-Oh", "Mew", "Dragonite",
    "Gyarados", "Alakazam", "Machamp", "Snorlax", "Arcanine",
    "Ninetales", "Jolteon", "Flareon", "Vaporeon", "Glaceon",
    "Leafeon", "Garchomp", "Lucario", "Gardevoir", "Tyranitar",
    "Salamence", "Metagross", "Darkrai", "Giratina", "Dialga",
    "Palkia", "Arceus", "Reshiram", "Zekrom", "Kyurem",
    "Greninja", "Mimikyu", "Zacian", "Zamazenta", "Miraidon",
    "Koraidon", "Charmander", "Squirtle", "Bulbasaur", "Magikarp",
}

# Lowercased for fast lookups
_POPULAR_POKEMON_LOWER = {p.lower() for p in _POPULAR_POKEMON}

# Signals that indicate a Pokemon card (found in OCR text)
_POKEMON_SIGNALS = {
    "pokemon", "pokémon", "tcg", "trainer", "energy",
    "hp", "weakness", "resistance", "retreat", "evolves",
    "stage 1", "stage 2", "basic", "gx", "vmax", "vstar",
    "illustrated by", "rarity",
}

# Common keywords to skip when guessing player names
_NAME_SKIP_WORDS = {
    "panini", "prizm", "topps", "chrome", "bowman", "donruss", "optic",
    "select", "mosaic", "contenders", "fleer", "upper", "deck", "hoops",
    "rookie", "auto", "autograph", "refractor", "holo", "rare",
    "base", "set", "card", "edition", "numbered", "parallel",
    "silver", "gold", "red", "blue", "green", "orange", "pink", "black",
    "national", "treasures", "immaculate", "flawless", "obsidian",
    "pokemon", "pokémon", "tcg", "trainer", "energy",
    "mint", "near", "excellent", "good", "poor",
    "psa", "bgs", "sgc", "cgc",
}

# Variant keywords to look for in OCR text
_VARIANT_KEYWORDS = [
    "Prizm Silver", "Silver Prizm", "Silver",
    "Holo Rare", "Reverse Holo", "Holo",
    "Full Art", "Alt Art", "Alternative Art",
    "Rainbow Rare", "Rainbow",
    "Gold", "Red", "Blue", "Green", "Orange", "Pink",
    "Refractor", "X-Fractor", "Xfractor",
    "1st Edition", "First Edition",
    "Shadowless",
    "VMAX", "VSTAR", "EX", "GX",
    "Secret Rare", "Illustration Rare", "Special Art Rare",
    "Mojo", "Blue Wave", "Pink Ice",
]


def _extract_text_from_image(image_bytes: bytes) -> str:
    """Run Tesseract OCR on raw image bytes. Returns extracted text or empty string."""
    try:
        import pytesseract
        from PIL import Image
        import io
    except ImportError:
        return ""

    try:
        img = Image.open(io.BytesIO(image_bytes))
        # Convert to RGB if needed (handles RGBA, palette, etc.)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception:
        return ""


def _extract_year(text: str) -> str | None:
    """Extract card year like '2023', '2023-24', or '2023/24'."""
    # Try 2-season format first (2023-24, 2023/24)
    m = re.search(r"((?:19|20)\d{2})[-/](\d{2})\b", text)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    # Single year
    m = re.search(r"\b((?:19|20)\d{2})\b", text)
    if m:
        return m.group(1)
    return None


def _extract_card_number(text: str) -> str | None:
    """Extract card number like '#220', '220/300', 'No. 55'."""
    # #220 or # 220
    m = re.search(r"#\s*(\d{1,4})", text)
    if m:
        return f"#{m.group(1)}"
    # 220/300 (card X of Y)
    m = re.search(r"\b(\d{1,4})\s*/\s*(\d{1,4})\b", text)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    # No. 55 or No 55
    m = re.search(r"\bNo\.?\s*(\d{1,4})\b", text, re.IGNORECASE)
    if m:
        return f"#{m.group(1)}"
    return None


def _detect_sport(text: str) -> str:
    """Detect whether the card is Pokemon or a sports card."""
    text_lower = text.lower()

    # Check for Pokemon signals
    pokemon_hits = sum(1 for sig in _POKEMON_SIGNALS if sig in text_lower)
    if pokemon_hits >= 2:
        return "Pokemon"

    # Check if a known Pokemon name appears
    for name in _POPULAR_POKEMON_LOWER:
        if name in text_lower:
            return "Pokemon"

    # Default to NBA (most common sports card)
    return "NBA"


def _match_set_name(text: str, sport: str) -> str | None:
    """Fuzzy-match OCR text against known card brands for the detected sport."""
    text_lower = text.lower()
    brands = SPORT_CARD_BRANDS.get(sport, [])
    # Also check all sports if no match in detected sport
    all_brands = brands + [b for s, bl in SPORT_CARD_BRANDS.items() if s != sport for b in bl]

    for brand in brands:
        if brand.lower() in text_lower:
            return brand

    # Fallback: check other sports' brands
    for brand in all_brands:
        if brand.lower() in text_lower:
            return brand

    return None


def _match_variant(text: str) -> str:
    """Scan OCR text for variant/parallel keywords. Returns first match or 'Base'."""
    text_lower = text.lower()
    for kw in _VARIANT_KEYWORDS:
        if kw.lower() in text_lower:
            return kw
    return "Base"


def _extract_player_name(text: str, sport: str) -> str | None:
    """Best-effort player/character name extraction from OCR text.

    For Pokemon: matches against popular Pokemon names.
    For sports: heuristic — first line that looks like a name
    (2+ capitalized words, not a known keyword).
    """
    text_lower = text.lower()

    # Pokemon: look for known names
    if sport == "Pokemon":
        for name in _POPULAR_POKEMON:
            if name.lower() in text_lower:
                return name
        return None

    # Sports: scan lines for something that looks like a name
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue

        # Remove common noise characters
        cleaned = re.sub(r"[^a-zA-Z\s.'-]", "", line).strip()
        if not cleaned:
            continue

        words = cleaned.split()
        if len(words) < 2 or len(words) > 5:
            continue

        # Skip if any word is a known keyword
        if any(w.lower() in _NAME_SKIP_WORDS for w in words):
            continue

        # Check that words look like proper names (capitalized or all-caps)
        if all(w[0].isupper() or w.isupper() for w in words if len(w) > 1):
            return " ".join(words)

    return None


def ocr_scan_card_image(image_bytes: bytes, file_name: str = "card.jpg") -> dict:
    """Main OCR scanner entry point.

    Returns the same dict shape as scan_card_image():
    player_name, year, set_name, card_number, variant, sport,
    condition_estimate, confidence.
    Returns error dict on failure.
    """
    raw_text = _extract_text_from_image(image_bytes)

    if not raw_text or len(raw_text) < OCR_MIN_TEXT_LENGTH:
        return {"error": "Could not read card text. Try a clearer photo or upgrade to Pro for AI-powered scanning."}

    sport = _detect_sport(raw_text)
    year = _extract_year(raw_text)
    card_number = _extract_card_number(raw_text)
    set_name = _match_set_name(raw_text, sport)
    variant = _match_variant(raw_text)
    player_name = _extract_player_name(raw_text, sport)

    # Count how many fields we successfully extracted
    fields_found = sum(1 for v in [player_name, year, set_name, card_number] if v is not None)
    confidence = "medium" if fields_found >= OCR_CONFIDENCE_THRESHOLD else "low"

    return {
        "player_name": player_name,
        "year": year,
        "set_name": set_name,
        "card_number": card_number,
        "variant": variant,
        "sport": sport,
        "condition_estimate": "N/A (Pro)",
        "confidence": confidence,
    }
