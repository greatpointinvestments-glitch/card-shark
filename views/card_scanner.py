"""Card Scanner page."""

import streamlit as st

from modules.card_scanner import smart_scan, build_collection_entry_from_scan
from modules.portfolio import add_card
from modules.ui_helpers import gradient_divider, whatnot_button, topps_button, drip_shop_button, ebay_button
from modules.affiliates import (
    ebay_search_affiliate_url, whatnot_search_affiliate_url,
    topps_search_affiliate_url, drip_shop_search_affiliate_url,
)
from tiers import (
    is_pro,
    check_usage_limit,
    increment_and_check,
    render_upgrade_banner,
    render_contextual_upsell,
    render_limit_warning,
)


def render():
    st.title("📷 Card Scanner")

    pro = is_pro()

    if pro:
        st.caption("Snap a photo or upload an image — AI identifies your card instantly.")
    else:
        st.caption("Snap a photo or upload an image — text recognition identifies your card. Upgrade to Pro for AI vision.")

    # --- Scan limit enforcement (bug fix: was never checked) ---
    allowed, count, limit = check_usage_limit("scans")
    if not allowed:
        render_limit_warning("scans", count, limit)
        return

    tab_camera, tab_upload = st.tabs(["Camera", "Upload"])

    scan_image = None
    scan_file_name = "card.jpg"

    with tab_camera:
        camera_img = st.camera_input("Take a photo of your card")
        if camera_img:
            scan_image = camera_img.getvalue()
            scan_file_name = "camera_capture.jpg"

    with tab_upload:
        uploaded = st.file_uploader("Upload a card image", type=["jpg", "jpeg", "png", "webp"])
        if uploaded:
            if uploaded.size > 5 * 1024 * 1024:
                st.error("Image too large (max 5 MB). Please resize or use a smaller photo.")
            else:
                scan_image = uploaded.getvalue()
                scan_file_name = uploaded.name

    if scan_image:
        # Consume a scan before firing
        if not increment_and_check("scans"):
            render_limit_warning("scans", limit, limit)
            return

        spinner_text = "Scanning card with AI..." if pro else "Reading card text..."
        with st.spinner(spinner_text):
            result = smart_scan(scan_image, scan_file_name)

        if "error" in result:
            st.error(f"Scan failed: {result['error']}")
        else:
            st.markdown('<div class="scan-result">', unsafe_allow_html=True)
            st.markdown("### Scan Results")

            conf = result.get("confidence", "low")
            conf_css = f"scan-confidence-{conf}"
            st.markdown(f'Confidence: <span class="{conf_css}">{conf.upper()}</span>', unsafe_allow_html=True)

            sr1, sr2, sr3, sr4 = st.columns(4)
            sr1.metric("Player", result.get("player_name") or "Unknown")
            sr2.metric("Year", result.get("year") or "Unknown")
            sr3.metric("Set", result.get("set_name") or "Unknown")
            sr4.metric("Sport", result.get("sport") or "Unknown")

            sr5, sr6, sr7, sr8 = st.columns(4)
            sr5.metric("Card #", result.get("card_number") or "N/A")
            sr6.metric("Variant", result.get("variant") or "Base")
            sr7.metric("Condition", result.get("condition_estimate") or "Unknown")
            sr8.write("")

            st.markdown('</div>', unsafe_allow_html=True)

            # "Find This Card" marketplace search buttons
            player_name = result.get("player_name")
            detected_sport = result.get("sport", "")
            if player_name:
                st.markdown("#### Find This Card")
                fc1, fc2, fc3, fc4 = st.columns(4)
                with fc1:
                    st.markdown(ebay_button(ebay_search_affiliate_url(player_name, detected_sport)), unsafe_allow_html=True)
                with fc2:
                    st.markdown(whatnot_button(whatnot_search_affiliate_url(player_name, detected_sport)), unsafe_allow_html=True)
                with fc3:
                    if detected_sport and detected_sport != "Pokemon":
                        st.markdown(topps_button(topps_search_affiliate_url(player_name, detected_sport)), unsafe_allow_html=True)
                with fc4:
                    st.markdown(drip_shop_button(drip_shop_search_affiliate_url(player_name, detected_sport)), unsafe_allow_html=True)

            # Pro upsell after OCR results
            if not pro:
                render_upgrade_banner(
                    "Card Scanner",
                    hook_text="AI vision identifies player, set, condition, and more with higher accuracy",
                )

            gradient_divider()
            st.markdown("#### Confirm & Add to Collection")
            st.caption("Edit any fields below before adding to your collection")

            with st.form("scanner_add_form", clear_on_submit=True):
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    scan_player = st.text_input("Player Name", value=result.get("player_name") or "")
                with sc2:
                    _sport_options = ["NBA", "NFL", "MLB", "Pokemon"]
                    _detected_sport = result.get("sport", "NBA")
                    _sport_idx = _sport_options.index(_detected_sport) if _detected_sport in _sport_options else 0
                    scan_sport = st.selectbox("Sport", _sport_options, index=_sport_idx)
                with sc3:
                    scan_year = st.text_input("Year", value=result.get("year") or "")

                sc4, sc5, sc6 = st.columns(3)
                with sc4:
                    scan_set = st.text_input("Set Name", value=result.get("set_name") or "")
                with sc5:
                    scan_variant = st.text_input("Variant", value=result.get("variant") or "Base")
                with sc6:
                    scan_card_num = st.text_input("Card #", value=result.get("card_number") or "")

                sc7, sc8 = st.columns(2)
                with sc7:
                    scan_price = st.number_input("Purchase Price ($)", min_value=0.0, step=1.0, key="scan_price")
                with sc8:
                    scan_date = st.date_input("Purchase Date", key="scan_date")

                scan_submit = st.form_submit_button("Add to Collection", use_container_width=True)

            if scan_submit and not scan_player:
                st.warning("Player name is required to add to collection.")

            if scan_submit and scan_player:
                if not pro:
                    from config.settings import FREE_TIER_LIMITS
                    from modules.portfolio import get_portfolio
                    current_count = len(get_portfolio())
                    max_cards = FREE_TIER_LIMITS.get("portfolio_max_cards", 25)
                    if current_count >= max_cards:
                        st.error(f"Free accounts can hold {max_cards} cards. Upgrade to Pro for unlimited.")
                        st.stop()

                entry = build_collection_entry_from_scan(result, scan_price, str(scan_date))
                entry["player_name"] = scan_player
                entry["sport"] = scan_sport
                entry["year"] = scan_year
                entry["set_name"] = scan_set
                entry["variant"] = scan_variant
                entry["card_number"] = scan_card_num

                add_card(
                    player_name=entry["player_name"],
                    sport=entry["sport"],
                    card_type=entry["card_type"],
                    purchase_price=entry["purchase_price"],
                    purchase_date=entry["purchase_date"],
                    quantity=entry["quantity"],
                    year=entry.get("year"),
                    set_name=entry.get("set_name"),
                    card_number=entry.get("card_number"),
                    variant=entry.get("variant"),
                    scan_source=entry.get("scan_source"),
                    scan_confidence=entry.get("scan_confidence"),
                )
                st.success(f"Added {scan_player} to your collection!")
