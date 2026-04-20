"""Flip Finder page."""

import streamlit as st

from modules.ui_helpers import card_thumbnail_lg, ebay_button, gradient_divider
from modules.affiliates import affiliate_url
from modules.flip_finder import find_flip_opportunities
from modules.card_types import get_card_type_options
from tiers import can_access, render_upgrade_prompt, render_disclaimer


def render():
    st.title("💰 Flip Finder")
    st.caption("BIN listings priced below recent sold prices — money on the table")
    render_disclaimer(compact=True)

    if not can_access("flip_finder"):
        render_upgrade_prompt("Flip Finder", "See which cards are listed below their sold prices — the easiest money in the hobby.")
        st.stop()

    ff_c1, ff_c2, ff_c3 = st.columns([2, 2, 1.5])
    with ff_c1:
        ff_sports = st.multiselect("Sports", ["NBA", "NFL", "MLB", "Pokemon"], default=["NBA", "NFL", "MLB"], key="ff_sports")
    with ff_c2:
        ff_type = st.selectbox("Card Type", get_card_type_options(), key="ff_type")
    with ff_c3:
        ff_conf = st.select_slider(
            "Min Confidence",
            options=["Low", "Medium", "High"],
            value="Medium",
            key="ff_confidence",
            help="Filters out flips with thin comp data or sketchy sellers.",
        )
    _conf_threshold = {"Low": 40, "Medium": 60, "High": 80}[ff_conf]

    if ff_sports:
        with st.spinner("Scanning for flip opportunities..."):
            flips = find_flip_opportunities(ff_sports, ff_type, min_confidence=_conf_threshold)

        if flips:
            st.success(f"Found {len(flips)} flip opportunities (confidence >= {_conf_threshold}).")

            for flip in flips:
                fc0, fc1, fc2, fc3, fc4, fc5 = st.columns([0.7, 3, 1.2, 1.2, 1.2, 1.2])
                with fc0:
                    st.markdown(card_thumbnail_lg(flip["image_url"]), unsafe_allow_html=True)
                with fc1:
                    flip_aff = affiliate_url(flip["url"])
                    conf = flip.get("confidence", 0)
                    label = flip.get("confidence_label", "Low")
                    pill_bg = {"High": "#065f46", "Medium": "#92400e", "Low": "#7f1d1d", "Very Low": "#450a0a"}.get(label, "#374151")
                    parallel = flip.get("parallel", "base").replace("_", " ").title()
                    grade = flip.get("grade") or ("Raw" if not flip.get("is_graded") else "Graded")
                    rookie_tag = " • RC" if flip.get("is_rookie") else ""
                    st.markdown(
                        f'<a href="{flip_aff}" target="_blank" style="text-decoration:none">'
                        f'{flip["title"][:70]}</a>'
                        f'<br><small style="color:#9ca3af">{flip["player"]} • {flip["sport"]} • {parallel} • {grade}{rookie_tag}</small>'
                        f'<br><span style="background:{pill_bg};color:white;padding:2px 8px;border-radius:4px;'
                        f'font-size:0.75em;font-weight:bold;margin-top:4px;display:inline-block;">'
                        f'{label} confidence ({conf}) • {flip["matched_comps"]} comps</span>',
                        unsafe_allow_html=True,
                    )
                with fc2:
                    st.metric("BIN Price", f"${flip['active_price']:.2f}")
                with fc3:
                    st.metric("Median Sold", f"${flip['median_sold']:.2f}")
                with fc4:
                    st.markdown(f'<span class="spread-positive">+${flip["spread"]:.2f} ({flip["spread_pct"]:.0f}%)</span>', unsafe_allow_html=True)
                with fc5:
                    st.markdown(ebay_button(flip["url"]), unsafe_allow_html=True)

            st.markdown("---")
            st.caption(
                "**Before you buy:** verify the listing photos match the title, check the return policy, "
                "and confirm condition (raw vs. graded, centering, corners). "
                "Spread assumes you resell at the median — factor ~13% in fees."
            )
        else:
            st.info("No flip opportunities found at this confidence level. Lower the threshold or try different filters.")

        gradient_divider()

        with st.expander("How Flip Finder Works"):
            st.markdown("""
**Flip Finder scans for arbitrage opportunities** by comparing active Buy It Now listings
against recently sold prices for the **same variation of the same card**.

**Quality filters applied automatically:**
- Same parallel/variation only (no base vs. refractor mixups)
- Raw vs. graded kept separate
- Rookies only compared to rookies
- Drops reprints, customs, damaged, "lot of" listings
- Requires seller with 98%+ feedback and 25+ transactions
- Needs 3+ matched comps before a flip is shown

**Confidence score** weighs comp volume, seller reputation, and data quality.
Higher = less risk the "flip" is actually a mismatch.

**Tips:**
- Always verify the listing photos before buying
- Factor in ~13% eBay + PayPal fees
- Check return policy — good sellers accept returns
- Low confidence flips can still work, but do more homework
            """)
    else:
        st.warning("Select at least one sport to scan.")


render()
