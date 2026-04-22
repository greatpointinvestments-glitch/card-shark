"""Legend Cards page."""

import re
import streamlit as st

from modules.ui_helpers import (
    signal_badge, score_progress_bar, gradient_divider,
    render_listing_row, render_listing_compact, market_signal_badge,
)
from modules.legends import build_legends_table, get_hidden_gems
from modules.ebay_search import search_ebay_cards, search_ebay_sold, flag_deals, get_market_summary
from modules.card_types import get_card_type_options
from data.watchlists import LEGENDS_WATCHLIST, POKEMON_LEGENDS_WATCHLIST


def _render_legend_deep_dive(legend: dict, source: dict, demo_mode: bool = False):
    """Render inline Deep Dive for a legend player."""
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Investment Score", legend["score"])
    d2.metric("HOF / Legacy", legend["hof_score"])
    d3.metric("Iconic Card Factor", legend["iconic_score"])
    d4.metric("Undervalued Score", legend["market_score"])

    st.write(f"**Key Cards:** {legend['iconic_cards']}")
    st.write(f"**Analysis:** {legend['notes']}")

    card_type = st.selectbox("Card Type", get_card_type_options(), key=f"ldd_ct_{legend['name']}")

    lf1, lf2, lf3 = st.columns(3)
    with lf1:
        leg_buying_format = st.selectbox("Buying Format", ["All", "BIN Only", "Auction Only"], key=f"ldd_bf_{legend['name']}")
    with lf2:
        leg_condition = st.selectbox("Condition", ["All", "Raw Only", "Graded Only"], key=f"ldd_cond_{legend['name']}")
    with lf3:
        leg_budget = st.number_input("My Budget ($)", min_value=0.0, value=0.0, step=5.0, key=f"ldd_bud_{legend['name']}", help="0 = no limit")

    with st.spinner("Searching eBay..."):
        legend_listings = search_ebay_cards(legend["name"], source["sport"], card_type, limit=30)
        legend_listings = flag_deals(legend_listings)

    _GRADED_RE = re.compile(r"\b(PSA|BGS|SGC|CGC)\b", re.IGNORECASE)

    if legend_listings:
        total_count = len(legend_listings)
        filtered_list = legend_listings

        if leg_buying_format == "BIN Only":
            filtered_list = [l for l in filtered_list if l.get("buying_format") == "BIN"]
        elif leg_buying_format == "Auction Only":
            filtered_list = [l for l in filtered_list if l.get("buying_format") == "Auction"]

        if leg_condition == "Graded Only":
            filtered_list = [l for l in filtered_list if _GRADED_RE.search(l.get("title", ""))]
        elif leg_condition == "Raw Only":
            filtered_list = [l for l in filtered_list if not _GRADED_RE.search(l.get("title", ""))]

        if leg_budget > 0:
            filtered_list = [l for l in filtered_list if l.get("total", 0) <= leg_budget]

        median_str = f"${legend_listings[0].get('median', '?')}"
        if len(filtered_list) < total_count:
            st.success(f"Showing {len(filtered_list)} of {total_count} listings | Median: {median_str}")
        else:
            st.success(f"Found {total_count} listings | Median: {median_str}")

        sorted_listings = sorted(filtered_list, key=lambda l: l.get("vs_median", 0))
        for listing in sorted_listings[:10]:
            render_listing_compact(listing)

        with st.spinner("Fetching sold data..."):
            sold = search_ebay_sold(legend["name"], source["sport"], card_type, limit=30)
        if sold:
            summary = get_market_summary(legend_listings, sold)
            demo_tag = " (Sample)" if demo_mode else ""
            st.markdown(f"**Sold Market{demo_tag}:**")
            lm1, lm2, lm3, lm4 = st.columns(4)
            lm1.metric("Avg Sold Price", f"${summary['avg_sold']:.2f}")
            lm2.metric("90d Volume", f"{summary['sold_volume']} sales")
            lm3.metric("Price Trend", summary["price_trend"], f"{summary['trend_delta']:+.1f}%")
            lm4.markdown("**Market Signal**")
            lm4.markdown(market_signal_badge(summary["market_signal"]), unsafe_allow_html=True)
    else:
        st.info("No listings found for this player.")


def render(demo_mode: bool = False):
    st.title("🏆 Legend Cards")
    st.caption("The GOATs. The classics. The cards your dad wishes he kept.")

    all_sources = LEGENDS_WATCHLIST + POKEMON_LEGENDS_WATCHLIST
    legends = build_legends_table(all_sources)

    if not legends:
        st.error("Could not load legends data.")
        return

    strong_buys = sum(1 for p in legends if p["rating"] == "STRONG BUY")
    buys = sum(1 for p in legends if p["rating"] == "BUY")

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Legends", len(legends))
    m2.metric("STRONG BUY", strong_buys)
    m3.metric("BUY", buys)

    sport_filter = st.multiselect("Filter by Sport", ["NBA", "NFL", "MLB", "Pokemon"], default=["NBA", "NFL", "MLB", "Pokemon"])
    filtered = [p for p in legends if p["sport"] in sport_filter]

    gradient_divider()

    # Track which legend is expanded
    expanded_legend = st.session_state.get("legend_expanded")

    for player in filtered:
        cols = st.columns([0.5, 2.5, 0.8, 1.5, 1, 1.5])
        with cols[0]:
            st.write(f"**#{player['rank']}**")
        with cols[1]:
            _is_expanded = expanded_legend == player["name"]
            _btn_label = f"{'▼' if _is_expanded else '▶'} {player['name']}"
            if st.button(_btn_label, key=f"leg_{player['name']}_{player['rank']}",
                         use_container_width=True):
                if _is_expanded:
                    st.session_state["legend_expanded"] = None
                else:
                    st.session_state["legend_expanded"] = player["name"]
                st.rerun()
        with cols[2]:
            st.write(player["sport"])
        with cols[3]:
            st.write(player["hof"])
        with cols[4]:
            st.write(f"**{player['score']}**")
            st.markdown(score_progress_bar(player['score']), unsafe_allow_html=True)
        with cols[5]:
            st.markdown(signal_badge(player["rating"]), unsafe_allow_html=True)

        # Inline Deep Dive
        if expanded_legend == player["name"]:
            source = next((p for p in all_sources if p["name"] == player["name"]), None)
            if source:
                st.markdown("---")
                _render_legend_deep_dive(player, source, demo_mode)
                st.markdown("---")

    # Hidden Gems
    gradient_divider()
    st.markdown("### Hidden Gems")
    st.caption("Players whose cards are underpriced relative to their career significance")

    gem_card_type = st.selectbox("Card Type", get_card_type_options(), key="gem_card_type")

    gems = get_hidden_gems(legends)
    if gems:
        for gem in gems:
            st.markdown(f"**{gem['name']}** ({gem['sport']}) — Score: {gem['score']} | {gem['rating']}")

            g1, g2, g3, g4 = st.columns(4)
            g1.metric("HOF/Legacy", gem["hof_score"])
            g2.metric("Iconic Card", gem["iconic_score"])
            g3.metric("Undervalued", gem["market_score"])
            g4.metric("Cultural", gem["cultural_score"])

            st.write(f"**Key Cards:** {gem['iconic_cards']}")
            st.write(f"**Why:** {gem['notes']}")

            if st.button(f"Search eBay for {gem['name']}", key=f"gem_{gem['name']}"):
                with st.spinner("Searching eBay..."):
                    gem_listings = search_ebay_cards(gem["name"], gem["sport"], gem_card_type, limit=20)
                    gem_listings = flag_deals(gem_listings)

                if gem_listings:
                    sorted_gems = sorted(gem_listings, key=lambda l: l.get("vs_median", 0))
                    for listing in sorted_gems[:10]:
                        render_listing_compact(listing)
                else:
                    st.info("No listings found for this player.")

            gradient_divider()
    else:
        st.info("No hidden gems identified in current data.")

    with st.expander("How Legend Ratings Work"):
        st.markdown("""
**STRONG BUY** = high significance + undervalued market + iconic cards. These legends have cards trading below where their legacy suggests they should be.

**BUY** = solid investment-grade legend. Cards hold value well and have room to grow.

**HOLD** = fairly priced for their legacy. Not overpriced, but not a bargain either.

**Score** (0-100) blends: HOF/Legacy status (30%), iconic card factor (25%), market undervaluation (25%), cultural impact (20%).
        """)
