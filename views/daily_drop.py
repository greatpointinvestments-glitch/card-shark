"""Daily Drop Challenge — vote BUY/PASS, build streaks, climb the leaderboard."""

import streamlit as st

from modules.daily_drop import (
    get_daily_card, cast_vote, get_user_vote, compute_user_streak,
    get_community_split, get_leaderboard, get_recent_drops,
)
from modules.ui_helpers import card_thumbnail_lg, gradient_divider, ebay_button
from modules.affiliates import ebay_search_affiliate_url
from tiers import is_pro, render_upgrade_banner


def render():
    st.title("Daily Drop Challenge")
    st.caption("Every day we pick one card. You vote BUY or PASS. After 7 days, we check the price. Build your streak.")

    with st.expander("How it works"):
        st.markdown(
            "1. **We pick one undervalued card every day** using our Flip Finder algorithm\n"
            "2. **You vote BUY or PASS** — do you think this card goes up in 7 days?\n"
            "3. **We check the price a week later** and score your call\n"
            "4. **Correct picks build your streak** — climb the leaderboard and see how you stack up\n\n"
            "No real money involved. Just test your card market instincts."
        )

    username = st.session_state.get("username")
    today_str = None

    # --- Today's Drop ---
    with st.spinner("Loading today's drop..."):
        card = get_daily_card()

    if card:
        today_str = card["drop_date"]
        st.markdown("### Today's Drop")

        dl, dr = st.columns([1, 3])
        with dl:
            st.markdown(card_thumbnail_lg(card.get("image_url", "")), unsafe_allow_html=True)
        with dr:
            listing = card.get("listing", {})
            st.markdown(f"**{card['player_name']}** ({card['sport']})")
            st.markdown(f"*{listing.get('title', '')[:80]}*")

            m1, m2, m3 = st.columns(3)
            m1.metric("Drop Price", f"${card['drop_price']:.2f}")
            summary = card.get("summary", {})
            if summary:
                m2.metric("Avg Sold", f"${summary.get('avg_sold', 0):.2f}")
                m3.metric("Sold Volume", summary.get("sold_volume", 0))

            if summary:
                st.caption(card.get("why", ""))

            # eBay link
            ebay_url = listing.get("url", "")
            if ebay_url:
                st.markdown(ebay_button(ebay_url), unsafe_allow_html=True)
            else:
                search_url = ebay_search_affiliate_url(card["player_name"], card["sport"])
                st.markdown(
                    f'<a href="{search_url}" target="_blank" class="ebay-btn">Search on eBay</a>',
                    unsafe_allow_html=True,
                )

        gradient_divider()

        # --- Vote Buttons ---
        if username and today_str:
            existing_vote = get_user_vote(username, today_str)
            if existing_vote:
                split = get_community_split(today_str)
                st.markdown(
                    f'<div style="text-align:center;padding:12px;">'
                    f'<span style="font-size:1.3em;font-weight:bold;">You voted: '
                    f'<span class="{"vote-buy" if existing_vote == "BUY" else "vote-pass"}">'
                    f'{existing_vote}</span></span>'
                    f'<br><span style="color:#9ca3af;">'
                    f'{split["buy_pct"]}% say BUY &bull; {split["pass_pct"]}% say PASS '
                    f'({split["total_votes"]} votes)</span></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown("### What's your call?")
                v1, v2 = st.columns(2)
                with v1:
                    if st.button("BUY", key="vote_buy", use_container_width=True, type="primary"):
                        cast_vote(username, today_str, "BUY")
                        st.rerun()
                with v2:
                    if st.button("PASS", key="vote_pass", use_container_width=True):
                        cast_vote(username, today_str, "PASS")
                        st.rerun()

            # Streak display
            streak = compute_user_streak(username)
            gradient_divider()

            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Current Streak", f"{streak['current_streak']}")
            s2.metric("Best Streak", f"{streak['best_streak']}")
            s3.metric("Accuracy", f"{streak['accuracy_pct']}%")
            s4.metric("Total Votes", streak["total_votes"])

            if streak["current_streak"] >= 3:
                st.markdown(
                    f'<div class="streak-badge" style="text-align:center;font-size:1.2em;">'
                    f'{streak["current_streak"]} streak!</div>',
                    unsafe_allow_html=True,
                )
        elif not username:
            st.info("Log in to vote and build your streak!")

    else:
        st.warning("No drop available today — check back later!")

    gradient_divider()

    # --- Recent Drops ---
    st.markdown("### Recent Drops")
    drops = get_recent_drops(days=7 if not is_pro() else 30)

    if drops:
        for drop in drops:
            resolved = drop.get("correct_vote") is not None
            r1, r2, r3, r4 = st.columns([2, 1, 1, 1])
            with r1:
                st.write(f"**{drop.get('player_name', '?')}** ({drop.get('sport', '')})")
                st.caption(drop["date"])
            with r2:
                st.write(f"Drop: ${drop.get('drop_price', 0):.2f}")
            with r3:
                if resolved:
                    result_price = drop.get("result_price", 0)
                    change = drop.get("price_change_pct", 0)
                    color = "#22c55e" if change > 0 else "#ef4444" if change < 0 else "#9ca3af"
                    st.markdown(
                        f"Result: ${result_price:.2f} "
                        f'<span style="color:{color}">({change:+.1f}%)</span>',
                        unsafe_allow_html=True,
                    )
                    st.caption(f"Correct: {drop['correct_vote']}")
                else:
                    st.caption("Pending (7 days)")
            with r4:
                buy_v = drop.get("total_buy_votes", 0)
                pass_v = drop.get("total_pass_votes", 0)
                total_v = buy_v + pass_v
                if total_v > 0:
                    st.caption(f"BUY {round(buy_v/total_v*100)}% / PASS {round(pass_v/total_v*100)}%")
    else:
        st.info("No recent drops yet. Come back tomorrow!")

    gradient_divider()

    # --- Leaderboard ---
    st.markdown("### Leaderboard")
    lb_limit = 10 if not is_pro() else 20
    leaderboard = get_leaderboard(limit=lb_limit)

    if leaderboard:
        for i, entry in enumerate(leaderboard):
            rank = i + 1
            medal = {1: "", 2: "", 3: ""}.get(rank, "")
            l1, l2, l3, l4 = st.columns([0.5, 2, 1, 1])
            with l1:
                st.write(f"{medal}{rank}")
            with l2:
                st.write(f"**{entry['username']}**")
            with l3:
                st.write(f"Streak: {entry['current_streak']}")
            with l4:
                st.write(f"{entry['accuracy_pct']}% accuracy")
    else:
        st.info("No leaderboard data yet. Be the first to vote!")

    if not is_pro():
        render_upgrade_banner("Daily Drop", "full leaderboard + all-time history")
