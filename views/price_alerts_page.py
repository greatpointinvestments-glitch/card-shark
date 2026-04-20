"""Price Alerts page."""

import streamlit as st

from modules.ui_helpers import gradient_divider
from modules.price_alerts import add_alert, remove_alert, get_alerts
from modules.card_types import get_card_type_options
from modules.affiliates import ebay_search_affiliate_url
from tiers import can_access, render_upgrade_prompt


def render():
    st.title("🔔 Price Alerts")
    st.caption("Get notified when cards hit your target price")

    if not can_access("price_alerts"):
        render_upgrade_prompt("Price Alerts", "Set custom price targets and get notified when cards hit your buy/sell point.")
        st.stop()

    with st.form("add_alert_form", clear_on_submit=True):
        st.markdown("**Create New Alert**")
        al1, al2, al3 = st.columns(3)
        with al1:
            al_player = st.text_input("Player Name", placeholder="e.g. Jared McCain", key="al_player")
        with al2:
            al_sport = st.selectbox("Sport", ["NBA", "NFL", "MLB", "Pokemon"], key="al_sport")
        with al3:
            al_type_opt = st.selectbox("Card Type", get_card_type_options(), key="al_type")

        al4, al5, al6 = st.columns(3)
        with al4:
            al_direction = st.selectbox("Alert When", ["Below", "Above"], key="al_dir")
        with al5:
            al_price = st.number_input("Price Threshold ($)", min_value=0.01, step=1.0, key="al_price")
        with al6:
            al_note = st.text_input("Note (optional)", placeholder="e.g. Buy at dip", key="al_note")

        al_submit = st.form_submit_button("Create Alert", use_container_width=True)

    if al_submit and al_player and al_price > 0:
        add_alert(al_player, al_sport, al_type_opt, al_direction.lower(), al_price, al_note)
        st.success(f"Alert created for {al_player} {al_direction.lower()} ${al_price:.2f}")
        st.rerun()

    gradient_divider()

    alerts = get_alerts()

    if not alerts:
        st.info("No alerts set. Create your first alert above!")
    else:
        st.markdown(f"### Active Alerts ({len(alerts)})")

        for alert in alerts:
            ac1, ac2, ac3, ac4, ac5 = st.columns([3, 1.5, 1.5, 1.5, 0.5])
            with ac1:
                st.write(f"**{alert['player_name']}** ({alert['sport']}) — {alert['card_type']}")
            with ac2:
                direction_label = "drops below" if alert["alert_type"] == "below" else "rises above"
                st.write(f"{direction_label} ${alert['threshold_price']:.2f}")
            with ac3:
                if alert.get("last_price"):
                    st.write(f"Last: ${alert['last_price']:.2f}")
                else:
                    st.write("Last: —")
            with ac4:
                if alert.get("triggered"):
                    st.markdown('<span class="alert-triggered">TRIGGERED</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="alert-watching">WATCHING</span>', unsafe_allow_html=True)
            with ac5:
                if st.button("X", key=f"rm_al_{alert['id']}"):
                    remove_alert(alert["id"])
                    st.rerun()

            if alert.get("note"):
                st.caption(f"Note: {alert['note']}")

            # Triggered alert = highest intent moment — show buy link
            if alert.get("triggered"):
                buy_url = ebay_search_affiliate_url(
                    alert["player_name"], alert["sport"], alert.get("card_type", "")
                )
                st.markdown(
                    f'<div style="background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.3);'
                    f'border-radius:8px;padding:8px 14px;margin:4px 0 12px 0;">'
                    f'Your target price was hit. &nbsp;'
                    f'<a href="{buy_url}" target="_blank" class="ebay-btn">Buy Now on eBay</a>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


render()
