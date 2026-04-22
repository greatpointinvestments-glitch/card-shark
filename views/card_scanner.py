"""Card Scanner page."""

import streamlit as st

from modules.card_scanner import smart_scan
from modules.trade_analyzer import get_card_market_value
from modules.ui_helpers import gradient_divider, whatnot_button, topps_button, drip_shop_button, ebay_button, market_signal_badge
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

            # --- Estimated Value lookup ---
            _scan_sport = result.get("sport", "NBA")
            _scan_player = result.get("player_name", "")
            _scan_variant = result.get("variant", "Base")
            _scan_year = result.get("year")
            _scan_set = result.get("set_name")
            _suggested_price = 0.0

            if _scan_player:
                with st.spinner("Looking up market value..."):
                    _market = get_card_market_value(
                        _scan_player, _scan_sport, _scan_variant,
                        year=_scan_year, set_name=_scan_set,
                    )
                if _market.get("avg_sold", 0) > 0 or _market.get("avg_active", 0) > 0:
                    _suggested_price = _market["avg_sold"] if _market["avg_sold"] > 0 else _market["avg_active"]
                    st.markdown("#### Estimated Value")
                    vm1, vm2, vm3, vm4 = st.columns(4)
                    vm1.metric("Avg Sold", f"${_market['avg_sold']:.2f}")
                    vm2.metric("Avg Active", f"${_market['avg_active']:.2f}")
                    vm3.metric("90d Volume", f"{_market['sold_volume']} sales")
                    vm4.markdown("**Market Signal**")
                    vm4.markdown(market_signal_badge(_market["market_signal"]), unsafe_allow_html=True)

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
            st.markdown("#### Add to Collection")
            st.caption("Search for this card in the marketplace and add it with real images and pricing")

            if st.button("Find This Card in My Collection", type="primary", use_container_width=True, key="scanner_to_collection"):
                st.session_state["scanner_to_collection"] = {
                    "player_name": result.get("player_name", ""),
                    "year": result.get("year", ""),
                    "card_number": result.get("card_number", ""),
                    "sport": result.get("sport", "NBA"),
                }
                st.session_state.nav_target = "📁 My Collection"
                st.rerun()
