"""Player Comparison page."""

import streamlit as st

from modules.ui_helpers import gradient_divider, signal_badge, market_signal_badge, score_progress_bar
from modules.player_compare import fetch_player_comparison_data, generate_verdict
from modules.affiliates import ebay_search_affiliate_url
from config.settings import SPORTS
from tiers import can_access, render_upgrade_prompt


def render():
    st.title("⚔️ Player Comparison")
    st.caption("Who's the better card investment? Side-by-side stats, market data, and a verdict.")

    if not can_access("player_comparison"):
        render_upgrade_prompt("Player Comparison", "Compare two players side-by-side — stats, card values, and an investment verdict.")
        st.stop()

    cmp_left, cmp_div, cmp_right = st.columns([5, 0.5, 5])

    with cmp_left:
        st.markdown("### Player A")
        pa_name = st.text_input("Player Name", placeholder="e.g. Victor Wembanyama", key="cmp_a_name")
        pa_sport = st.selectbox("Sport", ["NBA", "NFL", "MLB", "Pokemon"], key="cmp_a_sport")
    with cmp_div:
        st.markdown("<div style='text-align:center; font-size:2em; padding-top:80px'>vs</div>", unsafe_allow_html=True)
    with cmp_right:
        st.markdown("### Player B")
        pb_name = st.text_input("Player Name", placeholder="e.g. Chet Holmgren", key="cmp_b_name")
        pb_sport = st.selectbox("Sport", ["NBA", "NFL", "MLB", "Pokemon"], key="cmp_b_sport")

    if pa_name and pb_name:
        if st.button("Compare", type="primary", use_container_width=True):
            with st.spinner(f"Fetching data for {pa_name} and {pb_name}..."):
                data_a = fetch_player_comparison_data(pa_name, pa_sport)
                data_b = fetch_player_comparison_data(pb_name, pb_sport)

            if not data_a:
                st.error(f"Could not find {pa_name} in {pa_sport}.")
            elif not data_b:
                st.error(f"Could not find {pb_name} in {pb_sport}.")
            else:
                gradient_divider()

                st.markdown("#### Stats (Most Recent Season)")
                stat_left, stat_right = st.columns(2)
                for col, data, name, sport in [(stat_left, data_a, pa_name, pa_sport), (stat_right, data_b, pb_name, pb_sport)]:
                    with col:
                        st.markdown(f"**{name}**")
                        info = data["info"]
                        st.write(f"Team: {info.get('team', 'N/A')}")
                        if data["stats"]:
                            latest = data["stats"][0]
                            stat_keys = SPORTS.get(sport, {}).get("key_stats", [])
                            stat_labels = SPORTS.get(sport, {}).get("stat_labels", {})
                            for key in stat_keys[:6]:
                                val = latest.get(key)
                                if val is not None:
                                    st.write(f"{stat_labels.get(key, key)}: **{val}**")
                        else:
                            st.info("No stats available")

                gradient_divider()

                st.markdown("#### Market Data")
                mkt_left, mkt_right = st.columns(2)
                for col, data, name in [(mkt_left, data_a, pa_name), (mkt_right, data_b, pb_name)]:
                    with col:
                        st.markdown(f"**{name}**")
                        if data["market_summary"]:
                            ms = data["market_summary"]
                            st.metric("Avg Sold", f"${ms['avg_sold']:.2f}")
                            st.metric("Avg Active", f"${ms['avg_active']:.2f}")
                            st.metric("90d Volume", f"{ms['sold_volume']} sales")
                            st.write(f"Trend: {ms['price_trend']} ({ms['trend_delta']:+.1f}%)")
                            st.markdown(market_signal_badge(ms["market_signal"]), unsafe_allow_html=True)
                        else:
                            st.info("No market data available")

                gradient_divider()

                st.markdown("#### Breakout Score")
                bs_left, bs_right = st.columns(2)
                for col, data, name in [(bs_left, data_a, pa_name), (bs_right, data_b, pb_name)]:
                    with col:
                        score = data["breakout"].get("score", 0)
                        signal = data["breakout"].get("signal", "HOLD")
                        st.markdown(f"**{name}**: {score}/100")
                        st.markdown(score_progress_bar(score), unsafe_allow_html=True)
                        st.markdown(signal_badge(signal), unsafe_allow_html=True)

                gradient_divider()
                verdict = generate_verdict(data_a, data_b, pa_name, pb_name)
                st.markdown("#### Verdict")
                st.markdown(f"> {verdict}")

                # Affiliate buy links — capitalize on the decision moment
                gradient_divider()
                shop_left, shop_right = st.columns(2)
                with shop_left:
                    url_a = ebay_search_affiliate_url(pa_name, pa_sport, "Rookie")
                    st.markdown(
                        f'<a href="{url_a}" target="_blank" class="ebay-btn" '
                        f'style="display:block;text-align:center;padding:10px;">Shop {pa_name} Cards on eBay</a>',
                        unsafe_allow_html=True,
                    )
                with shop_right:
                    url_b = ebay_search_affiliate_url(pb_name, pb_sport, "Rookie")
                    st.markdown(
                        f'<a href="{url_b}" target="_blank" class="ebay-btn" '
                        f'style="display:block;text-align:center;padding:10px;">Shop {pb_name} Cards on eBay</a>',
                        unsafe_allow_html=True,
                    )


render()
