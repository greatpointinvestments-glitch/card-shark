"""Pack Simulator — rip virtual packs, see real prices, buy the hits."""

import streamlit as st

from config.pull_rates import PRODUCTS, FREE_PRODUCTS
from modules.pack_simulator import rip_pack, rip_box, save_rip_result, get_rip_stats
from modules.rip_battles import create_rip_challenge, accept_rip_battle, get_rip_hall_of_fame
from modules.affiliates import ebay_search_affiliate_url, tcgplayer_search_affiliate_url
from modules.ui_helpers import gradient_divider
from tiers import is_pro, render_upgrade_banner, increment_and_check


def render():
    st.title("Pack Simulator")
    st.caption("Pick a product. Rip a pack. See what you pulled with real market prices.")

    username = st.session_state.get("username")
    _user_is_pro = is_pro()

    # --- Product Picker ---
    st.markdown("### Choose Your Product")

    # Sport filter
    sports = sorted(set(p["sport"] for p in PRODUCTS.values()))
    sport_filter = st.radio("Sport", ["All"] + sports, horizontal=True, key="pack_sport")

    available = {}
    for key, product in PRODUCTS.items():
        if sport_filter != "All" and product["sport"] != sport_filter:
            continue
        if not _user_is_pro and key not in FREE_PRODUCTS:
            continue
        available[key] = product

    if not available:
        if not _user_is_pro:
            render_upgrade_banner("Pack Simulator", "all products unlocked")
        else:
            st.info("No products match your filter.")
        return

    product_key = st.selectbox(
        "Product",
        list(available.keys()),
        key="pack_product",
    )
    product = available[product_key]

    # Product info card
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#1a1f2e,#2d3748);border-radius:12px;'
        f'padding:16px 20px;margin:10px 0;border:1px solid #3b4560;">'
        f'<strong>{product_key}</strong><br>'
        f'<span style="color:#9ca3af;">{product["description"]}</span><br>'
        f'<span style="color:#f59e0b;">{product["cards_per_pack"]} cards/pack &bull; '
        f'${product["pack_price"]:.2f}/pack &bull; '
        f'{product["packs_per_box"]} packs/box</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    gradient_divider()

    # --- Rip Buttons ---
    st.markdown("### Rip It!")
    r1, r2 = st.columns(2)

    with r1:
        rip_label = f"Rip a Pack (${product['pack_price']:.2f})"
        if st.button(rip_label, key="rip_pack", use_container_width=True, type="primary"):
            # Check free tier limit
            if not _user_is_pro and username:
                if not increment_and_check("packs"):
                    st.warning("Free tier: 3 packs/day. Upgrade to Pro for unlimited rips!")
                    return
            st.session_state.last_rip = {
                "type": "pack",
                "product": product_key,
            }
            st.rerun()

    with r2:
        if _user_is_pro:
            box_label = f"Rip a Box (${product['box_price']:.2f})"
            if st.button(box_label, key="rip_box", use_container_width=True):
                st.session_state.last_rip = {
                    "type": "box",
                    "product": product_key,
                }
                st.rerun()
        else:
            st.button(
                f"Rip a Box (PRO)", key="rip_box_locked",
                use_container_width=True, disabled=True,
            )
            st.caption("Box rips are a Pro feature")

    # --- Rip Results ---
    last_rip = st.session_state.get("last_rip")
    if last_rip and last_rip.get("product") == product_key:
        gradient_divider()

        if last_rip["type"] == "pack":
            with st.spinner("Ripping pack..."):
                cards = rip_pack(product_key)
            if cards:
                _render_pack_results(cards, product, username)
        elif last_rip["type"] == "box":
            with st.spinner("Ripping box..."):
                box_result = rip_box(product_key)
            if box_result:
                _render_box_results(box_result, product, username)

    gradient_divider()

    # --- Rip Stats ---
    if username:
        st.markdown("### Your Rip Stats")
        stats = get_rip_stats(username)
        if stats["total_packs"] > 0:
            st1, st2, st3, st4 = st.columns(4)
            st1.metric("Packs Ripped", stats["total_packs"])
            st2.metric("Virtual Spent", f"${stats['total_spent_virtual']:.2f}")
            st3.metric("Total Value", f"${stats['total_value_pulled']:.2f}")
            pl = stats["virtual_pl"]
            st4.metric("Virtual P&L", f"${pl:+.2f}", delta=f"${pl:+.2f}")

            if stats["best_pull"]:
                bp = stats["best_pull"]
                st.markdown(
                    f'Best pull ever: **{bp["player_name"]}** {bp["card_type"]} '
                    f'(${bp["value"]:.2f}) on {bp.get("date", "N/A")}'
                )
        else:
            st.info("Rip your first pack to start tracking stats!")
    else:
        st.info("Log in to save your rip history and stats!")

    if not _user_is_pro:
        render_upgrade_banner("Pack Simulator", "unlimited packs, all products, box rips")

    # --- Hall of Fame + Rip Battle Tabs ---
    gradient_divider()
    hof_tab, battle_tab = st.tabs(["Hall of Fame", "Rip Battle"])

    with hof_tab:
        st.markdown("### Pack Hall of Fame")
        st.caption("The best rippers across all of CardHawk")
        hof = get_rip_hall_of_fame()

        medal_cols = st.columns(3)
        with medal_cols[0]:
            bp = hof["best_pull"]
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#854d0e,#ca8a04);border-radius:12px;'
                f'padding:16px;text-align:center;">'
                f'<div style="font-size:1.5em;">🥇</div>'
                f'<strong>Best Single Pull</strong><br>'
                f'<span style="font-size:1.3em;font-weight:900;">${bp["value"]:.2f}</span><br>'
                f'<span style="color:#d1d5db;">{bp["player"]} ({bp["card_type"]})</span><br>'
                f'<span style="color:#fbbf24;font-size:0.85em;">by {bp["user"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with medal_cols[1]:
            mp = hof["most_profitable"]
            pl_str = f"${mp['pl']:+.2f}" if isinstance(mp["pl"], (int, float)) else "—"
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#065f46,#059669);border-radius:12px;'
                f'padding:16px;text-align:center;">'
                f'<div style="font-size:1.5em;">💰</div>'
                f'<strong>Most Profitable</strong><br>'
                f'<span style="font-size:1.3em;font-weight:900;">{pl_str}</span><br>'
                f'<span style="color:#fbbf24;font-size:0.85em;">by {mp["user"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with medal_cols[2]:
            mpk = hof["most_packs"]
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#1e3a5f,#1e40af);border-radius:12px;'
                f'padding:16px;text-align:center;">'
                f'<div style="font-size:1.5em;">🎰</div>'
                f'<strong>Most Packs Ripped</strong><br>'
                f'<span style="font-size:1.3em;font-weight:900;">{mpk["count"]}</span><br>'
                f'<span style="color:#fbbf24;font-size:0.85em;">by {mpk["user"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with battle_tab:
        st.markdown("### Rip Battle")
        st.caption("Challenge a friend — both rip the same product, highest value wins!")

        if not username:
            st.warning("Log in to start a Rip Battle!")
        else:
            rb1, rb2 = st.columns(2)
            with rb1:
                st.markdown("**Create Challenge**")
                rb_product = st.selectbox("Product", list(PRODUCTS.keys()), key="rb_product")
                if st.button("Create Rip Challenge", key="rb_create", type="primary", use_container_width=True):
                    code = create_rip_challenge(username, rb_product)
                    st.session_state.rip_battle_code = code
                    st.rerun()

                if st.session_state.get("rip_battle_code"):
                    code = st.session_state.rip_battle_code
                    st.markdown(
                        f'<div style="text-align:center;padding:16px;background:#1a1f2e;'
                        f'border-radius:10px;margin:8px 0;">'
                        f'<div style="font-size:2.5em;font-weight:900;letter-spacing:8px;'
                        f'color:#f59e0b;">{code}</div>'
                        f'<p style="color:#9ca3af;font-size:0.85em;">Share this code. Expires in 1 hour.</p>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            with rb2:
                st.markdown("**Join Challenge**")
                rb_code = st.text_input("Battle Code", placeholder="e.g. ABC123", key="rb_join_code", max_chars=6)
                if st.button("Rip Battle!", key="rb_join", use_container_width=True):
                    if not rb_code or len(rb_code) < 6:
                        st.error("Enter a 6-character code")
                    else:
                        with st.spinner("Ripping packs..."):
                            result = accept_rip_battle(rb_code.upper(), username)
                        if result:
                            st.session_state.rip_battle_result = result
                            st.rerun()
                        else:
                            st.error("Invalid or expired code.")

            # Display result
            rb_result = st.session_state.get("rip_battle_result")
            if rb_result:
                gradient_divider()
                winner = rb_result["winner"]
                is_tie = winner == "TIE"
                user_won = winner == username

                if is_tie:
                    verdict = "IT'S A TIE!"
                    color = "#facc15"
                elif user_won:
                    verdict = "YOU WIN!"
                    color = "#22c55e"
                else:
                    verdict = "YOU LOSE!"
                    color = "#ef4444"

                st.markdown(
                    f'<div style="text-align:center;font-size:2em;font-weight:900;color:{color};'
                    f'margin:12px 0;">{verdict}</div>',
                    unsafe_allow_html=True,
                )

                rc1, rc2, rc3 = st.columns([2, 1, 2])
                with rc1:
                    st.markdown(f"**{rb_result['user_a']}**")
                    st.metric("Pack Value", f"${rb_result['total_value_a']:.2f}")
                    bp_a = rb_result["best_pull_a"]
                    st.caption(f"Best: {bp_a['player']} (${bp_a['value']:.2f})")
                    st.caption(f"Hits: {rb_result['hits_a']}")
                with rc2:
                    st.markdown('<div style="text-align:center;font-size:1.5em;color:#6b7280;padding-top:30px;">VS</div>', unsafe_allow_html=True)
                with rc3:
                    st.markdown(f"**{rb_result['user_b']}**")
                    st.metric("Pack Value", f"${rb_result['total_value_b']:.2f}")
                    bp_b = rb_result["best_pull_b"]
                    st.caption(f"Best: {bp_b['player']} (${bp_b['value']:.2f})")
                    st.caption(f"Hits: {rb_result['hits_b']}")

                if st.button("New Rip Battle", key="rb_new"):
                    st.session_state.pop("rip_battle_result", None)
                    st.session_state.pop("rip_battle_code", None)
                    st.rerun()


def _render_pack_results(cards: list[dict], product: dict, username: str | None):
    """Render the results of a single pack rip."""
    total_value = sum(c["value"] for c in cards)
    cost = product["pack_price"]
    profit = total_value - cost
    hits = [c for c in cards if c["is_hit"]]

    st.markdown("### Pack Results!")

    pm1, pm2, pm3 = st.columns(3)
    pm1.metric("Pack Value", f"${total_value:.2f}")
    pm2.metric("Pack Cost", f"${cost:.2f}")
    color = "normal" if profit >= 0 else "inverse"
    pm3.metric("Profit/Loss", f"${profit:+.2f}", delta=f"${profit:+.2f}")

    if hits:
        st.success(f"You pulled {len(hits)} hit{'s' if len(hits) > 1 else ''}!")

    for card in cards:
        _render_card_row(card, product["sport"])

    # Save result
    if username:
        save_rip_result(username, product.get("_key", ""), cards, cost)


def _render_card_row(card: dict, sport: str):
    """Render a single card from the pack with card image."""
    is_hit = card["is_hit"]
    image_url = card.get("image_url", "")

    # Hit styling
    if is_hit:
        border = "border-left:4px solid #f59e0b;" if card["value"] < 20 else "border-left:4px solid #22c55e;"
        bg = "background:rgba(245,158,11,0.08);" if card["value"] < 20 else "background:rgba(34,197,94,0.1);"
    else:
        border = ""
        bg = ""

    # Image size: larger for hits
    if is_hit and image_url:
        img_size = "160px" if card["value"] >= 20 else "112px"
        glow = "box-shadow:0 0 12px rgba(245,158,11,0.5);" if card["value"] >= 20 else ""
    else:
        img_size = "80px"
        glow = ""

    c0, c1, c2, c3, c4 = st.columns([0.8, 3, 1.5, 1, 1.5])

    with c0:
        if image_url:
            st.markdown(
                f'<img src="{image_url}" style="width:{img_size};height:auto;'
                f'border-radius:6px;{glow}" />',
                unsafe_allow_html=True,
            )
        else:
            st.write("")

    with c1:
        hit_tag = ' <span class="pack-hit">HIT</span>' if is_hit else ""
        st.markdown(
            f'<div style="{bg}{border}padding:6px 12px;border-radius:6px;margin:2px 0;">'
            f'<strong>{card["player_name"]}</strong>{hit_tag}<br>'
            f'<span style="color:#9ca3af;font-size:0.9em;">{card["tier_name"]}'
            f'{" &bull; " + card["card_type"] if card["card_type"] != card["tier_name"] else ""}'
            f'</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        value_color = "#22c55e" if card["value"] >= 10 else "#f59e0b" if card["value"] >= 3 else "#9ca3af"
        st.markdown(
            f'<span style="color:{value_color};font-weight:bold;font-size:1.1em;">'
            f'${card["value"]:.2f}</span>',
            unsafe_allow_html=True,
        )
    with c3:
        # Buy button — searches for the player, not the exact virtual card
        if sport == "Pokemon":
            url = tcgplayer_search_affiliate_url(card["player_name"])
        else:
            url = ebay_search_affiliate_url(card["player_name"], sport)
        st.markdown(
            f'<a href="{url}" target="_blank" class="ebay-btn" '
            f'style="font-size:0.75em;padding:3px 8px;">Buy Cards Like This</a>',
            unsafe_allow_html=True,
        )
    with c4:
        # Add to collection button
        btn_key = f"add_{card['player_name']}_{card['card_type']}_{card['value']}"
        if st.button("+ Collection", key=btn_key, help="Add to your collection"):
            try:
                from modules.portfolio import add_card
                add_card(
                    player_name=card["player_name"],
                    sport=sport,
                    card_type=card["card_type"],
                    purchase_price=0,
                    purchase_date="",
                    scan_source="pack_sim",
                )
                st.toast(f"Added {card['player_name']} to collection!")
            except Exception:
                st.error("Log in to add cards to your collection")


def _render_box_results(box_result: dict, product: dict, username: str | None):
    """Render box rip results — summary + expandable packs."""
    st.markdown("### Box Results!")

    bm1, bm2, bm3 = st.columns(3)
    bm1.metric("Box Value", f"${box_result['total_value']:.2f}")
    bm2.metric("Box Cost", f"${box_result['box_cost']:.2f}")
    pl = box_result["profit_loss"]
    bm3.metric("Profit/Loss", f"${pl:+.2f}", delta=f"${pl:+.2f}")

    if box_result["best_pull"]:
        bp = box_result["best_pull"]
        st.success(
            f"Best pull: **{bp['player_name']}** {bp['card_type']} (${bp['value']:.2f})"
        )

    # Show each pack in an expander
    for pack in box_result["packs"]:
        hits_in_pack = sum(1 for c in pack["cards"] if c["is_hit"])
        label = f"Pack {pack['pack_number']} — ${pack['pack_value']:.2f}"
        if hits_in_pack:
            label += f" ({hits_in_pack} hit{'s' if hits_in_pack > 1 else ''})"

        with st.expander(label):
            for card in pack["cards"]:
                _render_card_row(card, product["sport"])

    # Save all packs
    if username:
        for pack in box_result["packs"]:
            save_rip_result(username, product.get("_key", ""), pack["cards"], product["pack_price"])
