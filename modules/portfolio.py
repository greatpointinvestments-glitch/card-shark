"""Portfolio Tracker — CRUD operations with JSON persistence."""

import json
import os
import tempfile
import uuid
from datetime import datetime

# Default portfolio path (used when no user is logged in)
_DEFAULT_PORTFOLIO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "portfolio.json")


def _get_portfolio_path() -> str:
    """Get the portfolio path for the current user, or default."""
    try:
        import streamlit as st
        username = st.session_state.get("username")
        if username:
            from auth import get_user_portfolio_path
            return get_user_portfolio_path(username)
    except Exception:
        pass
    return _DEFAULT_PORTFOLIO_PATH


def _load_portfolio() -> list[dict]:
    """Read the portfolio from disk. Returns empty list if file doesn't exist."""
    path = _get_portfolio_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        backup = path + ".corrupt"
        try:
            os.replace(path, backup)
        except OSError:
            pass
        return []
    except IOError:
        return []


def _save_portfolio(cards: list[dict]) -> None:
    """Write the portfolio to disk atomically."""
    path = _get_portfolio_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(cards, f, indent=2)
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def add_card(
    player_name: str,
    sport: str,
    card_type: str,
    purchase_price: float,
    purchase_date: str,
    quantity: int = 1,
    year: str | None = None,
    set_name: str | None = None,
    card_number: str | None = None,
    variant: str | None = None,
    scan_source: str | None = None,
    scan_confidence: str | None = None,
    grade_company: str | None = None,
    grade_value: str | None = None,
    image_url: str | None = None,
) -> dict:
    """Add a card to the portfolio. Returns the new card dict.

    Optional enriched fields (year, set_name, card_number, variant) are
    populated by the card scanner but can also be set manually.
    """
    cards = _load_portfolio()
    new_card = {
        "id": str(uuid.uuid4()),
        "player_name": player_name,
        "sport": sport,
        "card_type": card_type,
        "purchase_price": purchase_price,
        "purchase_date": purchase_date,
        "quantity": quantity,
        "added_at": datetime.now().isoformat(),
    }
    # Enriched fields from scanner (backward-compatible optional)
    if year is not None:
        new_card["year"] = year
    if set_name is not None:
        new_card["set_name"] = set_name
    if card_number is not None:
        new_card["card_number"] = card_number
    if variant is not None:
        new_card["variant"] = variant
    if scan_source is not None:
        new_card["scan_source"] = scan_source
    if scan_confidence is not None:
        new_card["scan_confidence"] = scan_confidence
    if grade_company is not None:
        new_card["grade_company"] = grade_company
    if grade_value is not None:
        new_card["grade_value"] = grade_value
    if image_url is not None:
        new_card["image_url"] = image_url

    cards.append(new_card)
    _save_portfolio(cards)
    return new_card


def remove_card(card_id: str) -> bool:
    """Remove a card by UUID. Returns True if found and removed."""
    cards = _load_portfolio()
    original_len = len(cards)
    cards = [c for c in cards if c["id"] != card_id]
    if len(cards) < original_len:
        _save_portfolio(cards)
        return True
    return False


def bulk_import_cards(card_dicts: list[dict], max_allowed: int | None = None) -> dict:
    """Bulk import cards from a list of dicts.

    Each dict should have keys matching add_card() params:
        player_name, sport, card_type, purchase_price, purchase_date,
        quantity, year, set_name, card_number, variant

    Args:
        card_dicts: List of card data dicts to import.
        max_allowed: If set, cap total portfolio size at this number.

    Returns:
        {"imported": int, "skipped": int, "limit_hit": bool}
    """
    current = _load_portfolio()
    current_count = len(current)
    imported = 0
    skipped = 0
    limit_hit = False

    for card in card_dicts:
        if max_allowed is not None and current_count + imported >= max_allowed:
            skipped += len(card_dicts) - imported - skipped
            limit_hit = True
            break

        player = card.get("player_name", "").strip()
        if not player:
            skipped += 1
            continue

        try:
            add_card(
                player_name=player,
                sport=card.get("sport", "NBA"),
                card_type=card.get("card_type", "Base"),
                purchase_price=float(card.get("purchase_price", 0)),
                purchase_date=card.get("purchase_date", ""),
                quantity=int(card.get("quantity", 1)),
                year=card.get("year"),
                set_name=card.get("set_name"),
                card_number=card.get("card_number"),
                variant=card.get("variant"),
            )
            imported += 1
        except Exception:
            skipped += 1

    return {"imported": imported, "skipped": skipped, "limit_hit": limit_hit}


def get_portfolio() -> list[dict]:
    """Return all cards in the portfolio."""
    return _load_portfolio()
