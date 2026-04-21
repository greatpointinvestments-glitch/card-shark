"""API URLs, sport configs, and constants."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Explicit path so load_dotenv works regardless of CWD
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)


def _get_secret(key: str, default: str = "") -> str:
    """Try st.secrets first (Streamlit Cloud), fall back to env vars."""
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val:  # only use st.secrets if non-empty
            return val
    except Exception:
        pass
    return os.getenv(key, default)


# --- API Keys ---
BALLDONTLIE_API_KEY = _get_secret("BALLDONTLIE_API_KEY")
EBAY_CLIENT_ID = _get_secret("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = _get_secret("EBAY_CLIENT_SECRET")
ANTHROPIC_API_KEY = _get_secret("ANTHROPIC_API_KEY")

# --- BALLDONTLIE API ---
BALLDONTLIE_BASE_URL = "https://api.balldontlie.io/v1"

# --- eBay API ---
EBAY_AUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_BROWSE_URL = "https://api.ebay.com/buy/browse/v1"
EBAY_FINDING_URL = "https://svcs.ebay.com/services/search/FindingService/v1"

# --- Sport Configurations ---
SPORTS = {
    "NBA": {
        "key_stats": ["pts", "reb", "ast", "stl", "blk", "fg_pct"],
        "stat_labels": {
            "pts": "PPG", "reb": "RPG", "ast": "APG",
            "stl": "SPG", "blk": "BPG", "fg_pct": "FG%",
        },
        "trajectory_stats": ["pts", "reb", "ast"],
    },
    "NFL": {
        "key_stats": ["pass_yds", "pass_td", "rush_yds", "rush_td", "rec_yds", "rec_td"],
        "stat_labels": {
            "pass_yds": "Pass YDS", "pass_td": "Pass TD",
            "rush_yds": "Rush YDS", "rush_td": "Rush TD",
            "rec_yds": "Rec YDS", "rec_td": "Rec TD",
        },
        "trajectory_stats": ["pass_yds", "rush_yds", "rec_yds"],
    },
    "MLB": {
        "key_stats": ["avg", "hr", "rbi", "ops", "sb"],
        "stat_labels": {
            "avg": "AVG", "hr": "HR", "rbi": "RBI",
            "ops": "OPS", "sb": "SB",
        },
        "trajectory_stats": ["hr", "rbi", "ops"],
    },
    "Pokemon": {
        "key_stats": [],
        "stat_labels": {},
        "trajectory_stats": [],
        "pricing_source": "pokemon_tcg",
    },
}

# Breakout scoring weights
BREAKOUT_WEIGHTS = {
    "trajectory": 0.30,
    "usage": 0.20,
    "age": 0.15,
    "draft": 0.15,
    "market": 0.20,
}

# Legend scoring weights
LEGEND_WEIGHTS = {
    "hof_legacy": 0.30,
    "iconic_card": 0.25,
    "market_value": 0.25,
    "cultural": 0.20,
}

# Breakout signal thresholds
SIGNAL_BUY = 75
SIGNAL_WATCH = 50

# Cache TTL in seconds (5 minutes for API responses)
CACHE_TTL = 300

# --- Live Game Tracker ---
ESPN_NBA_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
ESPN_NFL_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
GAME_TRACKER_TTL = 120  # 2-minute refresh for live scores

# Team name aliases for matching (watchlist name -> API name)
TEAM_NAME_ALIASES = {
    "LA Lakers": "Los Angeles Lakers",
    "LA Clippers": "Los Angeles Clippers",
}

# --- PSA Population API ---
PSA_API_BASE_URL = "https://api.psacard.com/publicapi"
PSA_CACHE_TTL = 3600  # 1-hour cache for PSA population data

# --- Card Scanner ---
SCANNER_MODEL = "claude-haiku-4-5-20251001"
SCANNER_MAX_TOKENS = 1024

# --- OCR Scanner (free tier) ---
OCR_CONFIDENCE_THRESHOLD = 2   # min fields extracted for "medium" confidence
OCR_MIN_TEXT_LENGTH = 10       # min chars from Tesseract to attempt parsing

# --- Subscription Tiers ---
FREE_TIER_LIMITS = {
    "searches_per_day": 10,
    "trades_per_day": 3,
    "portfolio_max_cards": 25,
    "scans_per_day": 3,       # kept low — Anthropic vision calls are the #1 cost driver
}

PRO_FEATURES = [
    "flip_finder",
    "market_movers",
    "grading_calculator",
    "player_comparison",
    "price_alerts",
    "price_history_live",
    "psa_population",
    "csv_export",
    "unlimited_search",
    "unlimited_portfolio",
    "unlimited_trades",
]

PRO_PRICE_MONTHLY = 7.99
PRO_PRICE_YEARLY = 59.99
PRO_PRICE_LIFETIME = 149.00

# --- Promo / Abandoned-Checkout ---
ABANDON_COUPON_CODE = "WELCOME20"
ABANDON_COUPON_DISCOUNT_PCT = 20
ABANDON_TRIGGER_VISITS = 4  # show coupon after this many upgrade-page visits without buying

# --- Anonymous Try-It ---
ANON_SEARCH_LIMIT = 1  # free searches before signup gate

# --- Social Proof (placeholder until analytics wired) ---
SOCIAL_PROOF_STATS = {
    "cards_scanned": "50K+",
    "active_users": "2,400+",
    "deals_found": "12K+",
}

# --- Lifetime Deal ---
LIFETIME_DEAL_CAP = 100  # total spots available for the launch LTD

# --- Stripe ---
STRIPE_SECRET_KEY = _get_secret("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = _get_secret("STRIPE_PUBLISHABLE_KEY")
STRIPE_PRICE_MONTHLY = _get_secret("STRIPE_PRICE_MONTHLY")  # Stripe Price ID for $7.99/mo
STRIPE_PRICE_YEARLY = _get_secret("STRIPE_PRICE_YEARLY")    # Stripe Price ID for $59.99/yr
STRIPE_PRICE_LIFETIME = _get_secret("STRIPE_PRICE_LIFETIME")  # Stripe Price ID for $149 one-time
STRIPE_PRICE_MONTHLY_DISCOUNT = _get_secret("STRIPE_PRICE_MONTHLY_DISCOUNT")  # 20% off monthly Price ID
STRIPE_PRICE_YEARLY_DISCOUNT = _get_secret("STRIPE_PRICE_YEARLY_DISCOUNT")    # 20% off yearly Price ID
STRIPE_WEBHOOK_SECRET = _get_secret("STRIPE_WEBHOOK_SECRET")

# --- eBay Partner Network (Affiliate) ---
EPN_CAMPAIGN_ID = _get_secret("EPN_CAMPAIGN_ID")  # e.g. "5338123456"
EPN_TRACKING_ID = _get_secret("EPN_TRACKING_ID", "card-shark")  # custom tracking alias

# --- Other Affiliate Networks (Impact, ShareASale, direct partners) ---
PWCC_AFFILIATE_ID = _get_secret("PWCC_AFFILIATE_ID")
COMC_AFFILIATE_ID = _get_secret("COMC_AFFILIATE_ID")
FANATICS_COLLECT_AFFILIATE_ID = _get_secret("FANATICS_COLLECT_AFFILIATE_ID")
ALT_AFFILIATE_ID = _get_secret("ALT_AFFILIATE_ID")
GOLDIN_AFFILIATE_ID = _get_secret("GOLDIN_AFFILIATE_ID")

# --- Pokemon TCG API (free, no key required) ---
POKEMON_TCG_BASE_URL = "https://api.pokemontcg.io/v2"

# --- TCGPlayer Affiliate ---
TCGPLAYER_AFFILIATE_ID = _get_secret("TCGPLAYER_AFFILIATE_ID")

# --- New Affiliate Partners ---
WHATNOT_AFFILIATE_ID = _get_secret("WHATNOT_AFFILIATE_ID")
TOPPS_AFFILIATE_ID = _get_secret("TOPPS_AFFILIATE_ID")
BECKETT_AFFILIATE_ID = _get_secret("BECKETT_AFFILIATE_ID")
BCW_AFFILIATE_ID = _get_secret("BCW_AFFILIATE_ID")
ZION_AFFILIATE_ID = _get_secret("ZION_AFFILIATE_ID")
CARDSHELLZ_AFFILIATE_ID = _get_secret("CARDSHELLZ_AFFILIATE_ID")
DRIP_SHOP_AFFILIATE_ID = _get_secret("DRIP_SHOP_AFFILIATE_ID")

# --- Price Alerts ---
ALERTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "alerts.json")
