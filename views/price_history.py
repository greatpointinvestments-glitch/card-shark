"""Price History page."""

import streamlit as st

from modules.card_types import get_card_type_options
from modules.price_history import get_price_history, build_price_chart, compute_price_stats
from modules.affiliates import ebay_search_affiliate_url
from modules.ui_helpers import render_fuzzy_suggestions
from tiers import render_disclaimer, is_pro, render_teaser_gate


def render():
    st.title("📊 Price History")
    st.caption("Interactive charts — track any card's price over time")
    render_disclaimer(compact=True)

    # Pick up fuzzy suggestion before widget renders
    _fz_pick = st.session_state.pop("_ph_fuzzy_pick", "")
    if _fz_pick:
        st.session_state["ph_player"] = _fz_pick

    ph_c1, ph_c2, ph_c3 = st.columns(3)
    with ph_c1:
        ph_player = st.text_input("Player Name", placeholder="e.g. Victor Wembanyama", key="ph_player")
    with ph_c2:
        ph_sport = st.selectbox("Sport", ["NBA", "NFL", "MLB", "Pokemon"], key="ph_sport")
    with ph_c3:
        ph_type = st.selectbox("Card Type", get_card_type_options(), key="ph_type")

    # Optional filters to narrow to a specific card
    ph_f1, ph_f2 = st.columns(2)
    with ph_f1:
        ph_year = st.text_input("Year (optional)", placeholder="e.g. 2023-24", key="ph_year")
    with ph_f2:
        ph_set = st.text_input("Set / Parallel (optional)", placeholder="e.g. Prizm Silver", key="ph_set")

    # Fuzzy search suggestions — if suggestions appear, don't run the search yet
    _has_suggestions = False
    if ph_player:
        _sug = render_fuzzy_suggestions(ph_player, ph_sport, key_prefix="ph_fz")
        if _sug:
            st.session_state["_ph_fuzzy_pick"] = _sug
            st.rerun()
        # Check if suggestions were rendered (player not an exact match)
        from modules.fuzzy_search import has_exact_match
        _has_suggestions = not has_exact_match(ph_player, ph_sport)

    if ph_player and not _has_suggestions:
        _free_ranges = ["7d", "30d"]
        _pro_ranges = ["90d", "1Y"]
        _all_ranges = _free_ranges + _pro_ranges

        if is_pro():
            ph_range = st.radio("Time Range", _all_ranges, horizontal=True, key="ph_range", index=3)
            _gated = False
        else:
            ph_range = st.radio("Time Range", _all_ranges, horizontal=True, key="ph_range", index=1,
                                format_func=lambda x: f"{x} (Pro)" if x in _pro_ranges else x)
            _gated = ph_range in _pro_ranges

        with st.spinner("Loading price history..."):
            history = get_price_history(
                ph_player, ph_sport, ph_type,
                year=ph_year.strip(), set_name=ph_set.strip(),
            )

        if history:
            if _gated:
                # Show 30d chart as teaser, then gate
                fig = build_price_chart(history, ph_player, "30d")
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('<div class="teaser-blur">', unsafe_allow_html=True)
                st.markdown("*Extended price history data loads here...*")
                st.markdown('</div>', unsafe_allow_html=True)
                render_teaser_gate("Price History", f"Unlock {ph_range} price history with Pro")
            else:
                fig = build_price_chart(history, ph_player, ph_range)
                st.plotly_chart(fig, use_container_width=True)

                range_days = {"7d": 7, "30d": 30, "90d": 90, "1Y": 365}[ph_range]
                stats = compute_price_stats(history, range_days)
                range_label = {"7d": "7-Day", "30d": "30-Day", "90d": "90-Day", "1Y": "52-Week"}[ph_range]
                ps1, ps2, ps3, ps4 = st.columns(4)
                ps1.metric("Current", f"${stats['current']:.2f}")
                ps2.metric(f"{range_label} High", f"${stats['high_52w']:.2f}")
                ps3.metric(f"{range_label} Low", f"${stats['low_52w']:.2f}")
                change_color = "normal" if stats["change_pct"] >= 0 else "inverse"
                ps4.metric("Change", f"{stats['change_pct']:+.1f}%", delta_color=change_color)

            # Affiliate link to current listings
            buy_url = ebay_search_affiliate_url(ph_player, ph_sport, ph_type)
            st.markdown(
                f'<a href="{buy_url}" target="_blank" class="ebay-btn" '
                f'style="display:inline-block;margin-top:10px;padding:8px 20px;">'
                f'See Current Listings on eBay</a>',
                unsafe_allow_html=True,
            )
        else:
            st.info("No price history available for this player.")


