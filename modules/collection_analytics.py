"""Collection Analytics — portfolio summary, top gainer/dip, sport breakdown, CSV export."""

import csv
import io
from datetime import datetime, timedelta


def compute_collection_analytics(portfolio: list[dict], market_values: dict) -> dict:
    """Compute analytics across the entire collection.

    Parameters
    ----------
    portfolio : list of card dicts from get_portfolio()
    market_values : dict mapping card_id -> current market value (per unit)

    Returns
    -------
    dict with total_cards, total_invested, total_current, total_pl, pl_pct,
         avg_card_value, top_gainer, biggest_dip, sport_breakdown, summary_statement
    """
    if not portfolio:
        return {
            "total_cards": 0,
            "total_invested": 0,
            "total_current": 0,
            "total_pl": 0,
            "pl_pct": 0,
            "avg_card_value": 0,
            "top_gainer": None,
            "biggest_dip": None,
            "sport_breakdown": {},
            "summary_statement": "Your collection is empty. Add your first card to start tracking!",
        }

    total_cards = sum(c.get("quantity", 1) for c in portfolio)
    total_invested = sum(c["purchase_price"] * c.get("quantity", 1) for c in portfolio)
    total_current = sum(
        market_values.get(c["id"], 0) * c.get("quantity", 1) for c in portfolio
    )
    total_pl = total_current - total_invested
    pl_pct = round((total_pl / total_invested * 100), 1) if total_invested > 0 else 0
    avg_card_value = round(total_current / total_cards, 2) if total_cards > 0 else 0

    # Find top gainer and biggest dip (by P&L %)
    card_perfs = []
    for c in portfolio:
        qty = c.get("quantity", 1)
        cost = c["purchase_price"] * qty
        current = market_values.get(c["id"], 0) * qty
        pl = current - cost
        card_pl_pct = round((pl / cost * 100), 1) if cost > 0 else 0
        card_perfs.append({
            "player_name": c["player_name"],
            "sport": c["sport"],
            "card_type": c["card_type"],
            "pl": round(pl, 2),
            "pl_pct": card_pl_pct,
        })

    top_gainer = max(card_perfs, key=lambda x: x["pl_pct"]) if card_perfs else None
    biggest_dip = min(card_perfs, key=lambda x: x["pl_pct"]) if card_perfs else None

    # Sport breakdown: sport -> total current value
    sport_breakdown = {}
    for c in portfolio:
        sport = c.get("sport", "Other")
        val = market_values.get(c["id"], 0) * c.get("quantity", 1)
        sport_breakdown[sport] = round(sport_breakdown.get(sport, 0) + val, 2)

    # Summary statement
    direction = "up" if total_pl >= 0 else "down"
    summary_statement = (
        f"Your {total_cards}-card collection is {direction} "
        f"${abs(total_pl):,.2f} ({abs(pl_pct):.1f}%) since you started tracking."
    )

    return {
        "total_cards": total_cards,
        "total_invested": round(total_invested, 2),
        "total_current": round(total_current, 2),
        "total_pl": round(total_pl, 2),
        "pl_pct": pl_pct,
        "avg_card_value": avg_card_value,
        "top_gainer": top_gainer,
        "biggest_dip": biggest_dip,
        "sport_breakdown": sport_breakdown,
        "summary_statement": summary_statement,
    }


def compute_portfolio_timeline(portfolio: list[dict], market_values: dict) -> list[dict]:
    """Compute daily portfolio value over the last 90 days.

    Uses purchase dates and market values to simulate portfolio value history.
    Returns list of dicts with date, value.
    """
    if not portfolio:
        return []

    today = datetime.now().date()
    start = today - timedelta(days=90)

    # Sort cards by purchase date
    cards_by_date = []
    for c in portfolio:
        pd_str = c.get("purchase_date", "")
        try:
            pd = datetime.strptime(pd_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            pd = start
        cards_by_date.append((pd, c))

    timeline = []
    for day_offset in range(91):
        current_date = start + timedelta(days=day_offset)
        # Cards owned as of this date
        owned = [c for pd, c in cards_by_date if pd <= current_date]
        # Value = sum of market values for owned cards
        day_value = sum(
            market_values.get(c["id"], c["purchase_price"]) * c.get("quantity", 1)
            for c in owned
        )

        timeline.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "value": round(day_value, 2),
        })

    return timeline


def export_portfolio_csv(portfolio: list[dict], market_values: dict) -> str:
    """Export portfolio as CSV string for download.

    Columns: Player, Sport, Card Type, Qty, Purchase Price, Purchase Date,
             Current Value, P&L, P&L %
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Player", "Sport", "Card Type", "Year", "Set", "Card Number",
        "Variant", "Qty", "Purchase Price",
        "Purchase Date", "Current Value", "P&L ($)", "P&L (%)",
    ])

    for c in portfolio:
        qty = c.get("quantity", 1)
        cost = c["purchase_price"] * qty
        current = market_values.get(c["id"], 0) * qty
        pl = current - cost
        pl_pct = round((pl / cost * 100), 1) if cost > 0 else 0

        writer.writerow([
            c["player_name"],
            c["sport"],
            c["card_type"],
            c.get("year", ""),
            c.get("set_name", ""),
            c.get("card_number", ""),
            c.get("variant", ""),
            qty,
            f"{c['purchase_price']:.2f}",
            c.get("purchase_date", ""),
            f"{current:.2f}",
            f"{pl:.2f}",
            f"{pl_pct:.1f}%",
        ])

    return output.getvalue()
