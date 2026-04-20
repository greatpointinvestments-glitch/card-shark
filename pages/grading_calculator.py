"""Grading Calculator page."""

import streamlit as st

from modules.ui_helpers import gradient_divider, score_progress_bar
from modules.grading_calculator import lookup_grading_prices, compute_grading_roi, compute_expected_value, GRADING_TIERS
from modules.card_types import get_card_type_options
from modules.psa_population import lookup_psa_population
from modules.affiliates import ebay_search_affiliate_url
from tiers import can_access, render_upgrade_prompt, render_disclaimer


def render():
    st.title("📐 Grading Calculator")
    st.caption("Should you send it to PSA? See if the profit is there before you spend.")
    render_disclaimer(compact=True)

    if not can_access("grading_calculator"):
        render_upgrade_prompt("Grading Calculator", "See the expected value of grading your cards before you spend $20+ per submission.")
        st.stop()

    gc1, gc2, gc3 = st.columns(3)
    with gc1:
        gc_player = st.text_input("Player Name", placeholder="e.g. Jared McCain", key="gc_player")
    with gc2:
        gc_sport = st.selectbox("Sport", ["NBA", "NFL", "MLB", "Pokemon"], key="gc_sport")
    with gc3:
        gc_type = st.selectbox("Card Type", get_card_type_options(), key="gc_type")

    gc4, gc5 = st.columns(2)
    with gc4:
        gc_year = st.text_input("Year", placeholder="e.g. 2023-24", key="gc_year")
    with gc5:
        gc_set = st.text_input("Set", placeholder="e.g. Prizm", key="gc_set")

    if not gc_player:
        return

    with st.spinner("Looking up raw and graded prices..."):
        prices = lookup_grading_prices(gc_player, gc_sport, gc_type,
                                       year=gc_year or None, set_name=gc_set or None)

    st.markdown("#### Market Prices")
    pm1, pm2, pm3, pm4 = st.columns(4)
    pm1.metric("Raw Card", f"${prices['raw_price']:.2f}", f"{prices['raw_count']} listings")
    pm2.metric("PSA 10", f"${prices['psa_10_price']:.2f}", f"{prices['psa_10_count']} listings")
    pm3.metric("PSA 9", f"${prices['psa_9_price']:.2f}", f"{prices['psa_9_count']} listings")
    pm4.metric("PSA 8", f"${prices['psa_8_price']:.2f}", f"{prices['psa_8_count']} listings")

    st.markdown("##### Manual Override")
    st.caption("Adjust prices if the auto-lookup isn't accurate for your specific card")
    ov1, ov2, ov3, ov4 = st.columns(4)
    with ov1:
        raw_override = st.number_input("Raw Price ($)", value=prices["raw_price"], min_value=0.0, step=1.0, key="gc_raw")
    with ov2:
        psa10_override = st.number_input("PSA 10 Price ($)", value=prices["psa_10_price"], min_value=0.0, step=1.0, key="gc_psa10")
    with ov3:
        psa9_override = st.number_input("PSA 9 Price ($)", value=prices["psa_9_price"], min_value=0.0, step=1.0, key="gc_psa9")
    with ov4:
        psa8_override = st.number_input("PSA 8 Price ($)", value=prices["psa_8_price"], min_value=0.0, step=1.0, key="gc_psa8")

    gradient_divider()
    st.markdown("#### ROI Breakdown")

    for grade_label, grade_price in [("PSA 10", psa10_override), ("PSA 9", psa9_override), ("PSA 8", psa8_override)]:
        st.markdown(f"##### If it grades {grade_label}")
        tier_cols = st.columns(3)
        best_roi = None
        for i, (tier_name, fee) in enumerate(GRADING_TIERS.items()):
            result = compute_grading_roi(raw_override, grade_price, fee)
            with tier_cols[i]:
                st.markdown(f"**{tier_name}**")
                st.write(f"Profit: ${result['profit']:.2f}")
                st.write(f"ROI: {result['roi_pct']:.1f}%")
                st.markdown(f'<span class="{result["verdict_css"]}">{result["verdict"]}</span>', unsafe_allow_html=True)
            if best_roi is None or result["roi_pct"] > best_roi["roi_pct"]:
                best_roi = {**result, "tier": tier_name, "grade": grade_label}

    with st.expander("PSA Population Data"):
        gc_psa = lookup_psa_population(gc_player)
        st.markdown(f'<span class="psa-badge">Total Pop: {gc_psa["total_pop"]:,}</span> '
                    f'<span class="psa-gem">Gem Rate: {gc_psa["gem_rate"]:.1f}%</span>',
                    unsafe_allow_html=True)
        gc_psa_cols = st.columns(min(len(gc_psa["grade_distribution"]), 8))
        for i, (grade, count) in enumerate(sorted(gc_psa["grade_distribution"].items(), key=lambda x: -int(x[0]))):
            if i < 8:
                with gc_psa_cols[i]:
                    st.metric(f"PSA {grade}", f"{count:,}")
        if gc_psa.get("source") == "demo":
            st.caption("Sample data — connect PSA API for live population reports")

    gradient_divider()
    st.markdown("#### Expected Value Analysis")
    st.caption("Adjust the probability sliders — defaults set from PSA population gem rates")

    gc_pop = gc_psa.get("grade_distribution", {})
    gc_pop_total = sum(gc_pop.values()) if gc_pop else 1
    default_p10 = int(gc_pop.get("10", 0) / gc_pop_total * 100) if gc_pop_total else 20
    default_p9 = int(gc_pop.get("9", 0) / gc_pop_total * 100) if gc_pop_total else 50
    default_p8 = int(gc_pop.get("8", 0) / gc_pop_total * 100) if gc_pop_total else 30

    ev_c1, ev_c2, ev_c3 = st.columns(3)
    with ev_c1:
        prob_10_raw = st.slider("PSA 10 Chance (%)", 0, 100, default_p10, key="ev_p10")
    with ev_c2:
        prob_9_raw = st.slider("PSA 9 Chance (%)", 0, 100, default_p9, key="ev_p9")
    with ev_c3:
        prob_8_raw = st.slider("PSA 8 Chance (%)", 0, 100, default_p8, key="ev_p8")

    raw_total = prob_10_raw + prob_9_raw + prob_8_raw
    if raw_total > 0:
        prob_10 = prob_10_raw / raw_total
        prob_9 = prob_9_raw / raw_total
        prob_8 = prob_8_raw / raw_total
    else:
        prob_10, prob_9, prob_8 = 0.33, 0.34, 0.33

    st.caption(f"Normalized: PSA 10 = {prob_10:.0%} | PSA 9 = {prob_9:.0%} | PSA 8 = {prob_8:.0%}")

    gc_tier = st.selectbox("Grading Tier", list(GRADING_TIERS.keys()), key="ev_tier")
    gc_fee = GRADING_TIERS[gc_tier]

    ev_result = compute_expected_value(
        raw_override, psa10_override, psa9_override, psa8_override,
        gc_fee, prob_10, prob_9, prob_8
    )

    evm1, evm2, evm3, evm4 = st.columns(4)
    evm1.metric("Expected Graded Value", f"${ev_result['expected_graded']:.2f}")
    evm2.metric("Expected Profit", f"${ev_result['expected_profit']:.2f}")
    evm3.metric("EV ROI", f"{ev_result['ev_roi_pct']:.1f}%")
    evm4.metric("Break-Even Grade", ev_result["break_even_grade"])

    st.markdown("**Per-Grade Contribution:**")
    dg1, dg2, dg3 = st.columns(3)
    for col, grade in zip([dg1, dg2, dg3], ["PSA 10", "PSA 9", "PSA 8"]):
        d = ev_result["details"][grade]
        with col:
            st.write(f"**{grade}** ({d['prob']:.0%} chance)")
            st.write(f"Price: ${d['price']:.2f}")
            st.write(f"Weighted EV: ${d['ev']:.2f}")

    gradient_divider()
    st.markdown("#### Verdict")
    st.markdown(
        f'<span class="{ev_result["verdict_css"]}" style="font-size:1.3em">'
        f'{ev_result["verdict"]} — {ev_result["ev_roi_pct"]:.0f}% Expected ROI</span>',
        unsafe_allow_html=True
    )
    if ev_result["break_even_grade"] != "None":
        st.caption(f"You break even if it grades {ev_result['break_even_grade']} or better with {gc_tier} grading.")
    else:
        st.caption("No grade covers the cost at current prices. Keep it raw.")

    # Affiliate links — buy raw or graded versions
    gradient_divider()
    gc_buy1, gc_buy2, gc_buy3 = st.columns(3)
    with gc_buy1:
        raw_url = ebay_search_affiliate_url(gc_player, gc_sport, gc_type)
        st.markdown(
            f'<a href="{raw_url}" target="_blank" class="ebay-btn" '
            f'style="display:block;text-align:center;padding:8px;">Shop Raw Cards</a>',
            unsafe_allow_html=True,
        )
    with gc_buy2:
        psa10_url = ebay_search_affiliate_url(gc_player, gc_sport, "PSA 10")
        st.markdown(
            f'<a href="{psa10_url}" target="_blank" class="ebay-btn" '
            f'style="display:block;text-align:center;padding:8px;">Shop PSA 10</a>',
            unsafe_allow_html=True,
        )
    with gc_buy3:
        psa9_url = ebay_search_affiliate_url(gc_player, gc_sport, "PSA 9")
        st.markdown(
            f'<a href="{psa9_url}" target="_blank" class="ebay-btn" '
            f'style="display:block;text-align:center;padding:8px;">Shop PSA 9</a>',
            unsafe_allow_html=True,
        )


render()
