"""Card Shark — Sports Card Investment Analyzer.

Thin router: CSS + sidebar nav + page dispatch. All page logic lives in pages/*.py.
"""

import streamlit as st

from modules.ebay_search import test_ebay_connection, _ebay_is_configured
from config.settings import EBAY_CLIENT_ID
from auth import render_auth_ui
from tiers import is_pro

# Page modules
from views import (
    home, card_scanner, live_games, player_search, price_history,
    breakout_leaderboard, legend_cards, trade_checker, flip_finder_page,
    player_comparison, market_movers, price_alerts_page, my_collection,
    grading_calculator, budget_finder,
)


# --- Page Config ---
st.set_page_config(
    page_title="Card Shark",
    page_icon="🦈",
    layout="wide",
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* Existing signal badges — punchier */
    .deal-tag { color: #fff; background-color: #22c55e; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    .buy-signal { color: #fff; background-color: #22c55e; padding: 2px 10px; border-radius: 4px; font-weight: bold; }
    .watch-signal { color: #000; background-color: #facc15; padding: 2px 10px; border-radius: 4px; font-weight: bold; }
    .hold-signal { color: #fff; background-color: #6b7280; padding: 2px 10px; border-radius: 4px; font-weight: bold; }
    .strong-buy { color: #fff; background-color: #16a34a; padding: 2px 10px; border-radius: 4px; font-weight: bold; }
    .pass-signal { color: #fff; background-color: #dc2626; padding: 2px 10px; border-radius: 4px; font-weight: bold; }
    .market-buy { color: #fff; background-color: #16a34a; padding: 4px 12px; border-radius: 6px; font-weight: bold; font-size: 1.1em; }
    .market-fair { color: #000; background-color: #facc15; padding: 4px 12px; border-radius: 6px; font-weight: bold; font-size: 1.1em; }
    .market-over { color: #fff; background-color: #dc2626; padding: 4px 12px; border-radius: 6px; font-weight: bold; font-size: 1.1em; }

    /* New — vibe overhaul */
    .steal-alert {
        color: #fff; background: linear-gradient(135deg, #22c55e, #10b981);
        padding: 2px 10px; border-radius: 4px; font-weight: 900;
        font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.5px;
        animation: pulse-green 2s infinite;
    }
    .fire-deal {
        color: #fff; background: linear-gradient(135deg, #ff4b1f, #ff9068);
        padding: 2px 10px; border-radius: 4px; font-weight: 900;
        font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.5px;
        animation: pulse-fire 2s infinite;
    }
    @keyframes pulse-fire {
        0%, 100% { box-shadow: 0 0 4px rgba(255,75,31,0.4); }
        50% { box-shadow: 0 0 12px rgba(255,75,31,0.8); }
    }
    @keyframes pulse-green {
        0%, 100% { box-shadow: 0 0 4px rgba(34,197,94,0.4); }
        50% { box-shadow: 0 0 12px rgba(34,197,94,0.8); }
    }
    .ebay-btn {
        display: inline-block; padding: 4px 14px; border-radius: 6px;
        background: linear-gradient(135deg, #3b82f6, #2563eb); color: #fff;
        font-weight: bold; font-size: 0.85em; text-decoration: none;
        transition: transform 0.15s, box-shadow 0.15s;
    }
    .ebay-btn:hover { transform: scale(1.05); box-shadow: 0 2px 8px rgba(59,130,246,0.5); color: #fff; }
    .tcgplayer-btn {
        display: inline-block; padding: 4px 14px; border-radius: 6px;
        background: linear-gradient(135deg, #ed64a6, #d53f8c); color: #fff;
        font-weight: bold; font-size: 0.85em; text-decoration: none;
        transition: transform 0.15s, box-shadow 0.15s;
    }
    .tcgplayer-btn:hover { transform: scale(1.05); box-shadow: 0 2px 8px rgba(237,100,166,0.5); color: #fff; }
    .grade-badge {
        display: inline-block; padding: 16px 28px; border-radius: 12px;
        font-weight: 900; font-size: 3em; letter-spacing: 2px;
        text-align: center; min-width: 90px;
    }
    .grade-a { background: linear-gradient(135deg, #22c55e, #10b981); color: #fff; }
    .grade-b { background: linear-gradient(135deg, #3b82f6, #2563eb); color: #fff; }
    .grade-c { background: linear-gradient(135deg, #facc15, #eab308); color: #000; }
    .grade-d { background: linear-gradient(135deg, #f97316, #ea580c); color: #fff; }
    .grade-f { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; }

    /* Card thumbnails */
    .card-thumb {
        width: 50px; height: 70px; border-radius: 4px;
        border: 1px solid #444; object-fit: cover;
    }
    .card-thumb-placeholder {
        width: 50px; height: 70px; border-radius: 4px;
        border: 1px solid #444; background: #1a1f2e;
        display: flex; align-items: center; justify-content: center;
        color: #666; font-size: 0.6em;
    }

    /* Format badges */
    .format-bin {
        display: inline-block; color: #fff; background: #3b82f6;
        padding: 1px 6px; border-radius: 3px; font-weight: bold;
        font-size: 0.7em; margin-right: 4px; vertical-align: middle;
    }
    .format-bid {
        display: inline-block; color: #fff; background: #f97316;
        padding: 1px 6px; border-radius: 3px; font-weight: bold;
        font-size: 0.7em; margin-right: 4px; vertical-align: middle;
    }

    /* Homepage feature cards */
    .feature-card {
        border: 1px solid #3b4560; border-radius: 12px;
        padding: 24px 20px; text-align: center; min-height: 150px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }
    .feature-card h3 { margin: 8px 0 4px 0; font-size: 1.2em; }
    .feature-card p { color: #9ca3af; font-size: 0.9em; }
    .feature-card-search { background: linear-gradient(135deg, #064e3b, #065f46); }
    .feature-card-breakout { background: linear-gradient(135deg, #7c2d12, #9a3412); }
    .feature-card-legends { background: linear-gradient(135deg, #713f12, #854d0e); }
    .feature-card-trade { background: linear-gradient(135deg, #1e3a5f, #1e40af); }
    .feature-card-portfolio { background: linear-gradient(135deg, #4a1d6e, #6b21a8); }
    .feature-card-grading { background: linear-gradient(135deg, #164e63, #0e7490); }

    /* Grading calculator verdicts */
    .grade-it { color: #fff; background-color: #22c55e; padding: 4px 12px; border-radius: 6px; font-weight: bold; }
    .maybe { color: #000; background-color: #facc15; padding: 4px 12px; border-radius: 6px; font-weight: bold; }
    .skip { color: #fff; background-color: #ef4444; padding: 4px 12px; border-radius: 6px; font-weight: bold; }

    /* Portfolio P&L colors */
    .pl-positive { color: #22c55e; font-weight: bold; }
    .pl-negative { color: #ef4444; font-weight: bold; }

    /* --- v3.0 Visual Polish --- */

    /* Score progress bars */
    .score-bar-container {
        width: 100%; height: 10px; background: #1a1f2e;
        border-radius: 5px; overflow: hidden; margin: 4px 0;
    }
    .score-bar-fill {
        height: 100%; border-radius: 5px;
        transition: width 0.8s ease-in-out;
    }
    .score-bar-green { background: linear-gradient(90deg, #22c55e, #10b981); }
    .score-bar-yellow { background: linear-gradient(90deg, #facc15, #eab308); }
    .score-bar-red { background: linear-gradient(90deg, #ef4444, #dc2626); }

    /* Row hover highlighting */
    div[data-testid="stHorizontalBlock"]:hover {
        background: rgba(255,255,255,0.03);
        border-radius: 6px;
        transition: background 0.2s;
    }

    /* Large card thumbnail */
    .card-thumb-lg {
        width: 80px; height: 112px; border-radius: 6px;
        border: 1px solid #444; object-fit: cover;
    }
    .card-thumb-lg-placeholder {
        width: 80px; height: 112px; border-radius: 6px;
        border: 1px solid #444; background: #1a1f2e;
        display: flex; align-items: center; justify-content: center;
        color: #666; font-size: 0.7em;
    }

    /* Gradient dividers */
    .gradient-divider {
        height: 2px; border: none; margin: 24px 0;
        background: linear-gradient(90deg, transparent, #ff4b1f, #ff9068, transparent);
        border-radius: 1px;
    }

    /* Animated metrics */
    div[data-testid="stMetric"] {
        animation: fadeUp 0.5s ease-out;
    }
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* New homepage feature card gradients */
    .feature-card-flip { background: linear-gradient(135deg, #065f46, #059669); }
    .feature-card-compare { background: linear-gradient(135deg, #4c1d95, #7c3aed); }

    /* Expected value badge */
    .ev-send { color: #fff; background-color: #22c55e; padding: 4px 12px; border-radius: 6px; font-weight: bold; }
    .ev-borderline { color: #000; background-color: #facc15; padding: 4px 12px; border-radius: 6px; font-weight: bold; }
    .ev-keep-raw { color: #fff; background-color: #ef4444; padding: 4px 12px; border-radius: 6px; font-weight: bold; }

    /* Flip finder spread */
    .spread-positive { color: #22c55e; font-weight: bold; font-size: 1.1em; }

    /* Live game tracker */
    .game-live {
        display: inline-block; color: #fff; background: #22c55e;
        padding: 2px 8px; border-radius: 4px; font-weight: bold;
        font-size: 0.8em; animation: pulse-green 2s infinite;
    }
    .game-final {
        display: inline-block; color: #fff; background: #6b7280;
        padding: 2px 8px; border-radius: 4px; font-weight: bold;
        font-size: 0.8em;
    }
    .game-scheduled {
        display: inline-block; color: #fff; background: #3b82f6;
        padding: 2px 8px; border-radius: 4px; font-weight: bold;
        font-size: 0.8em;
    }
    .feature-card-games { background: linear-gradient(135deg, #1e3a2f, #065f46); }

    /* v5.0 — Scanner */
    .scan-result {
        border: 1px solid #3b4560; border-radius: 12px;
        padding: 20px; margin: 10px 0;
    }
    .scan-confidence-high { color: #22c55e; font-weight: bold; }
    .scan-confidence-medium { color: #facc15; font-weight: bold; }
    .scan-confidence-low { color: #ef4444; font-weight: bold; }

    /* Alerts */
    .alert-watching {
        display: inline-block; color: #000; background: #facc15;
        padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85em;
    }
    .alert-triggered {
        display: inline-block; color: #fff; background: #22c55e;
        padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85em;
        animation: pulse-green 2s infinite;
    }

    /* Market Movers */
    .mover-gain { color: #22c55e; font-weight: bold; }
    .mover-loss { color: #ef4444; font-weight: bold; }

    /* PSA Population */
    .psa-gem { color: #22c55e; font-weight: bold; font-size: 1.1em; }
    .psa-badge {
        display: inline-block; color: #fff; background: #3b82f6;
        padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8em;
    }

    /* New feature card styles */
    .feature-card-scanner { background: linear-gradient(135deg, #7c2d12, #ea580c); }
    .feature-card-alerts { background: linear-gradient(135deg, #713f12, #d97706); }
    .feature-card-movers { background: linear-gradient(135deg, #064e3b, #10b981); }
    .feature-card-history { background: linear-gradient(135deg, #1e3a5f, #3b82f6); }

    /* Pro badge for nav */
    .pro-badge {
        display: inline-block; color: #fff; background: linear-gradient(135deg, #f59e0b, #d97706);
        padding: 1px 6px; border-radius: 3px; font-weight: bold;
        font-size: 0.65em; margin-left: 4px; vertical-align: middle;
    }

    /* --- v6.3 Conversion & Marketing --- */

    /* Hero CTA button */
    .hero-cta {
        display: inline-block; padding: 14px 40px; border-radius: 10px;
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: #1f2937; font-weight: 900; font-size: 1.2em;
        text-decoration: none; letter-spacing: 0.5px;
        transition: transform 0.2s, box-shadow 0.2s;
        cursor: pointer; border: none;
    }
    .hero-cta:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 16px rgba(245,158,11,0.5);
        color: #1f2937;
    }

    /* Teaser blur + overlay for paywalled content */
    .teaser-blur {
        filter: blur(6px); pointer-events: none;
        user-select: none; -webkit-user-select: none;
        opacity: 0.6;
    }
    .teaser-overlay {
        background: linear-gradient(180deg, transparent 0%, rgba(30,58,95,0.95) 50%);
        border-radius: 10px; padding: 24px 20px; text-align: center;
        margin-top: -40px; position: relative; z-index: 2;
    }

    /* Trial urgency badges */
    .trial-urgent {
        background: linear-gradient(135deg, #dc2626, #b91c1c);
        color: #fff; font-weight: bold; padding: 8px 12px;
        border-radius: 8px; text-align: center; font-size: 0.9em;
        margin-bottom: 6px; animation: pulse-fire 2s infinite;
    }
    .trial-normal {
        background: linear-gradient(135deg, #facc15, #f97316);
        color: #1f2937; font-weight: bold; padding: 8px 12px;
        border-radius: 8px; text-align: center; font-size: 0.9em;
        margin-bottom: 6px;
    }

    /* Social proof strip */
    .social-proof-strip {
        display: flex; justify-content: center; gap: 40px;
        padding: 12px 20px; margin: 10px 0 20px 0;
        background: rgba(255,255,255,0.04); border-radius: 8px;
    }
    .social-proof-strip .stat {
        text-align: center;
    }
    .social-proof-strip .stat-value {
        font-size: 1.3em; font-weight: 900; color: #f59e0b;
    }
    .social-proof-strip .stat-label {
        font-size: 0.8em; color: #9ca3af;
    }

    /* Best value badge for pricing */
    .best-value-badge {
        display: inline-block; background: linear-gradient(135deg, #22c55e, #10b981);
        color: #fff; padding: 3px 10px; border-radius: 4px;
        font-weight: bold; font-size: 0.75em; text-transform: uppercase;
        letter-spacing: 0.5px; animation: pulse-green 2s infinite;
    }

    /* Nav PRO suffix */
    .nav-pro {
        color: #f59e0b; font-weight: bold; font-size: 0.7em;
    }

    /* --- Mobile responsive --- */
    @media (max-width: 768px) {
        .feature-card { padding: 16px 12px; min-height: 100px; }
        .feature-card h3 { font-size: 1em; }
        .feature-card p { font-size: 0.8em; }
        .card-thumb-lg { width: 60px; height: 84px; }
        .grade-badge { padding: 10px 18px; font-size: 2em; }
        .ebay-btn { padding: 6px 10px; font-size: 0.8em; }
    }
</style>
""", unsafe_allow_html=True)


# --- Sidebar Navigation ---
st.sidebar.title("🦈 Card Shark")
st.sidebar.caption("Your Edge in the Hobby")

# --- Auth ---
current_user = render_auth_ui()
if "anon_searches_used" not in st.session_state:
    st.session_state.anon_searches_used = 0
st.sidebar.markdown("---")

# --- Stripe return handler (after successful checkout) ---
try:
    _qp = st.query_params
    if _qp.get("upgrade") == "success" and _qp.get("session_id") and not st.session_state.get("_stripe_handled"):
        from billing import handle_stripe_return
        handle_stripe_return(dict(_qp))
        st.session_state["_stripe_handled"] = True
    elif _qp.get("upgrade") == "cancel":
        st.info("Checkout canceled — no charge was made. You can try again anytime.")
except AttributeError:
    pass  # query_params not available on older Streamlit versions
except Exception as e:
    st.error(f"Payment verification failed. If you were charged, email hello@cardsharkapp.com with your receipt. Error: {e}")

# Nav items grouped: Discover → Tools → Market → My Stuff
_NAV_ITEMS = [
    # Discover
    "🏠 Home",
    "🔍 Player Search",
    "💰 What Can I Get?",
    "🚀 Breakout Leaderboard",
    "🏆 Legend Cards",
    "🏟️ Live Games",
    # Tools
    "📷 Card Scanner",
    "🔄 Trade Checker",
    "⚔️ Player Comparison",
    "📐 Grading Calculator",
    # Market
    "💰 Flip Finder",
    "📈 Market Movers",
    "📊 Price History",
    "🔔 Price Alerts",
    # My Stuff
    "📁 My Collection",
]

_NAV_MAP = {label: label.split(" ", 1)[1] for label in _NAV_ITEMS}

# Features that require Pro — show "PRO" suffix in nav
from config.settings import PRO_FEATURES
_PRO_NAV_LABELS = {"Flip Finder", "Player Comparison", "Market Movers",
                   "Price Alerts", "Grading Calculator", "Price History"}

# If a homepage button requested a page change, apply before radio renders
_force_upgrade = False
_force_legal = None
if "nav_target" in st.session_state:
    target = st.session_state.nav_target
    del st.session_state.nav_target
    if target == "upgrade":
        _force_upgrade = True
    elif target in ("legal_terms", "legal_privacy", "legal_disclosure"):
        _force_legal = target
    else:
        st.session_state.nav_page = target

def _nav_format(label):
    """Add PRO suffix to gated features for non-pro users."""
    feature_name = label.split(" ", 1)[1] if " " in label else label
    if feature_name in _PRO_NAV_LABELS and not is_pro():
        return f"{label}  PRO"
    return label

_selected_nav = st.sidebar.radio(
    "Navigate",
    _NAV_ITEMS,
    key="nav_page",
    format_func=_nav_format,
)

if _force_upgrade:
    page = "Upgrade"
elif _force_legal:
    page = _force_legal
else:
    page = _NAV_MAP[_selected_nav]

DEMO_MODE = not _ebay_is_configured()

# --- Sidebar: Connection Status ---
st.sidebar.markdown("---")
if DEMO_MODE:
    st.sidebar.markdown("🟠 **Preview Mode** — sample data")
    st.sidebar.caption("Live market data coming soon")
else:
    if st.sidebar.button("🔌 Test Connection"):
        with st.sidebar:
            with st.spinner("Testing eBay APIs..."):
                conn = test_ebay_connection()
            browse_icon = "🟢" if conn["browse"] else "🔴"
            finding_icon = "🟢" if conn["finding"] else "🔴"
            st.sidebar.markdown(f"{browse_icon} Browse API (active listings)")
            st.sidebar.markdown(f"{finding_icon} Finding API (sold data)")
            if conn["browse"] and conn["finding"]:
                st.sidebar.success("Both APIs connected!")
            elif conn["browse"] or conn["finding"]:
                st.sidebar.warning("Partial connection — check API settings")
            else:
                st.sidebar.error("Both APIs failed — check credentials")
    else:
        st.sidebar.markdown("🟢 **Live Mode** — eBay APIs configured")


# ============================================================
# PAGE DISPATCH
# ============================================================
if page == "Home":
    home.render(current_user)
elif page == "Card Scanner":
    card_scanner.render()
elif page == "Live Games":
    live_games.render()
elif page == "Player Search":
    player_search.render(demo_mode=DEMO_MODE)
elif page == "What Can I Get?":
    budget_finder.render(demo_mode=DEMO_MODE)
elif page == "Price History":
    price_history.render()
elif page == "Breakout Leaderboard":
    breakout_leaderboard.render(demo_mode=DEMO_MODE)
elif page == "Legend Cards":
    legend_cards.render(demo_mode=DEMO_MODE)
elif page == "Trade Checker":
    trade_checker.render()
elif page == "Flip Finder":
    flip_finder_page.render()
elif page == "Player Comparison":
    player_comparison.render()
elif page == "Market Movers":
    market_movers.render()
elif page == "Price Alerts":
    price_alerts_page.render()
elif page == "My Collection":
    my_collection.render(current_user)
elif page == "Grading Calculator":
    grading_calculator.render()
elif page == "Upgrade":
    from billing import render_pricing_page
    render_pricing_page()
elif page in ("legal_terms", "legal_privacy", "legal_disclosure"):
    _LEGAL_FILES = {
        "legal_terms": ("Terms of Service", "legal/terms.md"),
        "legal_privacy": ("Privacy Policy", "legal/privacy.md"),
        "legal_disclosure": ("Affiliate Disclosure", "legal/disclosure.md"),
    }
    _title, _path = _LEGAL_FILES[page]
    st.title(_title)
    try:
        with open(_path, "r", encoding="utf-8") as _f:
            st.markdown(_f.read())
    except FileNotFoundError:
        st.error(f"{_title} is not available right now.")


# --- Footer ---
st.sidebar.markdown("---")
if current_user and not is_pro():
    if st.sidebar.button("⚡ Upgrade to Pro — $7.99/mo", key="sidebar_upgrade", use_container_width=True):
        st.session_state.nav_target = "upgrade"
        st.rerun()

st.sidebar.markdown("---")
_lf1, _lf2, _lf3 = st.sidebar.columns(3)
with _lf1:
    if st.button("Terms", key="footer_terms", use_container_width=True):
        st.session_state.nav_target = "legal_terms"
        st.rerun()
with _lf2:
    if st.button("Privacy", key="footer_privacy", use_container_width=True):
        st.session_state.nav_target = "legal_privacy"
        st.rerun()
with _lf3:
    if st.button("FTC", key="footer_disclosure", use_container_width=True):
        st.session_state.nav_target = "legal_disclosure"
        st.rerun()
st.sidebar.caption("Card Shark earns affiliate commissions on some links. Not financial advice.")
st.sidebar.caption("Card Shark v6.3")
