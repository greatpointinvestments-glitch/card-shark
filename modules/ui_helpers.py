"""Shared UI helpers — reusable rendering functions for eBay listings, metrics, and badges.

Extracted from app.py to eliminate 300+ duplicated lines across pages.
"""

import streamlit as st
from modules.affiliates import affiliate_url


# --- Thumbnails ---

def card_thumbnail(image_url: str) -> str:
    """Return an HTML img tag for a card thumbnail, or a placeholder div."""
    if image_url:
        return f'<img src="{image_url}" class="card-thumb" />'
    return '<div class="card-thumb-placeholder">N/A</div>'


def card_thumbnail_lg(image_url: str) -> str:
    """Return an HTML img tag for a large card thumbnail (80x112), or a placeholder."""
    if image_url:
        return f'<img src="{image_url}" class="card-thumb-lg" />'
    return '<div class="card-thumb-lg-placeholder">N/A</div>'


# --- Badges ---

def signal_badge(signal: str) -> str:
    """Return an HTML badge for a signal."""
    css_class = {
        "BUY": "buy-signal",
        "WATCH": "watch-signal",
        "HOLD": "hold-signal",
        "STRONG BUY": "strong-buy",
        "PASS": "pass-signal",
    }.get(signal, "hold-signal")
    return f'<span class="{css_class}">{signal}</span>'


def market_signal_badge(signal: str) -> str:
    """Return an HTML badge for a market signal."""
    css_class = {
        "BUY WINDOW": "market-buy",
        "FAIR VALUE": "market-fair",
        "OVERPRICED": "market-over",
        "N/A": "market-fair",
    }.get(signal, "market-fair")
    label = "Not enough data" if signal == "N/A" else signal
    return f'<span class="{css_class}">{label}</span>'


def deal_badge(vs_median: float) -> str:
    """Return STEAL, DEAL, or empty string based on vs_median percentage."""
    if vs_median <= -20:
        return '<span style="color:#fff;background:linear-gradient(135deg,#22c55e,#10b981);padding:2px 8px;border-radius:4px;font-weight:900;font-size:0.75em;text-transform:uppercase;letter-spacing:0.5px;margin-right:4px;">STEAL</span>'
    elif vs_median < 0:
        return '<span style="color:#fff;background:linear-gradient(135deg,#ff4b1f,#ff9068);padding:2px 8px;border-radius:4px;font-weight:900;font-size:0.75em;text-transform:uppercase;letter-spacing:0.5px;margin-right:4px;">DEAL</span>'
    return ""


def deal_score(vs_median: float) -> int:
    """Convert vs_median percentage into a 0-100 deal score (higher = better deal)."""
    return max(0, min(100, round(50 - vs_median)))


def deal_score_badge(vs_median: float) -> str:
    """Return a colored score pill based on deal score."""
    score = deal_score(vs_median)
    if score >= 80:
        return f'<span style="display:inline-block;color:#fff;background:#22c55e;padding:1px 8px;border-radius:10px;font-weight:bold;font-size:0.8em;margin-left:6px;">🔥 {score}</span>'
    elif score >= 60:
        return f'<span style="display:inline-block;color:#fff;background:#4ade80;padding:1px 8px;border-radius:10px;font-weight:bold;font-size:0.8em;margin-left:6px;">{score}</span>'
    elif score >= 40:
        return f'<span style="display:inline-block;color:#000;background:#facc15;padding:1px 8px;border-radius:10px;font-weight:bold;font-size:0.8em;margin-left:6px;">{score}</span>'
    else:
        return f'<span style="display:inline-block;color:#fff;background:#6b7280;padding:1px 8px;border-radius:10px;font-weight:bold;font-size:0.8em;margin-left:6px;">{score}</span>'


def format_badge(buying_format: str) -> str:
    """Return a compact BIN/BID badge."""
    if buying_format == "Auction":
        return '<span style="display:inline-block;color:#fff;background:#f97316;padding:1px 6px;border-radius:3px;font-weight:bold;font-size:0.7em;margin-right:4px;vertical-align:middle;">BID</span>'
    return '<span style="display:inline-block;color:#fff;background:#3b82f6;padding:1px 6px;border-radius:3px;font-weight:bold;font-size:0.7em;margin-right:4px;vertical-align:middle;">BIN</span>'


def score_progress_bar(score: float, max_score: float = 100) -> str:
    """Return HTML for a colored progress bar based on score."""
    pct = min(max(score / max_score * 100, 0), 100)
    if pct >= 75:
        color_class = "score-bar-green"
    elif pct >= 50:
        color_class = "score-bar-yellow"
    else:
        color_class = "score-bar-red"
    return (
        f'<div class="score-bar-container">'
        f'<div class="score-bar-fill {color_class}" style="width:{pct:.0f}%"></div>'
        f'</div>'
    )


# --- Links ---

def ebay_link(title: str, url: str, max_chars: int = 70, vs_median: float = 0, buying_format: str = "BIN") -> str:
    """Return a linked listing title with format badge and optional DEAL/STEAL badge."""
    truncated = title[:max_chars]
    fmt = format_badge(buying_format)
    badge = deal_badge(vs_median)
    aff_url = affiliate_url(url)
    return f'{fmt}{badge}<a href="{aff_url}" target="_blank" style="text-decoration:none">{truncated}</a>'


def ebay_button(url: str) -> str:
    """Return a styled buy button that opens the eBay listing in a new tab."""
    aff_url = affiliate_url(url)
    return f'<a href="{aff_url}" target="_blank" class="ebay-btn">Grab It</a>'


def tcgplayer_button(url: str) -> str:
    """Return a styled TCGPlayer buy button."""
    aff_url = affiliate_url(url)
    return f'<a href="{aff_url}" target="_blank" class="tcgplayer-btn">Buy on TCGPlayer</a>'


def whatnot_button(url: str) -> str:
    """Return a styled Whatnot button."""
    aff_url = affiliate_url(url)
    return f'<a href="{aff_url}" target="_blank" class="whatnot-btn">Watch on Whatnot</a>'


def topps_button(url: str) -> str:
    """Return a styled Topps button."""
    aff_url = affiliate_url(url)
    return f'<a href="{aff_url}" target="_blank" class="topps-btn">Shop Topps</a>'


def beckett_button(url: str) -> str:
    """Return a styled Beckett button."""
    aff_url = affiliate_url(url)
    return f'<a href="{aff_url}" target="_blank" class="beckett-btn">Price Guide</a>'


def drip_shop_button(url: str) -> str:
    """Return a styled Drip Shop Live button."""
    aff_url = affiliate_url(url)
    return f'<a href="{aff_url}" target="_blank" class="drip-shop-btn">Watch Live</a>'


def supplies_button(url: str, label: str = "Shop") -> str:
    """Return a styled green supplies button."""
    aff_url = affiliate_url(url)
    return f'<a href="{aff_url}" target="_blank" class="supplies-btn">{label}</a>'


def marketplace_button(url: str, sport: str = "") -> str:
    """Return the correct marketplace button based on sport context."""
    if sport == "Pokemon" and "tcgplayer.com" in (url or ""):
        return tcgplayer_button(url)
    return ebay_button(url)


# --- Layout helpers ---

def gradient_divider():
    """Render a gradient divider instead of a plain ---."""
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)


def render_table(rows: list[dict]):
    """Render a list of dicts as a markdown table (avoids pyarrow dependency)."""
    if not rows:
        return
    headers = list(rows[0].keys())
    header_line = "| " + " | ".join(str(h) for h in headers) + " |"
    sep_line = "| " + " | ".join("---" for _ in headers) + " |"
    body_lines = []
    for row in rows:
        body_lines.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")
    st.markdown("\n".join([header_line, sep_line] + body_lines))


# --- Composite listing rows ---

def render_listing_row(listing: dict, show_player: bool = False):
    """Render a full 6-column eBay listing row (thumb, title, price, shipping, total, button)."""
    cols = st.columns([0.5, 3, 1, 1, 1, 1])
    title = listing["title"]
    url = listing["url"]
    vs = listing.get("vs_median", 0)
    fmt = listing.get("buying_format", "BIN")

    with cols[0]:
        st.markdown(card_thumbnail(listing.get("image_url", "")), unsafe_allow_html=True)
    with cols[1]:
        link_html = ebay_link(title, url, max_chars=70, vs_median=vs, buying_format=fmt)
        if show_player:
            player = listing.get("player", "")
            sport = listing.get("sport", "")
            link_html += f'<br><small style="color:#9ca3af">{player} • {sport}</small>'
        st.markdown(link_html, unsafe_allow_html=True)
    with cols[2]:
        price_val = listing.get('price', listing.get('total', 0))
        if fmt == "Auction":
            bids = listing.get("bid_count", 0)
            if bids == 0:
                price_str = f"${price_val:.2f}" if price_val > 0 else "—"
                price_str += " (No bids)"
            else:
                price_str = f"${price_val:.2f} ({bids} bid{'s' if bids != 1 else ''})"
        else:
            price_str = f"${price_val:.2f}"
        st.write(price_str)
    with cols[3]:
        ship = listing.get("shipping", 0)
        st.write(f"+${ship:.2f} ship" if ship > 0 else "Free ship")
    with cols[4]:
        total = listing["total"]
        if fmt == "Auction" and listing.get("bid_count", 0) == 0:
            st.markdown(f"**${total:.2f}**" if total > 0 else "**—**", unsafe_allow_html=True)
        else:
            badge = deal_score_badge(vs)
            st.markdown(f"**${total:.2f}** {badge}", unsafe_allow_html=True)
    with cols[5]:
        st.markdown(ebay_button(url), unsafe_allow_html=True)


def render_listing_compact(listing: dict):
    """Render a compact 4-column listing row (thumb, title, total, button)."""
    c0, c1, c2, c3 = st.columns([0.5, 3, 1, 1])
    title = listing["title"]
    url = listing["url"]
    vs = listing.get("vs_median", 0)
    fmt = listing.get("buying_format", "BIN")
    with c0:
        st.markdown(card_thumbnail(listing.get("image_url", "")), unsafe_allow_html=True)
    with c1:
        st.markdown(ebay_link(title, url, max_chars=65, vs_median=vs, buying_format=fmt), unsafe_allow_html=True)
    with c2:
        if fmt == "Auction":
            bids = listing.get("bid_count", 0)
            if bids == 0:
                price_str = f"${listing['total']:.2f}" if listing['total'] > 0 else "—"
                price_str += " (No bids)"
                st.write(price_str)
            else:
                price_str = f"${listing['total']:.2f} ({bids} bid{'s' if bids != 1 else ''})"
                badge = deal_score_badge(vs)
                st.markdown(f"{price_str} {badge}", unsafe_allow_html=True)
        else:
            badge = deal_score_badge(vs)
            st.markdown(f"${listing['total']:.2f} {badge}", unsafe_allow_html=True)
    with c3:
        st.markdown(ebay_button(url), unsafe_allow_html=True)


def render_sold_row(listing: dict):
    """Render a sold listing row (thumb, title, price, date, type)."""
    sc0, sc1, sc2, sc3, sc4 = st.columns([0.5, 3.5, 1, 1, 1])
    with sc0:
        st.markdown(card_thumbnail(listing.get("image_url", "")), unsafe_allow_html=True)
    with sc1:
        aff_sold_url = affiliate_url(listing["url"])
        st.markdown(f'<a href="{aff_sold_url}" target="_blank">{listing["title"][:70]}</a>', unsafe_allow_html=True)
    with sc2:
        price = listing.get("sold_price", listing.get("total", 0))
        st.write(f"${price:.2f}")
    with sc3:
        st.write(listing.get("sold_date", ""))
    with sc4:
        st.write(listing.get("listing_type", ""))


def render_fuzzy_suggestions(query: str, sport: str | None = None, key_prefix: str = "fz"):
    """Render 'Did you mean:' chips if query doesn't exactly match known players.
    Returns the selected suggestion name if clicked, else None."""
    from modules.fuzzy_search import suggest_players, has_exact_match
    if not query or has_exact_match(query, sport):
        return None
    suggestions = suggest_players(query, sport, limit=4)
    if not suggestions:
        return None
    st.markdown(
        '<span style="color:#9ca3af;font-size:0.9em;">Did you mean:</span>',
        unsafe_allow_html=True,
    )
    cols = st.columns(min(len(suggestions), 4))
    for i, s in enumerate(suggestions):
        with cols[i]:
            if st.button(s["name"], key=f"{key_prefix}_{i}_{s['name']}", use_container_width=True):
                return s["name"]
    return None


def render_market_summary(summary: dict, demo_mode: bool = False):
    """Render market analytics as a 4-column metric row."""
    demo_tag = " (Sample)" if demo_mode else ""
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric(f"Avg Sold Price{demo_tag}", f"${summary['avg_sold']:.2f}")
    mc2.metric("90d Volume", f"{summary['sold_volume']} sales")
    trend_arrow = "+" if summary["trend_delta"] > 0 else ""
    mc3.metric("Price Trend", summary["price_trend"], f"{trend_arrow}{summary['trend_delta']}%")
    mc4.markdown("**Market Signal**")
    mc4.markdown(market_signal_badge(summary["market_signal"]), unsafe_allow_html=True)
