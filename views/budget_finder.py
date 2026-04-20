"""What Can I Get? — Budget-first card finder page."""

import streamlit as st

from modules.ui_helpers import render_listing_row, deal_score, gradient_divider, tcgplayer_button
from modules.ebay_search import search_ebay_cards, flag_deals
from modules.pokemon_tcg import search_pokemon_cards, get_pokemon_market_price
from tiers import check_usage_limit, increment_and_check, render_limit_warning, render_disclaimer


def render(demo_mode: bool = False):
    st.title("💰 What Can I Get?")
    st.caption("Enter your budget and pick a player — we'll find the best cards you can afford")
    render_disclaimer(compact=True)

    # Track quick-pick budget separately to avoid widget key conflict
    _default_budget = st.session_state.get("_bf_quick_budget", 25.0)

    col1, col2, col3 = st.columns(3)
    with col1:
        player_name = st.text_input("Player Name", placeholder="e.g. Victor Wembanyama", key="bf_player")
    with col2:
        sport = st.selectbox("Sport", ["NBA", "NFL", "MLB", "Pokemon"], key="bf_sport")
    with col3:
        budget = st.number_input("My Budget ($)", min_value=1.0, value=_default_budget, step=5.0, key="bf_budget")

    # Quick budget buttons
    qb_cols = st.columns(4)
    quick_amounts = [10, 25, 50, 100]
    for i, amt in enumerate(quick_amounts):
        with qb_cols[i]:
            if st.button(f"${amt}", key=f"qb_{amt}", use_container_width=True):
                st.session_state._bf_quick_budget = float(amt)
                st.rerun()

    if not player_name:
        st.info("Type a player name above to get started.")
        return

    allowed, count, limit = check_usage_limit("searches")
    if not allowed:
        render_limit_warning("searches", count, limit)
        st.stop()

    if sport == "Pokemon":
        with st.spinner(f"Finding Pokemon cards for {player_name} under ${budget:.0f}..."):
            cards = search_pokemon_cards(player_name)
        increment_and_check("searches")
        affordable = [c for c in cards if 0 < get_pokemon_market_price(c) <= budget]
        affordable.sort(key=lambda c: get_pokemon_market_price(c))
        if affordable:
            st.success(f"Found {len(affordable)} card{'s' if len(affordable) != 1 else ''} under ${budget:.0f} for {player_name}")
            for card in affordable:
                price = get_pokemon_market_price(card)
                c1, c2, c3 = st.columns([0.8, 3, 1.2])
                with c1:
                    if card.get("image_small"):
                        st.image(card["image_small"], width=50)
                with c2:
                    st.write(f"**{card['name']}** — {card.get('set_name', '')} | {card.get('rarity', '')}")
                with c3:
                    st.write(f"${price:.2f}")
                    if card.get("tcgplayer_url"):
                        st.markdown(tcgplayer_button(card["tcgplayer_url"]), unsafe_allow_html=True)
        else:
            st.warning(f"No Pokemon cards found under ${budget:.0f} for {player_name}. Try a higher budget.")
    else:
        with st.spinner(f"Finding cards for {player_name} under ${budget:.0f}..."):
            listings = search_ebay_cards(player_name, sport, "Any", sort="price")
            listings = flag_deals(listings)

        increment_and_check("searches")

        # Filter to budget
        affordable = [l for l in listings if l.get("total", 0) <= budget]

        # Sort by deal score (best deals first)
        affordable.sort(key=lambda l: deal_score(l.get("vs_median", 0)), reverse=True)

        if affordable:
            st.success(f"Found {len(affordable)} card{'s' if len(affordable) != 1 else ''} under ${budget:.0f} for {player_name}")
            for listing in affordable:
                render_listing_row(listing)
        else:
            st.warning(f"No cards found under ${budget:.0f} for {player_name}. Try a higher budget or different player.")

    gradient_divider()


