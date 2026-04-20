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


def render(demo_mode: bool = False):
    st.title("🏆 Legend Cards")
    st.caption("The GOATs. The classics. The cards your dad wishes he kept.")

    legends = build_legends_table(LEGENDS_WATCHLIST + POKEMON_LEGENDS_WATCHLIST)

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

    for player in filtered:
        cols = st.columns([0.5, 2.5, 0.8, 1.5, 1, 1.5])
        with cols[0]:
            st.write(f"**#{player['rank']}**")
        with cols[1]:
            st.write(f"**{player['name']}**")
        with cols[2]:
            st.write(player["sport"])
        with cols[3]:
            st.write(player["hof"])
        with cols[4]:
            st.write(f"**{player['score']}**")
            st.markdown(score_progress_bar(player['score']), unsafe_allow_html=True)
        with cols[5]:
            st.markdown(signal_badge(player["rating"]), unsafe_allow_html=True)

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
                    for listing in gem_listings[:10]:
                        render_listing_compact(listing)
                else:
                    st.info("No listings found for this player.")

            gradient_divider()
    else:
        st.info("No hidden gems identified in current data.")

    # Deep Dive
    st.markdown("### Player Deep Dive")
    legend_names = [p["name"] for p in legends]
    selected_legend = st.selectbox("Select a legend", legend_names)

    if selected_legend:
        legend = next(p for p in legends if p["name"] == selected_legend)
        source = next(p for p in LEGENDS_WATCHLIST if p["name"] == selected_legend)

        st.markdown(f"#### {selected_legend}")

        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Investment Score", legend["score"])
        d2.metric("HOF / Legacy", legend["hof_score"])
        d3.metric("Iconic Card Factor", legend["iconic_score"])
        d4.metric("Undervalued Score", legend["market_score"])

        st.write(f"**Key Cards:** {legend['iconic_cards']}")
        st.write(f"**Analysis:** {legend['notes']}")

        card_type = st.selectbox("Card Type", get_card_type_options(), key="legend_card_type")

        lf1, lf2, lf3 = st.columns(3)
        with lf1:
            leg_buying_format = st.selectbox("Buying Format", ["All", "BIN Only", "Auction Only"], key="legend_buying_format")
        with lf2:
            leg_condition = st.selectbox("Condition", ["All", "Raw Only", "Graded Only"], key="legend_condition")
        with lf3:
            leg_budget = st.number_input("My Budget ($)", min_value=0.0, value=0.0, step=5.0, key="legend_budget", help="0 = no limit")

        if st.button(f"Search eBay for {selected_legend} Cards"):
            with st.spinner("Searching eBay..."):
                legend_listings = search_ebay_cards(selected_legend, source["sport"], card_type, limit=30)
                legend_listings = flag_deals(legend_listings)

            _GRADED_RE = re.compile(r"\b(PSA|BGS|SGC|CGC)\b", re.IGNORECASE)

            if legend_listings:
                total_count = len(legend_listings)
                filtered = legend_listings

                if leg_buying_format == "BIN Only":
                    filtered = [l for l in filtered if l.get("buying_format") == "BIN"]
                elif leg_buying_format == "Auction Only":
                    filtered = [l for l in filtered if l.get("buying_format") == "Auction"]

                if leg_condition == "Graded Only":
                    filtered = [l for l in filtered if _GRADED_RE.search(l.get("title", ""))]
                elif leg_condition == "Raw Only":
                    filtered = [l for l in filtered if not _GRADED_RE.search(l.get("title", ""))]

                if leg_budget > 0:
                    filtered = [l for l in filtered if l.get("total", 0) <= leg_budget]

                median_str = f"${legend_listings[0].get('median', '?')}"
                if len(filtered) < total_count:
                    st.success(f"Showing {len(filtered)} of {total_count} listings | Median: {median_str}")
                else:
                    st.success(f"Found {total_count} listings | Median: {median_str}")
                for listing in filtered:
                    render_listing_row(listing)

                with st.spinner("Fetching sold data..."):
                    sold = search_ebay_sold(selected_legend, source["sport"], card_type, limit=30)
                if sold:
                    summary = get_market_summary(legend_listings, sold)
                    demo_tag = " (Sample)" if demo_mode else ""
                    gradient_divider()
                    st.markdown(f"**Sold Market Analytics{demo_tag}:**")
                    lm1, lm2, lm3, lm4 = st.columns(4)
                    lm1.metric("Avg Sold Price", f"${summary['avg_sold']:.2f}")
                    lm2.metric("90d Volume", f"{summary['sold_volume']} sales")
                    lm3.metric("Price Trend", summary["price_trend"], f"{summary['trend_delta']:+.1f}%")
                    lm4.markdown("**Market Signal**")
                    lm4.markdown(market_signal_badge(summary["market_signal"]), unsafe_allow_html=True)
            else:
                st.info("No listings found for this player.")


render(demo_mode=False)
