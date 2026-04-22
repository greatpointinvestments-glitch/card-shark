"""Collection Battles — head-to-head collection comparisons."""

import streamlit as st

from modules.battles import (
    generate_battle_code, accept_battle, get_user_battles,
    render_battle_card_html,
)
from modules.ui_helpers import gradient_divider
from modules.affiliates import ebay_search_affiliate_url
from tiers import is_pro, render_upgrade_banner, increment_and_check


def render():
    st.title("Collection Battles")
    st.caption("Challenge a friend. Compare collections across 5 categories. Winner takes bragging rights.")

    username = st.session_state.get("username")
    if not username:
        st.warning("Log in to battle! You need a collection to compete.")
        return

    _user_is_pro = is_pro()

    with st.expander("How Battles Work"):
        st.markdown("""
**Collection Battles compare two users across 5 categories, each worth 20 points (100 total):**

1. **Total Value** — Sum of all purchase prices in your collection. Bigger portfolio wins.
2. **Best Card** — Your single most valuable card. Quality over quantity.
3. **Biggest Gainer** — Card with the highest P&L % vs. current market price. Smart picks win.
4. **Diversification** — How spread out your collection is across sports and card types. Balanced beats one-dimensional.
5. **Collection Size** — Total number of cards. Collectors who keep buying win this one.

Each category: **Winner gets 20 pts**, loser gets 0. Ties split 10-10. Highest total wins.
        """)

    # --- Create or Join ---
    st.markdown("### Start a Battle")
    b1, b2 = st.columns(2)

    with b1:
        st.markdown(
            '<div style="background:linear-gradient(135deg,#1e3a5f,#1e40af);'
            'border-radius:12px;padding:20px;text-align:center;">'
            '<h4>Challenge a Friend</h4>'
            '<p style="color:#9ca3af;">Generate a code and share it</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        if st.button("Generate Battle Code", key="gen_code", use_container_width=True, type="primary"):
            if not _user_is_pro and not increment_and_check("battles"):
                st.warning("Free tier: 3 battles/day. Upgrade for unlimited!")
            else:
                code = generate_battle_code(username)
                st.session_state.battle_code = code
                st.rerun()

        if st.session_state.get("battle_code"):
            code = st.session_state.battle_code
            st.markdown(
                f'<div style="text-align:center;padding:16px;background:#1a1f2e;'
                f'border-radius:10px;margin:8px 0;">'
                f'<div style="font-size:2.5em;font-weight:900;letter-spacing:8px;'
                f'color:#f59e0b;">{code}</div>'
                f'<p style="color:#9ca3af;font-size:0.85em;">Share this code with your opponent. Expires in 1 hour.</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with b2:
        st.markdown(
            '<div style="background:linear-gradient(135deg,#4a1d6e,#6b21a8);'
            'border-radius:12px;padding:20px;text-align:center;">'
            '<h4>Join a Battle</h4>'
            '<p style="color:#9ca3af;">Enter your opponent\'s code</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        join_code = st.text_input("Battle Code", placeholder="e.g. ABC123", key="join_code_input", max_chars=6)
        if st.button("Battle!", key="join_battle", use_container_width=True):
            if not join_code:
                st.error("Enter a battle code!")
            elif len(join_code) < 6:
                st.error("Code must be 6 characters")
            else:
                if not _user_is_pro and not increment_and_check("battles"):
                    st.warning("Free tier: 3 battles/day. Upgrade for unlimited!")
                else:
                    with st.spinner("Battling..."):
                        result = accept_battle(join_code.upper(), username)
                    if result:
                        st.session_state.battle_result = result
                        st.rerun()
                    else:
                        st.error("Invalid or expired code. Check with your opponent.")

    gradient_divider()

    # --- Battle Result ---
    result = st.session_state.get("battle_result")
    if result:
        st.markdown("### Battle Result!")

        # Score display
        winner = result["winner"]
        is_tie = winner == "TIE"
        user_won = winner == username

        if is_tie:
            verdict_text = "IT'S A TIE!"
            verdict_color = "#facc15"
        elif user_won:
            verdict_text = "YOU WIN!"
            verdict_color = "#22c55e"
        else:
            verdict_text = "YOU LOSE!"
            verdict_color = "#ef4444"

        st.markdown(
            f'<div style="text-align:center;font-size:2em;font-weight:900;'
            f'color:{verdict_color};margin:16px 0;">{verdict_text}</div>',
            unsafe_allow_html=True,
        )

        # Score
        sc1, sc2, sc3 = st.columns([2, 1, 2])
        with sc1:
            st.markdown(
                f'<div style="text-align:center;">'
                f'<div style="font-size:1.2em;font-weight:bold;">{result["user_a"]}</div>'
                f'<div style="font-size:3em;font-weight:900;">{result["score_a"]}</div></div>',
                unsafe_allow_html=True,
            )
        with sc2:
            st.markdown(
                '<div style="text-align:center;font-size:2em;color:#6b7280;'
                'font-weight:bold;padding-top:30px;">VS</div>',
                unsafe_allow_html=True,
            )
        with sc3:
            st.markdown(
                f'<div style="text-align:center;">'
                f'<div style="font-size:1.2em;font-weight:bold;">{result["user_b"]}</div>'
                f'<div style="font-size:3em;font-weight:900;">{result["score_b"]}</div></div>',
                unsafe_allow_html=True,
            )

        # Category breakdown
        _CAT_EXPLANATIONS = {
            "Total Value": "Sum of all card purchase prices",
            "Best Card": "Highest-value single card",
            "Biggest Gainer": "Best P&L % from real market data",
            "Diversification": "Sports & card type variety (out of 100)",
            "Collection Size": "Total cards in collection",
        }

        st.markdown("#### Category Breakdown")
        for cat in result["categories"]:
            cc1, cc2, cc3 = st.columns([2, 2, 2])
            a_won = cat["score_a"] > cat["score_b"]
            b_won = cat["score_b"] > cat["score_a"]
            with cc1:
                style = "font-weight:bold;color:#22c55e;" if a_won else ""
                val = _fmt_display(cat["val_a"], cat["name"])
                st.markdown(f'<span style="{style}">{val}</span>', unsafe_allow_html=True)
            with cc2:
                explanation = _CAT_EXPLANATIONS.get(cat["name"], "")
                st.markdown(
                    f'<div style="text-align:center;">'
                    f'<span style="color:#e5e7eb;">{cat["name"]}</span><br>'
                    f'<span style="color:#6b7280;font-size:0.75em;">{explanation}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with cc3:
                style = "font-weight:bold;color:#22c55e;" if b_won else ""
                val = _fmt_display(cat["val_b"], cat["name"])
                st.markdown(f'<div style="text-align:right;{style}">{val}</div>', unsafe_allow_html=True)

        # Best card buy links
        gradient_divider()
        st.markdown("#### Shop the Best Cards")
        shop1, shop2 = st.columns(2)
        stats_a = result.get("stats_a", {})
        stats_b = result.get("stats_b", {})
        with shop1:
            best_a = stats_a.get("best_card_name", "")
            if best_a and best_a != "None":
                sport_a = stats_a.get("sports", ["NBA"])[0] if stats_a.get("sports") else "NBA"
                buy_url = ebay_search_affiliate_url(best_a, sport_a)
                st.markdown(
                    f'**{result["user_a"]}\'s best:** {best_a}<br>'
                    f'<a href="{buy_url}" target="_blank" class="ebay-btn">Buy on eBay</a>',
                    unsafe_allow_html=True,
                )
        with shop2:
            best_b = stats_b.get("best_card_name", "")
            if best_b and best_b != "None":
                sport_b = stats_b.get("sports", ["NBA"])[0] if stats_b.get("sports") else "NBA"
                buy_url = ebay_search_affiliate_url(best_b, sport_b)
                st.markdown(
                    f'**{result["user_b"]}\'s best:** {best_b}<br>'
                    f'<a href="{buy_url}" target="_blank" class="ebay-btn">Buy on eBay</a>',
                    unsafe_allow_html=True,
                )

        # Share card
        with st.expander("Share Result"):
            html = render_battle_card_html(result)
            st.markdown(html, unsafe_allow_html=True)

        if st.button("New Battle", key="new_battle"):
            st.session_state.pop("battle_result", None)
            st.session_state.pop("battle_code", None)
            st.rerun()

    gradient_divider()

    # --- Battle History ---
    st.markdown("### Battle History")
    history_limit = 5 if not _user_is_pro else 50
    battles = get_user_battles(username)[:history_limit]

    if battles:
        for b in battles:
            result_emoji = {"W": "", "L": "", "T": ""}[b["result"]]
            result_color = {"W": "#22c55e", "L": "#ef4444", "T": "#facc15"}[b["result"]]

            h1, h2, h3, h4 = st.columns([0.5, 2, 1, 1])
            with h1:
                st.write(result_emoji)
            with h2:
                st.write(f"vs **{b['opponent']}**")
            with h3:
                st.markdown(
                    f'<span style="color:{result_color};font-weight:bold;">'
                    f'{b["my_score"]}-{b["their_score"]}</span>',
                    unsafe_allow_html=True,
                )
            with h4:
                st.caption(b.get("date", "")[:10])
    else:
        st.info("No battles yet. Challenge a friend!")

    if not _user_is_pro:
        render_upgrade_banner("Collection Battles", "unlimited battles + full history")


def _fmt_display(val, category: str) -> str:
    """Format values for the category breakdown."""
    if category in ("Total Value", "Best Card"):
        return f"${val:,.2f}"
    elif category == "Biggest Gainer":
        return f"{val:+.1f}%"
    elif category == "Diversification":
        return f"{val}/100"
    else:
        return str(int(val))
