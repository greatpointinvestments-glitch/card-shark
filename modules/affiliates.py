"""Unified affiliate link handling across card marketplaces.

Supports: eBay (EPN), PWCC, COMC, Fanatics Collect, Alt, Goldin.

Usage:
    from modules.affiliates import affiliate_url, detect_marketplace
    url = affiliate_url("https://www.ebay.com/itm/12345")
"""

from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

from config.settings import (
    EPN_CAMPAIGN_ID, EPN_TRACKING_ID,
    PWCC_AFFILIATE_ID, COMC_AFFILIATE_ID,
    FANATICS_COLLECT_AFFILIATE_ID, ALT_AFFILIATE_ID, GOLDIN_AFFILIATE_ID,
    TCGPLAYER_AFFILIATE_ID,
)


# Marketplace identifier → display name (for UI badges/attribution)
MARKETPLACE_NAMES = {
    "ebay": "eBay",
    "pwcc": "PWCC",
    "comc": "COMC",
    "fanatics_collect": "Fanatics Collect",
    "alt": "Alt",
    "goldin": "Goldin",
    "tcgplayer": "TCGPlayer",
    "unknown": "Marketplace",
}


def detect_marketplace(url: str) -> str:
    """Return a marketplace key for the given URL."""
    if not url:
        return "unknown"
    host = urlparse(url).netloc.lower()
    if "ebay." in host:
        return "ebay"
    if "pwccmarketplace" in host or "pwcc.com" in host:
        return "pwcc"
    if "comc.com" in host:
        return "comc"
    if "fanaticscollect.com" in host:
        return "fanatics_collect"
    if "onlyalt.com" in host or "alt.xyz" in host:
        return "alt"
    if "goldin.co" in host or "goldinauctions.com" in host:
        return "goldin"
    if "tcgplayer.com" in host:
        return "tcgplayer"
    return "unknown"


def _append_params(url: str, params: dict) -> str:
    """Append query params to a URL without duplicating existing keys."""
    parts = urlparse(url)
    current = parse_qs(parts.query)
    for k, v in params.items():
        current[k] = [str(v)]
    flat = {k: vs[0] for k, vs in current.items()}
    return urlunparse(parts._replace(query=urlencode(flat)))


def _ebay_url(url: str) -> str:
    if not EPN_CAMPAIGN_ID:
        return url
    return _append_params(url, {
        "mkcid": 1,
        "mkrid": "711-53200-19255-0",
        "campid": EPN_CAMPAIGN_ID,
        "toolid": 10001,
        "customid": EPN_TRACKING_ID or "card-shark",
    })


def _pwcc_url(url: str) -> str:
    if not PWCC_AFFILIATE_ID:
        return url
    return _append_params(url, {"ref": PWCC_AFFILIATE_ID, "utm_source": "cardshark"})


def _comc_url(url: str) -> str:
    if not COMC_AFFILIATE_ID:
        return url
    return _append_params(url, {"aid": COMC_AFFILIATE_ID, "utm_source": "cardshark"})


def _fanatics_url(url: str) -> str:
    if not FANATICS_COLLECT_AFFILIATE_ID:
        return url
    return _append_params(url, {"aff": FANATICS_COLLECT_AFFILIATE_ID, "utm_source": "cardshark"})


def _alt_url(url: str) -> str:
    if not ALT_AFFILIATE_ID:
        return url
    return _append_params(url, {"ref": ALT_AFFILIATE_ID, "utm_source": "cardshark"})


def _goldin_url(url: str) -> str:
    if not GOLDIN_AFFILIATE_ID:
        return url
    return _append_params(url, {"ref": GOLDIN_AFFILIATE_ID, "utm_source": "cardshark"})


def _tcgplayer_url(url: str) -> str:
    if not TCGPLAYER_AFFILIATE_ID:
        return url
    return _append_params(url, {"partner": TCGPLAYER_AFFILIATE_ID, "utm_source": "cardshark", "utm_medium": "affiliate"})


_ROUTER = {
    "ebay": _ebay_url,
    "pwcc": _pwcc_url,
    "comc": _comc_url,
    "fanatics_collect": _fanatics_url,
    "alt": _alt_url,
    "goldin": _goldin_url,
    "tcgplayer": _tcgplayer_url,
}


def affiliate_url(url: str) -> str:
    """Return the URL with the correct affiliate parameters for its marketplace.

    Pass-through for unknown marketplaces or when the affiliate ID is not set.
    """
    if not url:
        return url
    marketplace = detect_marketplace(url)
    handler = _ROUTER.get(marketplace)
    if not handler:
        return url
    try:
        return handler(url)
    except Exception:
        return url


def marketplace_name(url: str) -> str:
    """Pretty marketplace label for a URL ('eBay', 'PWCC', etc.)."""
    return MARKETPLACE_NAMES.get(detect_marketplace(url), "Marketplace")


def ebay_search_affiliate_url(player_name: str, sport: str = "", card_type: str = "") -> str:
    """Generate an eBay search URL for a player's cards, wrapped with affiliate params.
    Use this on pages that show player data but don't have specific listing URLs."""
    from urllib.parse import quote_plus
    query_parts = [player_name]
    if sport:
        query_parts.append(sport)
    if card_type and card_type != "Any":
        query_parts.append(card_type)
    query_parts.append("card")
    query = quote_plus(" ".join(query_parts))
    base = f"https://www.ebay.com/sch/i.html?_nkw={query}&_sacat=212&LH_BIN=1"
    return affiliate_url(base)


def tcgplayer_search_affiliate_url(card_name: str, set_name: str = "") -> str:
    """Generate a TCGPlayer search URL for a Pokemon card, wrapped with affiliate params."""
    from urllib.parse import quote_plus
    query_parts = [card_name]
    if set_name:
        query_parts.append(set_name)
    query = quote_plus(" ".join(query_parts))
    base = f"https://www.tcgplayer.com/search/pokemon/product?q={query}&view=grid"
    return affiliate_url(base)
