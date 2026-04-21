"""Player Search page."""

import re
import streamlit as st

from modules.ui_helpers import (
    render_listing_row, render_sold_row, render_market_summary,
    gradient_divider, market_signal_badge, ebay_button, tcgplayer_button,
    whatnot_button, topps_button, beckett_button, drip_shop_button,
)
from modules.player_stats import search_players, get_multi_season_stats, format_player_info
from modules.ebay_search import search_ebay_cards, search_ebay_sold, flag_deals, get_market_summary
from modules.pokemon_tcg import search_pokemon_cards, get_pokemon_market_price, get_pokemon_market_summary
from modules.price_history import get_price_history, build_price_chart
from modules.psa_population import lookup_psa_population
from modules.card_types import get_card_type_options
from modules.affiliates import (
    affiliate_url, tcgplayer_search_affiliate_url,
    whatnot_search_affiliate_url, topps_search_affiliate_url,
    beckett_search_affiliate_url, drip_shop_search_affiliate_url,
)
from modules.ui_helpers import render_table
from config.settings import SPORTS
from tiers import check_usage_limit, increment_and_check, render_limit_warning, render_disclaimer, render_contextual_upsell, is_pro

QUICK_PICKS = {
    "NBA": ["Victor Wembanyama", "LeBron James", "Anthony Edwards", "Jared McCain", "Chet Holmgren"],
    "NFL": ["Caleb Williams", "CJ Stroud", "Marvin Harrison Jr", "Brock Bowers", "Puka Nacua"],
    "MLB": ["Paul Skenes", "Elly De La Cruz", "Gunnar Henderson", "Jackson Chourio", "Corbin Carroll"],
    "Pokemon": ["Charizard", "Pikachu", "Mewtwo", "Lugia", "Umbreon"],
}

_SPORT_OPTIONS = ["NBA", "NFL", "MLB", "Pokemon"]


def _push_search_history(name: str, sport: str):
    entry = (name, sport)
    hist = st.session_state.search_history
    if entry in hist:
        hist.remove(entry)
    hist.insert(0, entry)
    st.session_state.search_history = hist[:5]


def render(demo_mode: bool = False):
    st.title("🔍 Player Search")
    st.caption("Look up any player — stats, card prices, and the best deals on eBay")
    render_disclaimer(compact=True)

    if "search_history" not in st.session_state:
        st.session_state.search_history = []
    if "prefill_player" not in st.session_state:
        st.session_state.prefill_player = ""
    if "prefill_sport" not in st.session_state:
        st.session_state.prefill_sport = "NBA"
    if "active_player" not in st.session_state:
        st.session_state.active_player = ""

    col1, col2 = st.columns([3, 1])
    with col2:
        sport = st.selectbox("Sport", _SPORT_OPTIONS,
                             index=_SPORT_OPTIONS.index(st.session_state.prefill_sport)
                             if st.session_state.prefill_sport in _SPORT_OPTIONS else 0)

    picks = QUICK_PICKS.get(sport, [])
    qp_cols = st.columns(len(picks))
    for i, name in enumerate(picks):
        with qp_cols[i]:
            if st.button(name, key=f"qp_{name}", use_container_width=True):
                st.session_state.prefill_player = name
                st.session_state.prefill_sport = sport
                st.rerun()

    with col1:
        # Show the active player name if we have one, otherwise use prefill
        display_value = st.session_state.prefill_player or st.session_state.active_player
        _label = "Pokemon Name" if sport == "Pokemon" else "Player Name"
        _placeholder = "e.g. Charizard" if sport == "Pokemon" else "e.g. LeBron James"
        player_query = st.text_input(_label, placeholder=_placeholder,
                                     value=display_value)

    if st.session_state.search_history:
        st.caption("Recent searches:")
        hist_cols = st.columns(len(st.session_state.search_history))
        for i, (hname, hsport) in enumerate(st.session_state.search_history):
            with hist_cols[i]:
                if st.button(f"{hname} ({hsport})", key=f"hist_{i}", use_container_width=True):
                    st.session_state.prefill_player = hname
                    st.session_state.prefill_sport = hsport
                    st.rerun()

    if player_query:
        allowed, count, limit = check_usage_limit("searches")
        if not allowed:
            render_limit_warning("searches", count, limit)
            st.stop()

        st.session_state.prefill_player = ""
        st.session_state.active_player = player_query

        # ============================================================
        # POKEMON BRANCH
        # ============================================================
        if sport == "Pokemon":
            _render_pokemon_results(player_query, demo_mode)
        else:
            _render_sports_results(player_query, sport, demo_mode)

        # Contextual upsell for free users
        if not is_pro():
            render_contextual_upsell("player_search")


# ============================================================
# Pokemon-specific search & display
# ============================================================

def _render_pokemon_results(card_name: str, demo_mode: bool):
    """Search Pokemon TCG API and display card results with TCGPlayer pricing."""
    increment_and_check("searches")
    _push_search_history(card_name, "Pokemon")

    st.markdown(f"### {card_name}")

    with st.spinner(f"Searching Pokemon TCG for {card_name}..."):
        cards = search_pokemon_cards(card_name)

    if not cards:
        st.warning(f"No Pokemon cards found for '{card_name}'. Check the spelling.")
        return

    # Market summary
    summary = get_pokemon_market_summary(cards)
    render_market_summary(summary, demo_mode)

    gradient_divider()
    st.markdown(f"#### {len(cards)} Cards Found")

    # Card grid — 3 per row
    for row_start in range(0, len(cards), 3):
        row_cards = cards[row_start:row_start + 3]
        cols = st.columns(3)
        for i, card in enumerate(row_cards):
            with cols[i]:
                # Card image
                if card.get("image_small"):
                    st.image(card["image_small"], width=180)

                # Card info
                price = get_pokemon_market_price(card)
                price_str = f"${price:.2f}" if price > 0 else "N/A"
                st.markdown(f"**{card['name']}** — {card.get('set_name', '')}")
                st.caption(f"{card.get('rarity', 'Unknown')} | #{card.get('number', '?')} | {card.get('set_release_date', '')}")
                st.markdown(f"**TCGPlayer: {price_str}**")

                # Buy button
                if card.get("tcgplayer_url"):
                    st.markdown(tcgplayer_button(card["tcgplayer_url"]), unsafe_allow_html=True)

    # eBay graded section (secondary)
    gradient_divider()
    st.markdown("#### Graded Cards on eBay")
    st.caption("PSA/BGS-graded Pokemon cards from eBay")

    with st.spinner("Searching eBay for graded cards..."):
        graded_listings = search_ebay_cards(card_name, "Pokemon", "PSA 10", limit=20)
        graded_listings = flag_deals(graded_listings)

    if graded_listings:
        for listing in graded_listings:
            render_listing_row(listing)
    else:
        st.info("No graded listings found on eBay for this card.")

    # "Also Available On" — Pokemon (no Topps)
    gradient_divider()
    st.markdown("#### Also Available On")
    _pm1, _pm2, _pm3 = st.columns(3)
    with _pm1:
        st.markdown(whatnot_button(whatnot_search_affiliate_url(card_name, "Pokemon")), unsafe_allow_html=True)
    with _pm2:
        st.markdown(beckett_button(beckett_search_affiliate_url(card_name, "Pokemon")), unsafe_allow_html=True)
    with _pm3:
        st.markdown(drip_shop_button(drip_shop_search_affiliate_url(card_name, "Pokemon")), unsafe_allow_html=True)


# ============================================================
# Sports-specific search & display (original flow)
# ============================================================

def _render_sports_results(player_query: str, sport: str, demo_mode: bool):
    """Original sports card search flow — player stats + eBay listings."""
    with st.spinner(f"Searching for {player_query}..."):
        players = search_players(player_query, sport)

    if not players:
        st.warning(f"No results for '{player_query}' in {sport}. Check the spelling or try a different sport.")
        return

    increment_and_check("searches")
    if len(players) > 1:
        player_names = [
            f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
            for p in players
        ]
        selected_name = st.selectbox("Select player", player_names)
        selected_idx = player_names.index(selected_name)
        player = players[selected_idx]
    else:
        player = players[0]

    info = format_player_info(player, sport)
    player_id = info["id"]
    player_name = info["name"]
    _push_search_history(player_name, sport)

    st.markdown(f"### {player_name}")
    meta_cols = st.columns(4)
    meta_cols[0].metric("Team", info.get("team", "N/A"))
    if sport == "NBA":
        meta_cols[1].metric("Position", info.get("position", "N/A"))
        meta_cols[2].metric("Draft Year", info.get("draft_year", "N/A"))
        meta_cols[3].metric("Draft Pick", info.get("draft_number", "N/A"))

    st.markdown("#### Career Stats")
    with st.spinner("Loading stats..."):
        seasons = get_multi_season_stats(player_id, sport, num_seasons=6)

    if seasons:
        stat_keys = SPORTS.get(sport, {}).get("key_stats", [])
        stat_labels = SPORTS.get(sport, {}).get("stat_labels", {})

        rows = []
        for s in seasons:
            row = {"Season": s.get("season", "?")}
            for key in stat_keys:
                val = s.get(key)
                label = stat_labels.get(key, key)
                if val is not None:
                    row[label] = val
            if any(k != "Season" for k in row):
                rows.append(row)

        if rows:
            render_table(rows)
        else:
            st.info("No season data available for this player.")
    else:
        st.info("No stats returned — the player may not have recent season data.")

    gradient_divider()
    st.markdown("#### eBay Card Listings")

    _SORT_LABELS = {
        "price": "Price: Low to High",
        "bestMatch": "Best Match",
        "-price": "Price: High to Low",
        "newlyListed": "Newest",
        "endingSoonest": "Auction: Ending Soonest",
    }
    eb_filter1, eb_filter2 = st.columns(2)
    with eb_filter1:
        card_type_filter = st.selectbox("Card Type", get_card_type_options(), key="ebay_card_type")
    with eb_filter2:
        sort_option = st.selectbox("Sort", list(_SORT_LABELS.keys()), format_func=lambda k: _SORT_LABELS[k], key="ebay_sort")

    # --- Smart filter auto-linking ---
    _needs_rerun = False

    # Auction: Ending Soonest → auto-flip to Auction Only
    if sort_option == "endingSoonest" and st.session_state.get("ebay_buying_format") != "Auction Only":
        st.session_state["ebay_buying_format"] = "Auction Only"
        _needs_rerun = True

    # BIN Only → don't leave sort on Auction: Ending Soonest
    if st.session_state.get("ebay_buying_format") == "BIN Only" and sort_option == "endingSoonest":
        st.session_state["ebay_sort"] = "price"
        _needs_rerun = True

    # Graded Card Type → auto-flip Condition to Graded Only
    _GRADED_CARD_TYPES = {"PSA 10", "PSA 9.5", "PSA 9", "PSA 8", "BGS 10", "BGS 9.5", "BGS 9", "SGC 10", "SGC 9.5", "CGC 10"}
    if card_type_filter in _GRADED_CARD_TYPES and st.session_state.get("ebay_condition") != "Graded Only":
        st.session_state["ebay_condition"] = "Graded Only"
        _needs_rerun = True

    # Raw (Ungraded) Card Type → auto-flip Condition to Raw Only
    if card_type_filter == "Raw (Ungraded)" and st.session_state.get("ebay_condition") != "Raw Only":
        st.session_state["ebay_condition"] = "Raw Only"
        _needs_rerun = True

    if _needs_rerun:
        st.rerun()

    eb_filter3, eb_filter4, eb_filter5 = st.columns(3)
    with eb_filter3:
        buying_format_filter = st.selectbox("Buying Format", ["All", "BIN Only", "Auction Only"], key="ebay_buying_format")
    with eb_filter4:
        condition_filter = st.selectbox("Condition", ["All", "Raw Only", "Graded Only"], key="ebay_condition")
    with eb_filter5:
        budget = st.number_input("My Budget ($)", min_value=0.0, value=0.0, step=5.0, key="ebay_budget", help="0 = no limit")

    with st.spinner("Searching eBay..."):
        listings = search_ebay_cards(player_name, sport, card_type_filter, sort=sort_option)
        listings = flag_deals(listings)

    _GRADED_RE = re.compile(r"\b(PSA|BGS|SGC|CGC)\b", re.IGNORECASE)

    if listings:
        total_count = len(listings)
        filtered = listings

        if buying_format_filter == "BIN Only":
            filtered = [l for l in filtered if l.get("buying_format") == "BIN"]
        elif buying_format_filter == "Auction Only":
            filtered = [l for l in filtered if l.get("buying_format") == "Auction"]

        if condition_filter == "Graded Only":
            filtered = [l for l in filtered if _GRADED_RE.search(l.get("title", ""))]
        elif condition_filter == "Raw Only":
            filtered = [l for l in filtered if not _GRADED_RE.search(l.get("title", ""))]

        if budget > 0:
            filtered = [l for l in filtered if l.get("total", 0) <= budget]

        demo_tag = " (Sample)" if demo_mode else ""
        median_str = f"${listings[0].get('median', '?')}"
        if len(filtered) < total_count:
            st.success(f"Showing {len(filtered)} of {total_count} listings{demo_tag} — deals flagged below median ({median_str})")
        else:
            st.success(f"Found {total_count} listings{demo_tag} — deals flagged below median ({median_str})")
        for listing in filtered:
            render_listing_row(listing)
    else:
        st.info("No listings found for this player.")

    # "Also Available On" — Sports (includes Topps)
    gradient_divider()
    st.markdown("#### Also Available On")
    _sm1, _sm2, _sm3, _sm4 = st.columns(4)
    with _sm1:
        st.markdown(whatnot_button(whatnot_search_affiliate_url(player_name, sport)), unsafe_allow_html=True)
    with _sm2:
        st.markdown(topps_button(topps_search_affiliate_url(player_name, sport)), unsafe_allow_html=True)
    with _sm3:
        st.markdown(beckett_button(beckett_search_affiliate_url(player_name, sport)), unsafe_allow_html=True)
    with _sm4:
        st.markdown(drip_shop_button(drip_shop_search_affiliate_url(player_name, sport)), unsafe_allow_html=True)

    gradient_divider()
    st.markdown("#### Recent Sales")

    with st.spinner("Fetching sold/completed listings..."):
        sold_listings = search_ebay_sold(player_name, sport, card_type_filter, limit=50)

    if sold_listings:
        summary = get_market_summary(listings, sold_listings)
        render_market_summary(summary, demo_mode)

        _has_active = listings and summary.get("avg_active", 0) > 0
        cmp1, cmp2 = st.columns(2)
        with cmp1:
            st.markdown("**Active Ask (avg)**")
            if _has_active:
                st.markdown(f"### ${summary['avg_active']:.2f}")
            else:
                st.markdown("### —")
                st.caption("No active listings match this player right now.")
        with cmp2:
            st.markdown("**Sold Price (avg)**")
            st.markdown(f"### ${summary['avg_sold']:.2f}")

        if _has_active:
            spread = summary["active_vs_sold_pct"]
            if spread > 0:
                st.caption(f"Active listings are **{spread:.1f}% above** recent sold prices")
            elif spread < 0:
                st.caption(f"Active listings are **{abs(spread):.1f}% below** recent sold prices")
            else:
                st.caption("Active and sold prices are aligned")

        st.markdown("##### Price History")
        chart_range = st.radio("Time Range", ["7d", "30d", "90d", "1Y"], horizontal=True, key="price_chart_range")

        ps_history = get_price_history(player_name, sport, card_type_filter)
        if ps_history:
            ps_fig = build_price_chart(ps_history, player_name, chart_range)
            st.plotly_chart(ps_fig, use_container_width=True)
        else:
            st.info("No price history data available.")

        with st.expander("PSA Population Data"):
            psa_data = lookup_psa_population(player_name)
            st.markdown(f'<span class="psa-badge">Total Pop: {psa_data["total_pop"]:,}</span> '
                        f'<span class="psa-gem">Gem Rate: {psa_data["gem_rate"]:.1f}%</span>',
                        unsafe_allow_html=True)
            psa_cols = st.columns(len(psa_data["grade_distribution"]))
            for i, (grade, count) in enumerate(sorted(psa_data["grade_distribution"].items(), key=lambda x: -int(x[0]))):
                with psa_cols[i]:
                    st.metric(f"PSA {grade}", f"{count:,}")
            if psa_data.get("source") == "demo":
                st.caption("Sample data — connect PSA API for live population reports")

        demo_tag = " (Sample)" if demo_mode else ""
        st.markdown(f"**{len(sold_listings)} sold listings{demo_tag}:**")
        for sl in sold_listings:
            render_sold_row(sl)
    else:
        st.info("No sold data available for this player.")


