"""League Leaders — real-time stat leaders by sport with Buy Cards links."""

import streamlit as st

from modules.league_leaders import (
    get_leaders,
    is_nba_offseason, get_nba_display_season,
    is_mlb_offseason, get_mlb_display_season,
    is_nfl_offseason, get_nfl_display_season,
    SPORT_CATEGORIES,
)
from modules.affiliates import ebay_search_affiliate_url
from modules.ui_helpers import gradient_divider
from tiers import is_pro, render_teaser_gate


def render():
    st.title("League Leaders")
    st.caption("Top performers across MLB, NBA, and NFL — every row is a card to chase")

    # --- Sport + Category selectors ---
    col_sport, col_cat = st.columns([1, 2])
    with col_sport:
        sport = st.radio("Sport", ["MLB", "NBA", "NFL"], horizontal=True, key="ll_sport")
    with col_cat:
        categories = list(SPORT_CATEGORIES.get(sport, {}).keys())
        default_idx = 0
        category = st.selectbox("Stat Category", categories, index=default_idx, key="ll_cat")

    # --- Offseason banners ---
    if sport == "NBA" and is_nba_offseason():
        _, nba_label = get_nba_display_season()
        st.info(f"NBA offseason — showing **{nba_label}** final leaders.")
    elif sport == "MLB" and is_mlb_offseason():
        _, mlb_label = get_mlb_display_season()
        st.info(f"MLB offseason — showing **{mlb_label}** final leaders.")
    elif sport == "NFL" and is_nfl_offseason():
        _, nfl_label = get_nfl_display_season()
        st.info(f"NFL offseason — showing **{nfl_label}** final leaders.")

    gradient_divider()

    # --- Tier limits ---
    _is_pro = is_pro()
    row_limit = 20 if _is_pro else 5

    # --- Fetch data ---
    with st.spinner("Loading leaders..."):
        leaders = get_leaders(sport, category, limit=20)

    if not leaders:
        st.warning(f"No {sport} leader data available right now. Try again later.")
        return

    # --- Metrics row ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Sport", sport)
    m2.metric("Category", category)
    m3.metric("Players Shown", f"{min(len(leaders), row_limit)} of {len(leaders)}")

    gradient_divider()

    # --- Leader table ---
    st.markdown("### Leaderboard")

    # Header row
    h1, h2, h3, h4, h5 = st.columns([0.5, 2.5, 1.5, 1.5, 1.5])
    h1.markdown("**#**")
    h2.markdown("**Player**")
    h3.markdown("**Team**")
    h4.markdown("**Value**")
    h5.markdown("**Buy Cards**")

    # Visible rows
    visible = leaders[:row_limit]
    for row in visible:
        c1, c2, c3, c4, c5 = st.columns([0.5, 2.5, 1.5, 1.5, 1.5])
        c1.write(row["rank"])
        c2.write(row["player"])
        c3.write(row["team"])
        c4.write(row["value"])
        buy_url = ebay_search_affiliate_url(row["player"], sport)
        c5.markdown(
            f'<a href="{buy_url}" target="_blank" class="ebay-btn">Buy Cards</a>',
            unsafe_allow_html=True,
        )

    # --- Teaser blur for free users ---
    if not _is_pro and len(leaders) > row_limit:
        st.markdown('<div class="teaser-blur">', unsafe_allow_html=True)
        for row in leaders[row_limit:row_limit + 5]:
            t1, t2, t3, t4, t5 = st.columns([0.5, 2.5, 1.5, 1.5, 1.5])
            t1.write(row["rank"])
            t2.write(row["player"])
            t3.write(row["team"])
            t4.write(row["value"])
            t5.write("---")
        st.markdown('</div>', unsafe_allow_html=True)
        render_teaser_gate("League Leaders", "Unlock the full top 20 with Pro")
