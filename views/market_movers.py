"""Market Movers page."""

import streamlit as st

from modules.ui_helpers import gradient_divider, render_table, ebay_button
from modules.market_movers import compute_market_movers
from modules.affiliates import ebay_search_affiliate_url
from data.watchlists import NBA_BREAKOUT_WATCHLIST, NFL_BREAKOUT_WATCHLIST, MLB_BREAKOUT_WATCHLIST, LEGENDS_WATCHLIST
from tiers import can_access, render_upgrade_prompt, render_disclaimer


def render():
    st.title("📈 Market Movers")
    st.caption("Biggest weekly price gainers and losers across all sports")
    render_disclaimer(compact=True)

    if not can_access("market_movers"):
        render_upgrade_prompt("Market Movers", "See which cards are gaining and losing value this week.")
        st.stop()

    mm_sport_filter = st.selectbox("Filter by Sport", ["All", "NBA", "NFL", "MLB"], key="mm_sport")

    all_players = []
    for sport_key, wl in [("NBA", NBA_BREAKOUT_WATCHLIST), ("NFL", NFL_BREAKOUT_WATCHLIST), ("MLB", MLB_BREAKOUT_WATCHLIST)]:
        for p in wl:
            all_players.append({"name": p["name"], "sport": sport_key})
    for legend in LEGENDS_WATCHLIST:
        all_players.append({"name": legend["name"], "sport": legend.get("sport", "NBA")})

    if mm_sport_filter != "All":
        all_players = [p for p in all_players if p["sport"] == mm_sport_filter]

    with st.spinner("Computing market movers..."):
        movers = compute_market_movers(all_players, max_players=10)

    gradient_divider()

    mc_left, mc_right = st.columns(2)

    with mc_left:
        st.markdown("### Top Gainers")
        if movers["gainers"]:
            for i, g in enumerate(movers["gainers"], 1):
                gc1, gc2, gc3, gc4 = st.columns([2.5, 1.2, 1.2, 1.2])
                with gc1:
                    st.write(f"**{i}. {g['name']}** ({g['sport']})")
                with gc2:
                    st.write(f"${g['current_price']:.2f}")
                with gc3:
                    st.markdown(f'<span class="mover-gain">+{g["change_pct"]:.1f}%</span>', unsafe_allow_html=True)
                with gc4:
                    buy_url = ebay_search_affiliate_url(g["name"], g["sport"])
                    st.markdown(f'<a href="{buy_url}" target="_blank" class="ebay-btn">Buy</a>', unsafe_allow_html=True)
        else:
            st.info("No gainers this week")

    with mc_right:
        st.markdown("### Top Losers")
        st.caption("Buy the dip? Check the fundamentals first.")
        if movers["losers"]:
            for i, l in enumerate(movers["losers"], 1):
                lc1, lc2, lc3, lc4 = st.columns([2.5, 1.2, 1.2, 1.2])
                with lc1:
                    st.write(f"**{i}. {l['name']}** ({l['sport']})")
                with lc2:
                    st.write(f"${l['current_price']:.2f}")
                with lc3:
                    st.markdown(f'<span class="mover-loss">{l["change_pct"]:.1f}%</span>', unsafe_allow_html=True)
                with lc4:
                    buy_url = ebay_search_affiliate_url(l["name"], l["sport"])
                    st.markdown(f'<a href="{buy_url}" target="_blank" class="ebay-btn">Buy</a>', unsafe_allow_html=True)
        else:
            st.info("No losers this week")

    with st.expander("Full Movers Table"):
        all_movers = movers["gainers"] + movers["losers"]
        all_movers.sort(key=lambda x: x["change_pct"], reverse=True)
        if all_movers:
            rows = []
            for m in all_movers:
                rows.append({
                    "Player": m["name"],
                    "Sport": m["sport"],
                    "Current": f"${m['current_price']:.2f}",
                    "Previous": f"${m['prev_price']:.2f}",
                    "Change": f"{m['change_pct']:+.1f}%",
                })
            render_table(rows)


render()
