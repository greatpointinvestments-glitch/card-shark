"""Card Scanner — Claude Vision API card identification."""

import base64
import json
from datetime import datetime

from config.settings import ANTHROPIC_API_KEY, SCANNER_MODEL, SCANNER_MAX_TOKENS


def _anthropic_is_configured() -> bool:
    """Check if the Anthropic API key is set."""
    return bool(ANTHROPIC_API_KEY and ANTHROPIC_API_KEY not in ("", "your_key_here"))


def _build_scan_prompt() -> str:
    """Structured prompt asking Claude to identify a sports card from an image."""
    return """You are a trading card identification expert. Analyze this image of a trading card and return a JSON object with these fields:

{
  "player_name": "Full player/character name (e.g. LeBron James, Charizard)",
  "year": "Card year (e.g. 2023-24 or 2023)",
  "set_name": "Card set/brand (e.g. Panini Prizm, Topps Chrome, Base Set, Scarlet & Violet)",
  "card_number": "Card number if visible (e.g. #220), or null",
  "variant": "Variant/parallel if any (e.g. Silver, Refractor, Base, Holo Rare, Full Art, Alt Art, Reverse Holo), or 'Base'",
  "sport": "NBA, NFL, MLB, or Pokemon",
  "condition_estimate": "Mint, Near Mint, Excellent, Good, or Poor",
  "confidence": "high, medium, or low"
}

Rules:
- Return ONLY valid JSON, no other text
- If you cannot identify a field, use null
- For sport, default to NBA if unclear. Use "Pokemon" for any Pokemon TCG cards.
- For Pokemon cards: player_name = the Pokemon name (e.g. "Charizard"), set_name = the TCG set (e.g. "Base Set", "Scarlet & Violet")
- For condition_estimate, judge centering, corners, edges, surface from the image
- Set confidence to "high" if you can clearly read the card, "medium" if partially visible, "low" if guessing"""


def _parse_scan_result(response_text: str) -> dict:
    """Parse Claude's response into a structured dict."""
    text = response_text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from the response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                result = json.loads(text[start:end])
            except json.JSONDecodeError:
                result = {}
        else:
            result = {}

    defaults = {
        "player_name": None,
        "year": None,
        "set_name": None,
        "card_number": None,
        "variant": "Base",
        "sport": "NBA",
        "condition_estimate": "Unknown",
        "confidence": "low",
    }
    for key, default in defaults.items():
        if key not in result or result[key] is None:
            result[key] = default
    return result


def scan_card_image(image_bytes: bytes, file_name: str = "card.jpg") -> dict:
    """Send image to Claude Vision API and return card identification results.

    Returns dict with player_name, year, set_name, card_number, variant,
    sport, condition_estimate, confidence. Returns error dict on failure.
    """
    if not _anthropic_is_configured():
        return {"error": "Anthropic API key not configured"}

    try:
        import anthropic
    except ImportError:
        return {"error": "anthropic package not installed. Run: pip install anthropic"}

    # Determine media type from file name
    ext = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else "jpg"
    media_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                 "gif": "image/gif", "webp": "image/webp"}
    media_type = media_map.get(ext, "image/jpeg")

    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model=SCANNER_MODEL,
            max_tokens=SCANNER_MAX_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": b64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": _build_scan_prompt(),
                        },
                    ],
                }
            ],
        )
        response_text = message.content[0].text
        return _parse_scan_result(response_text)
    except Exception as e:
        return {"error": str(e)}


def build_collection_entry_from_scan(
    scan_result: dict,
    purchase_price: float,
    purchase_date: str,
) -> dict:
    """Convert scan result into a portfolio-compatible dict with enriched fields."""
    sport = scan_result.get("sport", "NBA")
    # Map set_name to a card_type for portfolio compatibility
    variant = scan_result.get("variant", "Base")
    set_name = scan_result.get("set_name", "")

    if sport == "Pokemon":
        # Pokemon-specific card type mapping
        v_lower = (variant or "").lower()
        if "full art" in v_lower:
            card_type = "Full Art"
        elif "alt art" in v_lower or "alternative" in v_lower:
            card_type = "Alt Art"
        elif "rainbow" in v_lower:
            card_type = "Rainbow Rare"
        elif "holo" in v_lower and "reverse" in v_lower:
            card_type = "Reverse Holo"
        elif "holo" in v_lower:
            card_type = "Holo Rare"
        elif "vmax" in v_lower:
            card_type = "VMAX"
        elif "vstar" in v_lower:
            card_type = "VSTAR"
        elif "1st edition" in v_lower or "first edition" in v_lower:
            card_type = "1st Edition"
        elif "shadowless" in v_lower:
            card_type = "Shadowless"
        elif "ex" in v_lower:
            card_type = "EX"
        elif "gx" in v_lower:
            card_type = "GX"
        else:
            card_type = "Any"
    elif "prizm" in (set_name or "").lower() and "silver" in (variant or "").lower():
        card_type = "Prizm Silver"
    elif "prizm" in (set_name or "").lower():
        card_type = "Prizm"
    elif "refractor" in (variant or "").lower() or "chrome" in (set_name or "").lower():
        card_type = "Refractor"
    elif "auto" in (variant or "").lower():
        card_type = "Auto"
    elif "rookie" in (set_name or "").lower() or "rc" in (set_name or "").lower():
        card_type = "Rookie"
    else:
        card_type = "Any"

    return {
        "player_name": scan_result.get("player_name", "Unknown"),
        "sport": sport,
        "card_type": card_type,
        "purchase_price": purchase_price,
        "purchase_date": purchase_date,
        "quantity": 1,
        # Enriched fields from scanner
        "year": scan_result.get("year"),
        "set_name": scan_result.get("set_name"),
        "card_number": scan_result.get("card_number"),
        "variant": variant,
        "scan_source": "claude_vision",
        "scan_confidence": scan_result.get("confidence", "low"),
    }
