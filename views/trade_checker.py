"""Trade Checker page — scan-based card input."""

import streamlit as st

from modules.ui_helpers import gradient_divider, market_signal_badge
from modules.trade_analyzer import get_card_market_value, compute_trade_grade
from modules.card_scanner import scan_card_image, _anthropic_is_configured
from modules.card_types import get_card_type_options
from tiers import check_usage_limit, increment_and_check, render_limit_warning, render_disclaimer


def _scan_and_add(image_bytes, file_name, side_key):
    """Scan a card image and add it to the specified trade side."""
    with st.spinner("Scanning card..."):
        result = scan_card_image(image_bytes, file_name)

    if result.get("error"):
        st.error(f"Scan failed: {result['error']}")
        return

    player = result.get("player_name")
    if not player:
        st.error("Couldn't identify the player. Try a clearer photo.")
        return

    sport = result.get("sport", "NBA")
    variant = result.get("variant", "Base")
    year = result.get("year", "")
    set_name = result.get("set_name", "")
    confidence = result.get("confidence", "low")

    # Build a descriptive card type from the scan
    card_desc = f"{year} {set_name} {variant}".strip() or "Base"

    # Look up market value using full card context
    with st.spinner(f"Looking up {player}..."):
        market = get_card_market_value(player, sport, variant, year=year, set_name=set_name)

    card = {
        "player": player,
        "sport": sport,
        "card_type": card_desc,
        "variant": variant,
        "year": year,
        "set_name": set_name,
        "confidence": confidence,
        "value": market["avg_sold"] if market["avg_sold"] > 0 else market["avg_active"],
        "source": "eBay",
        "market": market,
        "on_breakout_watchlist": market.get("on_breakout_watchlist", False),
    }
    st.session_state[side_key].append(card)


def _render_card_input(side_key, side_label):
    """Render scan input + card list for one side of the trade."""
    st.markdown(f"### {side_label}")

    scanner_ok = _anthropic_is_configured()

    if scanner_ok:
        tab_camera, tab_upload, tab_manual = st.tabs(
            ["📷 Camera", "📁 Upload", "✏️ Manual"])
    else:
        tab_manual = None
        tab_camera = None
        tab_upload = None

    if scanner_ok:
        with tab_camera:
            cam_img = st.camera_input(
                f"Snap {side_label.lower()}", key=f"cam_{side_key}")
            if cam_img:
                _scan_and_add(cam_img.getvalue(), "card.jpg", side_key)
                st.rerun()

        with tab_upload:
            upload = st.file_uploader(
                f"Upload {side_label.lower()}", type=["jpg", "jpeg", "png"],
                key=f"upload_{side_key}")
            if upload:
                _scan_and_add(upload.getvalue(), upload.name, side_key)
                st.rerun()

        with tab_manual:
            _render_manual_input(side_key)
    else:
        st.info("Card scanner requires an Anthropic API key. Using manual entry.")
        _render_manual_input(side_key)

    # Show added cards
    total = 0
    for i, card in enumerate(st.session_state[side_key]):
        total += card.get("value", 0)
        cc1, cc2, cc3 = st.columns([3, 1, 0.5])
        with cc1:
            label = f"**{card['player']}**"
            if card.get("card_type") and card["card_type"] != "Any":
                label += f" ({card['card_type']})"
            if card.get("on_breakout_watchlist"):
                label += " 🚀"
            if card.get("confidence"):
                conf = card["confidence"]
                if conf == "high":
                    label += " ✅"
                elif conf == "medium":
                    label += " 🟡"
            st.write(label)
        with cc2:
            st.write(f"${card.get('value', 0):.2f}")
        with cc3:
            if st.button("X", key=f"rm_{side_key}_{i}"):
                st.session_state[side_key].pop(i)
                st.rerun()

    st.markdown(f"**Total: ${total:.2f}**")
    return total


def _render_manual_input(side_key):
    """Manual entry form with specific card details for accurate lookups."""
    with st.form(f"{side_key}_manual_form", clear_on_submit=True):
        player = st.text_input("Player Name", placeholder="e.g. Victor Wembanyama",
                               key=f"manual_player_{side_key}")
        mc1, mc2 = st.columns(2)
        with mc1:
            sport = st.selectbox("Sport", ["NBA", "NFL", "MLB", "Pokemon"],
                                 key=f"manual_sport_{side_key}")
        with mc2:
            card_type = st.selectbox("Card Type", get_card_type_options(),
                                     key=f"manual_type_{side_key}")
        mc3, mc4, mc5 = st.columns(3)
        with mc3:
            year = st.text_input("Year", placeholder="e.g. 2023-24",
                                 key=f"manual_year_{side_key}")
        with mc4:
            set_name = st.text_input("Set", placeholder="e.g. Prizm",
                                     key=f"manual_set_{side_key}")
        with mc5:
            value = st.number_input("Value ($) — 0 to auto-check",
                                    min_value=0.0, step=1.0,
                                    key=f"manual_value_{side_key}")
        add = st.form_submit_button("Add Card")

    if add and player:
        # Build descriptive card type label
        card_desc_parts = []
        if year:
            card_desc_parts.append(year.strip())
        if set_name:
            card_desc_parts.append(set_name.strip())
        if card_type and card_type != "Any":
            card_desc_parts.append(card_type)
        card_desc = " ".join(card_desc_parts) if card_desc_parts else card_type

        card = {"player": player, "sport": sport, "card_type": card_desc}
        if value > 0:
            card["value"] = value
            card["source"] = "manual"
        else:
            with st.spinner(f"Looking up {player} {card_desc}..."):
                market = get_card_market_value(player, sport, card_type)
            card["value"] = market["avg_sold"] if market["avg_sold"] > 0 else market["avg_active"]
            card["source"] = "eBay"
            card["market"] = market
            card["on_breakout_watchlist"] = market.get("on_breakout_watchlist", False)
        st.session_state[side_key].append(card)
        st.rerun()


def render():
    st.title("🔄 Trade Checker")
    st.caption("Scan your cards, scan theirs. See who wins.")
    render_disclaimer(compact=True)

    if "your_cards" not in st.session_state:
        st.session_state.your_cards = []
    if "their_cards" not in st.session_state:
        st.session_state.their_cards = []

    your_col, divider_col, their_col = st.columns([5, 0.5, 5])

    with your_col:
        your_total = _render_card_input("your_cards", "Your Cards")

    with divider_col:
        st.markdown(
            "<div style='text-align:center; font-size:2em; padding-top:120px'>"
            "vs</div>", unsafe_allow_html=True)

    with their_col:
        their_total = _render_card_input("their_cards", "Their Cards")

    gradient_divider()
    btn_col1, btn_col2 = st.columns([3, 1])
    with btn_col1:
        analyze = st.button("🔍 Check This Trade", type="primary",
                            use_container_width=True)
    with btn_col2:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.your_cards = []
            st.session_state.their_cards = []
            st.rerun()

    if analyze:
        if not st.session_state.your_cards or not st.session_state.their_cards:
            st.warning("Add at least one card to each side to check the trade.")
        else:
            allowed, count, limit = check_usage_limit("trades")
            if not allowed:
                render_limit_warning("trades", count, limit)
                st.stop()
            increment_and_check("trades")

            result = compute_trade_grade(
                st.session_state.your_cards, st.session_state.their_cards)
            grade = result["grade"]

            gradient_divider()
            grade_css = f"grade-{grade.lower()}"
            r1, r2 = st.columns([1, 3])
            with r1:
                st.markdown(
                    f'<div class="grade-badge {grade_css}">{grade}</div>',
                    unsafe_allow_html=True)
            with r2:
                st.markdown(f"### {result['verdict']}")
                diff = result["diff_pct"]
                if diff >= 0:
                    st.markdown(
                        f"You're getting **{diff:.1f}% more value** in this trade.")
                else:
                    st.markdown(
                        f"You're giving up **{abs(diff):.1f}% more value** "
                        f"in this trade.")

            vc1, vc2, vc3 = st.columns(3)
            vc1.metric("You Give Up", f"${result['your_total']:.2f}")
            vc2.metric("You Get Back", f"${result['their_total']:.2f}")
            if result["breakout_bonus"] > 0:
                vc3.metric("Breakout Upside Bonus",
                           f"+${result['breakout_bonus']:.2f}")

            gradient_divider()
            st.markdown("#### Card-by-Card Breakdown")

            st.markdown("**Your cards:**")
            for card in st.session_state.your_cards:
                bc1, bc2, bc3, bc4 = st.columns([3, 1, 1, 1])
                with bc1:
                    st.write(f"{card['player']} ({card.get('card_type', 'Any')})")
                with bc2:
                    st.write(f"${card.get('value', 0):.2f}")
                with bc3:
                    st.write(card.get("source", "manual"))
                with bc4:
                    market = card.get("market", {})
                    if market:
                        st.write(market.get("price_trend", "—"))

            st.markdown("**Their cards:**")
            for card in st.session_state.their_cards:
                bc1, bc2, bc3, bc4 = st.columns([3, 1, 1, 1])
                with bc1:
                    label = f"{card['player']} ({card.get('card_type', 'Any')})"
                    if card.get("on_breakout_watchlist"):
                        label += " 🚀 Breakout Watchlist"
                    st.write(label)
                with bc2:
                    st.write(f"${card.get('value', 0):.2f}")
                with bc3:
                    st.write(card.get("source", "manual"))
                with bc4:
                    market = card.get("market", {})
                    if market:
                        st.write(market.get("price_trend", "—"))

            ebay_cards = [c for c in
                          st.session_state.your_cards + st.session_state.their_cards
                          if c.get("market")]
            if ebay_cards:
                gradient_divider()
                st.markdown("#### Market Details")
                for card in ebay_cards:
                    m = card["market"]
                    st.markdown(
                        f"**{card['player']}** ({card.get('card_type', 'Any')})"
                        f" — {card['sport']}")
                    dm1, dm2, dm3, dm4 = st.columns(4)
                    dm1.metric("Avg Sold", f"${m['avg_sold']:.2f}")
                    dm2.metric("90d Volume", f"{m['sold_volume']} sales")
                    dm3.metric("Trend", m["price_trend"],
                               f"{m['trend_delta']:+.1f}%")
                    dm4.markdown(market_signal_badge(m["market_signal"]),
                                 unsafe_allow_html=True)


render()
