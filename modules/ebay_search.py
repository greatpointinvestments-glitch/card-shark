"""eBay Browse API + Finding API wrapper with OAuth authentication."""

import base64
from datetime import datetime, timedelta
import requests
import streamlit as st
from config.settings import (
    EBAY_CLIENT_ID, EBAY_CLIENT_SECRET, EBAY_AUTH_URL,
    EBAY_BROWSE_URL, EBAY_FINDING_URL,
)
from config.card_keywords import build_search_query

import re

# Patterns that indicate bulk/pick-your-card listings (not single card sales)
_BULK_PATTERNS = re.compile(
    # Pick-your-card language
    r"pick your|choose your|you choose|you pick|u pick|u choose|"
    r"pick a card|select your|pick \d+|choose \d+|"
    r"\bpyc\b|\bcyc\b|- choose|- pick|your choice|buyers choice|buyer's choice|"
    # Set building / completion
    r"complete your set|build your set|finish your set|master set|"
    # Lots, bulks, mystery, order minimums
    r"lot of \d+|card lot|bulk lot|base lot|mystery pack|mystery box|"
    r"grab bag|repack|you get all|set break|break lot|"
    r"\d+ card minimum|order minimum|card order minimum|multi-?buy|"
    # Listing a range of card numbers (e.g., "#151-300") signals a set listing
    r"#\s*\d+\s*-\s*\d+",
    re.IGNORECASE,
)


def _is_bulk_listing(title: str) -> bool:
    """Return True if the listing title looks like a bulk/pick-your-card listing."""
    return bool(_BULK_PATTERNS.search(title or ""))


def _mentions_player(title: str, player_name: str) -> bool:
    """Return True if the title actually mentions the searched player.
    Accepts full name OR last name (case-insensitive, word-boundary matched)."""
    if not title or not player_name:
        return False
    t = title.lower()
    name_lower = player_name.lower().strip()
    if name_lower in t:
        return True
    # Fall back to last-name match
    parts = name_lower.split()
    if len(parts) >= 2:
        last = parts[-1]
        return bool(re.search(r"\b" + re.escape(last) + r"\b", t))
    return False


@st.cache_data(ttl=7200)
def _get_ebay_token() -> str | None:
    """Get an eBay OAuth application token (client credentials grant)."""
    if not EBAY_CLIENT_ID or not EBAY_CLIENT_SECRET:
        return None
    if EBAY_CLIENT_ID == "your_client_id_here":
        return None

    credentials = base64.b64encode(
        f"{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}".encode()
    ).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {credentials}",
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope",
    }

    try:
        resp = requests.post(EBAY_AUTH_URL, headers=headers, data=data, timeout=10)
        resp.raise_for_status()
        return resp.json().get("access_token")
    except requests.RequestException:
        return None


def _ebay_is_configured() -> bool:
    """Check if eBay API keys are set."""
    return (
        EBAY_CLIENT_ID
        and EBAY_CLIENT_SECRET
        and EBAY_CLIENT_ID != "your_client_id_here"
        and EBAY_CLIENT_SECRET != "your_client_secret_here"
    )


@st.cache_data(ttl=300)
def search_ebay_cards(
    player_name: str,
    sport: str = "NBA",
    card_type: str = "Any",
    sort: str = "bestMatch",
    limit: int = 50,
    year: str | None = None,
    set_name: str | None = None,
) -> list[dict]:
    """Search eBay for sports card listings. Falls back to demo data if API keys not set."""
    if not player_name or not player_name.strip():
        return []
    if not _ebay_is_configured():
        from data.demo_listings import generate_demo_listings
        return generate_demo_listings(player_name, sport, card_type, limit)

    token = _get_ebay_token()
    if not token:
        from data.demo_listings import generate_demo_listings
        return generate_demo_listings(player_name, sport, card_type, limit)

    query = build_search_query(player_name, sport, card_type, year=year, set_name=set_name)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
    }
    # CCG category (183454) for Pokemon, Sports Trading Cards (212) for everything else
    category_id = "183454" if sport == "Pokemon" else "212"
    params = {
        "q": query,
        "category_ids": category_id,
        "limit": min(limit, 200),
    }
    # eBay Browse API: omit sort for default "best match" relevance ranking
    if sort and sort != "bestMatch":
        params["sort"] = sort
    # When sorting by ending soonest, filter to auction listings only
    if sort == "endingSoonest":
        params["filter"] = "buyingOptions:{AUCTION}"

    try:
        resp = requests.get(
            f"{EBAY_BROWSE_URL}/item_summary/search",
            headers=headers,
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        items = resp.json().get("itemSummaries", [])
        parsed = [_parse_listing(item) for item in items]
        # Drop bulk/PYC + drop listings that don't mention the searched player
        return [
            l for l in parsed
            if not _is_bulk_listing(l["title"])
            and _mentions_player(l["title"], player_name)
        ]
    except requests.RequestException:
        return []


def _parse_listing(item: dict) -> dict:
    """Parse a raw eBay item summary into a clean dict."""
    price_info = item.get("price", {})
    price = float(price_info.get("value", 0))

    # For auctions, use currentBidPrice if available (price may be 0 or the start price)
    bid_info = item.get("currentBidPrice", {})
    if bid_info:
        bid_price = float(bid_info.get("value", 0))
        if bid_price > 0:
            price = bid_price

    shipping = item.get("shippingOptions", [{}])
    ship_cost = 0.0
    if shipping:
        ship_price = shipping[0].get("shippingCost", {})
        ship_cost = float(ship_price.get("value", 0))

    image = item.get("image", {})
    thumbnail = item.get("thumbnailImages", [{}])

    buying_options = item.get("buyingOptions", [])
    if "FIXED_PRICE" in buying_options:
        buying_format = "BIN"
    elif "AUCTION" in buying_options:
        buying_format = "Auction"
    else:
        buying_format = "BIN"

    seller = item.get("seller", {}) or {}
    try:
        feedback_pct = float(seller.get("feedbackPercentage", 0) or 0)
    except (TypeError, ValueError):
        feedback_pct = 0.0
    try:
        feedback_count = int(seller.get("feedbackScore", 0) or 0)
    except (TypeError, ValueError):
        feedback_count = 0

    bid_count = int(item.get("bidCount", 0) or 0)

    return {
        "title": item.get("title", ""),
        "price": price,
        "shipping": ship_cost,
        "total": round(price + ship_cost, 2),
        "condition": item.get("condition", "N/A"),
        "url": item.get("itemWebUrl", ""),
        "image_url": image.get("imageUrl", ""),
        "item_id": item.get("itemId", ""),
        "buying_format": buying_format,
        "bid_count": bid_count,
        "seller_username": seller.get("username", ""),
        "seller_feedback_pct": feedback_pct,
        "seller_feedback_count": feedback_count,
    }


def flag_deals(listings: list[dict]) -> list[dict]:
    """Flag BIN listings priced below the median as DEAL. Auctions are excluded."""
    if not listings:
        return listings

    # Compute median from BIN listings only
    bin_prices = [l["total"] for l in listings
                  if l["total"] > 0 and l.get("buying_format", "BIN") == "BIN"]
    if not bin_prices:
        # Fall back to auction listings that have actual bids (skip no-bid $0 auctions)
        bin_prices = [l["total"] for l in listings
                      if l["total"] > 0 and l.get("bid_count", 0) > 0]
    if not bin_prices:
        return listings

    bin_prices.sort()
    mid = len(bin_prices) // 2
    median = bin_prices[mid] if len(bin_prices) % 2 else (bin_prices[mid - 1] + bin_prices[mid]) / 2

    for listing in listings:
        listing["median"] = round(median, 2)
        if listing.get("buying_format", "BIN") == "BIN":
            listing["is_deal"] = listing["total"] > 0 and listing["total"] < median
            if median > 0:
                listing["vs_median"] = round((listing["total"] - median) / median * 100, 1)
            else:
                listing["vs_median"] = 0.0
        else:
            # Auctions show current bid — don't flag as deals
            listing["is_deal"] = False
            listing["vs_median"] = 0.0

    return listings


# ============================================================
# Finding API — Sold / Completed Listings
# ============================================================

def _iso_date_days_ago(days: int) -> str:
    """Return an ISO 8601 date string for N days ago (used by Finding API filters)."""
    return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _parse_sold_listing(item: dict) -> dict:
    """Parse a Finding API item (everything wrapped in single-element arrays) into a clean dict."""
    def _val(obj, key, default=""):
        v = obj.get(key, [default])
        return v[0] if isinstance(v, list) else v

    selling = _val(item, "sellingStatus", {})
    if isinstance(selling, list):
        selling = selling[0] if selling else {}
    price_info = _val(selling, "currentPrice", {})
    if isinstance(price_info, list):
        price_info = price_info[0] if price_info else {}

    sold_price = float(price_info.get("__value__", 0) if isinstance(price_info, dict) else 0)

    shipping_info = _val(item, "shippingInfo", {})
    if isinstance(shipping_info, list):
        shipping_info = shipping_info[0] if shipping_info else {}
    ship_cost_info = _val(shipping_info, "shippingServiceCost", {})
    if isinstance(ship_cost_info, list):
        ship_cost_info = ship_cost_info[0] if ship_cost_info else {}
    ship_cost = float(ship_cost_info.get("__value__", 0) if isinstance(ship_cost_info, dict) else 0)

    condition_info = _val(item, "condition", {})
    if isinstance(condition_info, list):
        condition_info = condition_info[0] if condition_info else {}
    condition = _val(condition_info, "conditionDisplayName", "N/A")

    listing_info = _val(item, "listingInfo", {})
    if isinstance(listing_info, list):
        listing_info = listing_info[0] if listing_info else {}
    listing_type = _val(listing_info, "listingType", "Unknown")
    end_time = _val(listing_info, "endTime", "")

    # Parse end date
    sold_date = ""
    if end_time:
        try:
            sold_date = end_time[:10]
        except (IndexError, TypeError):
            sold_date = ""

    return {
        "title": _val(item, "title"),
        "sold_price": sold_price,
        "shipping": ship_cost,
        "total": round(sold_price + ship_cost, 2),
        "condition": condition,
        "sold_date": sold_date,
        "listing_type": listing_type,
        "url": _val(item, "viewItemURL"),
        "item_id": _val(item, "itemId"),
    }


@st.cache_data(ttl=300)
def search_ebay_sold(
    player_name: str,
    sport: str = "NBA",
    card_type: str = "Any",
    limit: int = 50,
    year: str | None = None,
    set_name: str | None = None,
) -> list[dict]:
    """Search eBay Finding API for sold/completed sports card listings (90-day lookback).
    Falls back to demo data if API keys are not set."""
    if not player_name or not player_name.strip():
        return []
    if not _ebay_is_configured():
        from data.demo_listings import generate_demo_sold_listings
        return generate_demo_sold_listings(player_name, sport, card_type, limit)

    query = build_search_query(player_name, sport, card_type, year=year, set_name=set_name)

    params = {
        "OPERATION-NAME": "findCompletedItems",
        "SERVICE-VERSION": "1.13.0",
        "SECURITY-APPNAME": EBAY_CLIENT_ID,
        "RESPONSE-DATA-FORMAT": "JSON",
        "REST-PAYLOAD": "true",
        "keywords": query,
        "categoryId": "183454" if sport == "Pokemon" else "212",
        "paginationInput.entriesPerPage": str(min(limit, 100)),
        "sortOrder": "EndTimeSoonest",
        # Filters
        "itemFilter(0).name": "SoldItemsOnly",
        "itemFilter(0).value": "true",
        "itemFilter(1).name": "EndTimeFrom",
        "itemFilter(1).value": _iso_date_days_ago(90),
    }

    try:
        resp = requests.get(EBAY_FINDING_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        result = data.get("findCompletedItemsResponse", [{}])
        if isinstance(result, list):
            result = result[0] if result else {}

        search_result = result.get("searchResult", [{}])
        if isinstance(search_result, list):
            search_result = search_result[0] if search_result else {}

        items = search_result.get("item", [])
        parsed = [_parse_sold_listing(item) for item in items]
        return [
            l for l in parsed
            if not _is_bulk_listing(l["title"])
            and _mentions_player(l["title"], player_name)
        ]
    except requests.RequestException:
        from data.demo_listings import generate_demo_sold_listings
        return generate_demo_sold_listings(player_name, sport, card_type, limit)


def get_market_summary(
    active_listings: list[dict],
    sold_listings: list[dict],
) -> dict:
    """Combine active + sold data into market analytics.

    Returns dict with: avg_sold, sold_volume, avg_active, price_trend,
    trend_delta, market_signal, active_vs_sold_pct.
    """
    # Exclude no-bid auctions (total still 0 even after currentBidPrice check)
    # from active pricing — they'd drag the average down to meaningless levels
    active_prices = [
        l["total"] for l in active_listings
        if l.get("total", 0) > 0
        and not (l.get("buying_format") == "Auction" and l.get("bid_count", 0) == 0)
    ]
    sold_prices = [l["total"] for l in sold_listings if l.get("total", 0) > 0]

    avg_active = round(sum(active_prices) / len(active_prices), 2) if active_prices else 0
    avg_sold = round(sum(sold_prices) / len(sold_prices), 2) if sold_prices else 0
    sold_volume = len(sold_prices)

    # Price trend: compare recent half vs older half of sold listings (by date)
    # Finding API sorts EndTimeSoonest (oldest first), so second half = recent
    trend = "Stable"
    trend_delta = 0.0
    if len(sold_prices) >= 6:
        mid = len(sold_prices) // 2
        older_avg = sum(sold_prices[:mid]) / mid
        recent_avg = sum(sold_prices[mid:]) / (len(sold_prices) - mid)
        if older_avg > 0:
            trend_delta = round((recent_avg - older_avg) / older_avg * 100, 1)
            if trend_delta > 5:
                trend = "Rising"
            elif trend_delta < -5:
                trend = "Falling"

    # Market signal based on active vs sold spread
    # Needs BOTH sides of data — don't flash BUY WINDOW on an empty active pool
    signal = "N/A"
    if avg_sold > 0 and avg_active > 0:
        spread_pct = (avg_active - avg_sold) / avg_sold * 100
        if spread_pct > 15:
            signal = "OVERPRICED"
        elif spread_pct < -10:
            signal = "BUY WINDOW"
        else:
            signal = "FAIR VALUE"

    active_vs_sold_pct = 0.0
    if avg_sold > 0 and avg_active > 0:
        active_vs_sold_pct = round((avg_active - avg_sold) / avg_sold * 100, 1)

    return {
        "avg_sold": avg_sold,
        "sold_volume": sold_volume,
        "avg_active": avg_active,
        "price_trend": trend,
        "trend_delta": trend_delta,
        "market_signal": signal,
        "active_vs_sold_pct": active_vs_sold_pct,
    }


def test_ebay_connection() -> dict:
    """Verify both Browse + Finding APIs respond. Returns status dict."""
    result = {"browse": False, "finding": False, "configured": _ebay_is_configured()}

    if not result["configured"]:
        return result

    # Test Browse API (needs OAuth token)
    token = _get_ebay_token()
    if token:
        try:
            resp = requests.get(
                f"{EBAY_BROWSE_URL}/item_summary/search",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
                },
                params={"q": "sports card", "limit": "1"},
                timeout=10,
            )
            result["browse"] = resp.status_code == 200
        except requests.RequestException:
            pass

    # Test Finding API (uses App ID directly)
    try:
        resp = requests.get(
            EBAY_FINDING_URL,
            params={
                "OPERATION-NAME": "findCompletedItems",
                "SERVICE-VERSION": "1.13.0",
                "SECURITY-APPNAME": EBAY_CLIENT_ID,
                "RESPONSE-DATA-FORMAT": "JSON",
                "keywords": "sports card",
                "paginationInput.entriesPerPage": "1",
                "itemFilter(0).name": "SoldItemsOnly",
                "itemFilter(0).value": "true",
            },
            timeout=10,
        )
        result["finding"] = resp.status_code == 200
    except requests.RequestException:
        pass

    return result
