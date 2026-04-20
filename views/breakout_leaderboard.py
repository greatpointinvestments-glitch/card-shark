"""Breakout Leaderboard page."""

import streamlit as st

from modules.ui_helpers import (
    signal_badge, score_progress_bar, gradient_divider,
    render_listing_compact, render_table, market_signal_badge,
)
from modules.breakout_engine import build_leaderboard
from modules.trend_indicators import get_leaderboard_trends, trend_indicator
from modules.player_stats import search_players, get_multi_season_stats, format_player_info
from modules.ebay_search import search_ebay_cards, search_ebay_sold, flag_deals, get_market_summary
from modules.card_types import get_card_type_options
from config.settings import SPORTS
from tiers import is_pro
from data.watchlists import NBA_BREAKOUT_WATCHLIST, NFL_BREAKOUT_WATCHLIST, MLB_BREAKOUT_WATCHLIST

BREAKOUT_WATCHLISTS = {
    "NBA": NBA_BREAKOUT_WATCHLIST,
    "NFL": NFL_BREAKOUT_WATCHLIST,
    "MLB": MLB_BREAKOUT_WATCHLIST,
}


def render(demo_mode: bool = False):
    st.title("🚀 Breakout Leaderboard")
    st.caption("Find tomorrow's stars before everyone else")

    breakout_sport = st.selectbox("Sport", ["NBA", "NFL", "MLB"], key="breakout_sport")
    breakout_watchlist = BREAKOUT_WATCHLISTS[breakout_sport]

    leaderboard = build_leaderboard(breakout_watchlist, breakout_sport)

    if not leaderboard:
        st.error("Could not build leaderboard.")
        return

    buy_count = sum(1 for p in leaderboard if p["signal"] == "BUY")
    watch_count = sum(1 for p in leaderboard if p["signal"] == "WATCH")
    hold_count = sum(1 for p in leaderboard if p["signal"] == "HOLD")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Players", len(leaderboard))
    m2.metric("BUY Signals", buy_count)
    m3.metric("WATCH Signals", watch_count)
    m4.metric("HOLD Signals", hold_count)

    gradient_divider()

    filter_signal = st.multiselect("Filter by Signal", ["BUY", "WATCH", "HOLD"], default=["BUY", "WATCH", "HOLD"])
    filtered = [p for p in leaderboard if p["signal"] in filter_signal]

    if not is_pro() and len(filtered) > 10:
        full_count = len(filtered)
        _teaser_rows = filtered[10:12]  # 2 blurred teaser rows
        filtered = filtered[:10]
        _show_leaderboard_upsell = True
    else:
        _show_leaderboard_upsell = False
        _teaser_rows = []
        full_count = 0

    player_names_tuple = tuple(p["name"] for p in leaderboard)
    with st.spinner("Loading market trends..."):
        trends = get_leaderboard_trends(player_names_tuple, breakout_sport)

    hdr = st.columns([0.5, 2.5, 1.5, 1, 1, 1, 1.5, 1.5])
    hdr[0].caption("Rank")
    hdr[1].caption("Player")
    hdr[2].caption("Team")
    hdr[3].caption("Age")
    hdr[4].caption("Draft")
    hdr[5].caption("Score")
    hdr[6].caption("Signal")
    hdr[7].caption("Price Trend (90d)")

    for player in filtered:
        cols = st.columns([0.5, 2.5, 1.5, 1, 1, 1, 1.5, 1.5])
        with cols[0]:
            st.write(f"**#{player['rank']}**")
        with cols[1]:
            st.write(f"**{player['name']}**")
        with cols[2]:
            st.write(player["team"])
        with cols[3]:
            st.write(f"Age {player['age']}")
        with cols[4]:
            pick = player.get('draft_pick')
            st.write(f"Pick #{pick}" if pick is not None else "Intl")
        with cols[5]:
            st.write(f"**{player['score']}**")
            st.markdown(score_progress_bar(player['score']), unsafe_allow_html=True)
        with cols[6]:
            st.markdown(signal_badge(player["signal"]), unsafe_allow_html=True)
        with cols[7]:
            t_data = trends.get(player["name"])
            if t_data:
                st.markdown(trend_indicator(t_data["trend"], t_data["delta"]), unsafe_allow_html=True)
            else:
                st.markdown('<span style="color:#6b7280">—</span>', unsafe_allow_html=True)

    # Blurred teaser rows + upgrade CTA
    if _show_leaderboard_upsell:
        if _teaser_rows:
            st.markdown('<div class="teaser-blur">', unsafe_allow_html=True)
            for player in _teaser_rows:
                cols = st.columns([0.5, 2.5, 1.5, 1, 1, 1, 1.5, 1.5])
                with cols[0]:
                    st.write(f"**#{player['rank']}**")
                with cols[1]:
                    st.write(f"**{player['name']}**")
                with cols[2]:
                    st.write(player["team"])
                with cols[3]:
                    st.write(f"Age {player['age']}")
                with cols[4]:
                    pick = player.get('draft_pick')
                    st.write(f"Pick #{pick}" if pick is not None else "Intl")
                with cols[5]:
                    st.write(f"**{player['score']}**")
                with cols[6]:
                    st.markdown(signal_badge(player["signal"]), unsafe_allow_html=True)
                with cols[7]:
                    st.markdown('<span style="color:#6b7280">—</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        from tiers import render_teaser_gate
        render_teaser_gate("Breakout Leaderboard", f"{full_count - 10} more players hidden — see them all with Pro")

    with st.expander("How Breakout Signals Work"):
        st.markdown("""
**BUY** = high breakout score (stats improving + young + high draft pick + favorable market conditions). A negative price trend alongside BUY means *buy the dip* — the player's fundamentals are strong but card prices recently dipped, which creates an entry window.

**WATCH** = solid score but not strong enough across all factors to push into BUY. Keep an eye on upcoming games.

**HOLD** = either older player, declining stats, or market already priced in. Not a sell signal — just means don't add more right now.

**Price Trend** = 90-day card price change. Compares recent sold prices to older sold prices.

**Score** (0-100) blends: stat trajectory (30%), usage/role (20%), age (15%), draft position (15%), market pricing (20%).
        """)

    gradient_divider()

    # Deep dive
    st.markdown("### Deep Dive")
    player_names = [p["name"] for p in leaderboard]
    selected = st.selectbox("Select a player for detailed analysis", player_names)

    if selected:
        st.markdown(f"#### {selected}")
        player_data = next(p for p in breakout_watchlist if p["name"] == selected)

        info_cols = st.columns(4)
        info_cols[0].metric("Team", player_data["team"])
        info_cols[1].metric("Age", player_data["age"])
        info_cols[2].metric("Draft Pick", f"#{player_data.get('draft_pick', 'N/A')}")
        info_cols[3].metric("Seasons", player_data.get("seasons", "?"))

        with st.spinner("Fetching live stats..."):
            api_players = search_players(selected, breakout_sport)

        if api_players:
            p = api_players[0]
            info = format_player_info(p, breakout_sport)
            stats = get_multi_season_stats(info["id"], breakout_sport, num_seasons=3)

            if stats:
                st.markdown("**Season Stats:**")
                stat_labels = SPORTS.get(breakout_sport, {}).get("stat_labels", {})
                rows = []
                for s in stats:
                    row = {"Season": s.get("season", "?")}
                    for key in SPORTS.get(breakout_sport, {}).get("key_stats", []):
                        val = s.get(key)
                        if val is not None:
                            row[stat_labels.get(key, key)] = val
                    rows.append(row)
                if rows:
                    render_table(rows)

        with st.spinner("Checking eBay market..."):
            listings = search_ebay_cards(selected, breakout_sport, "Rookie", limit=20)
            listings = flag_deals(listings)

        if listings:
            prices = [l["total"] for l in listings if l["total"] > 0
                      and not (l.get("buying_format") == "Auction" and l.get("bid_count", 0) == 0)]
            if prices:
                demo_tag = " (Sample)" if demo_mode else ""
                st.markdown(f"**eBay Market{demo_tag}:** {len(listings)} rookie card listings | Median: ${sorted(prices)[len(prices)//2]:.2f}")

                deal_count = sum(1 for l in listings if l.get("is_deal"))
                if deal_count:
                    st.success(f"Found {deal_count} deals below median!")

                for listing in listings[:10]:
                    render_listing_compact(listing)

            with st.spinner("Fetching sold data..."):
                sold = search_ebay_sold(selected, breakout_sport, "Rookie", limit=20)
            if sold:
                summary = get_market_summary(listings, sold)
                demo_tag = " (Sample)" if demo_mode else ""
                st.markdown(f"**Sold Market{demo_tag}:**")
                sm1, sm2, sm3 = st.columns(3)
                sm1.metric("Avg Sold Price", f"${summary['avg_sold']:.2f}")
                sm2.metric("90d Volume", f"{summary['sold_volume']} sales")
                sm3.metric("Price Trend", summary["price_trend"], f"{summary['trend_delta']:+.1f}%")
        else:
            st.info("No listings found for this player.")


render(demo_mode=False)
