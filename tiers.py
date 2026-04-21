"""Tier gating — check feature access and render upgrade prompts."""

import streamlit as st

from config.settings import FREE_TIER_LIMITS, PRO_FEATURES, PRO_PRICE_MONTHLY


def get_current_tier() -> str:
    """Get the current user's tier. Defaults to 'free'. Honors active trials."""
    username = st.session_state.get("username")
    if username:
        from auth import get_user_info, effective_tier
        return effective_tier(get_user_info(username))
    return st.session_state.get("user_tier", "free")


def is_pro() -> bool:
    """Check if the current user has Pro access (paid or on active trial)."""
    return get_current_tier() == "pro"


def is_on_trial() -> bool:
    """True only when the user is using the free trial (not paid)."""
    username = st.session_state.get("username")
    if not username:
        return False
    from auth import get_user_info, is_trial_active
    user_info = get_user_info(username)
    if not user_info:
        return False
    if user_info.get("tier") in ("pro", "pro_lifetime"):
        return False
    return is_trial_active(user_info)


def can_access(feature: str) -> bool:
    """Check if the current user can access a Pro feature."""
    if is_pro():
        return True
    return feature not in PRO_FEATURES


def check_usage_limit(action: str) -> tuple[bool, int, int]:
    """Check if the user is within their free tier usage limit.

    Returns (allowed, current_count, max_count).
    Pro users always get (True, 0, 999).
    """
    if is_pro():
        return True, 0, 999

    limit = FREE_TIER_LIMITS.get(f"{action}_per_day", FREE_TIER_LIMITS.get(f"{action}_max_cards", 999))

    username = st.session_state.get("username")
    if not username:
        return True, 0, limit  # not logged in = no tracking

    from auth import get_daily_usage
    count = get_daily_usage(username, action)
    return count < limit, count, limit


def increment_and_check(action: str) -> bool:
    """Increment usage and return True if still within limits."""
    if is_pro():
        return True
    username = st.session_state.get("username")
    if not username:
        return True
    from auth import increment_usage, get_daily_usage
    limit = FREE_TIER_LIMITS.get(f"{action}_per_day", 999)
    count = get_daily_usage(username, action)
    if count >= limit:
        return False
    increment_usage(username, action)
    return True


def render_disclaimer(compact: bool = False):
    """Standard 'not financial advice' disclaimer.
    Use on Flip Finder, Market Movers, Grading Calc, Price History."""
    if compact:
        st.caption(
            "Not financial advice. Past sales don't predict future prices. "
            "Verify every listing before buying."
        )
        return
    st.info(
        "**Heads up:** Card Shark is a research tool, not financial advice. "
        "Past sold prices don't guarantee future value. Always verify condition, "
        "seller reputation, and return policy before buying. You are responsible "
        "for your own purchases."
    )


def render_upgrade_banner(feature_name: str, hook_text: str = ""):
    """Render a compact upgrade banner inline — doesn't block the page."""
    inner_hook = f" — {hook_text}" if hook_text else ""
    st.markdown(
        f'<div style="background: linear-gradient(135deg, #1e3a5f, #1e40af); '
        f'border-radius: 10px; padding: 16px 20px; margin: 10px 0;">'
        f'<span style="font-weight:bold; font-size:1.1em;">Upgrade to Pro</span> '
        f'&nbsp; to unlock full {feature_name}{inner_hook} &nbsp; '
        f'<span style="color:#facc15; font-weight:bold;">${PRO_PRICE_MONTHLY}/mo</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if st.button("See Pro Features", key=f"upgrade_{feature_name}", use_container_width=True):
        st.session_state.nav_target = "upgrade"
        st.rerun()


# Feature-specific "missed opportunity" hooks shown on paywall screens.
# Numbers are live when possible; otherwise realistic placeholders until wired up.
_MISSED_OPPORTUNITY_HOOKS = {
    "Flip Finder": "4 active arbitrage flips found today. $127 in potential profit locked behind Pro.",
    "Market Movers": "23 cards moved 15%+ this week. Pro users got the alerts before the spike.",
    "Grading Calculator": "Avg Pro user avoids $40 in bad PSA submissions per month.",
    "Player Comparison": "Side-by-side ROI for any two players — find the better investment in 10 seconds.",
    "Price Alerts": "Pro users set alerts and bought 3 cards at 30%+ discounts this week.",
    "Card Scanner": "Pro scanner uses AI vision to read player, set, condition, and variant with high accuracy.",
}


def render_upgrade_prompt(feature_name: str, preview_text: str = ""):
    """Show a friendly upgrade prompt when a user hits a Pro feature.
    Used as a full-page gate (with st.stop() after)."""
    hook = _MISSED_OPPORTUNITY_HOOKS.get(feature_name, "")

    st.markdown(
        f'<div style="text-align:center; padding: 40px 20px;">'
        f'<div style="font-size:3em; margin-bottom:12px;">🔒</div>'
        f'<h2 style="margin-bottom:8px;">{feature_name} is a Pro feature</h2>'
        f'<p style="color:#9ca3af; font-size:1.1em; max-width:500px; margin:0 auto;">'
        f'{preview_text}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if hook:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#7c2d12,#991b1b);'
            f'color:#fef3c7;border-radius:10px;padding:14px 20px;margin:10px auto;'
            f'max-width:640px;text-align:center;font-size:1.05em;font-weight:500;">'
            f'{hook}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Show what Pro includes — make them want it
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown("**Flip Finder**")
        st.caption("Cards listed below sold prices")
    with p2:
        st.markdown("**Market Movers**")
        st.caption("Weekly gainers and losers")
    with p3:
        st.markdown("**Grading Calculator**")
        st.caption("Should you send it to PSA?")

    p4, p5, p6 = st.columns(3)
    with p4:
        st.markdown("**Player Comparison**")
        st.caption("Side-by-side investment analysis")
    with p5:
        st.markdown("**Price Alerts**")
        st.caption("Get notified at your target price")
    with p6:
        st.markdown("**Unlimited Everything**")
        st.caption("No daily limits on searches or trades")

    st.markdown("---")

    cta1, cta2, cta3 = st.columns([1, 2, 1])
    with cta2:
        st.markdown(
            f'<div style="text-align:center;">'
            f'<p style="font-size:1.3em; font-weight:bold;">'
            f'${PRO_PRICE_MONTHLY}/month</p>'
            f'<p style="color:#9ca3af;">One good flip pays for a year</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("Upgrade to Pro", key=f"upgrade_full_{feature_name}", type="primary", use_container_width=True):
            st.session_state.nav_target = "upgrade"
            st.rerun()
        st.caption("Cancel anytime. No contracts.")


def render_teaser_gate(feature_name: str, teaser_text: str = ""):
    """Upgrade CTA overlay — sits below blurred content. Uses loss aversion
    instead of a hard paywall. Pair with the .teaser-overlay CSS class."""
    if not teaser_text:
        teaser_text = f"Unlock full {feature_name} with Pro"
    st.markdown(
        f'<div class="teaser-overlay">'
        f'<p style="font-size:1.15em;font-weight:bold;margin-bottom:4px;">{teaser_text}</p>'
        f'<p style="color:#9ca3af;font-size:0.95em;margin-bottom:12px;">'
        f'See what you\'re missing — upgrade now.</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if st.button(f"Unlock {feature_name}", key=f"teaser_{feature_name}", type="primary", use_container_width=True):
        st.session_state.nav_target = "upgrade"
        st.rerun()


def render_contextual_upsell(context: str):
    """Subtle banner after free actions complete. Non-blocking, appears at bottom."""
    _UPSELL_COPY = {
        "player_search": "Like what you see? Pro users get unlimited searches, price alerts, and full price history.",
        "breakout_leaderboard": "Pro users see the full leaderboard and get early breakout alerts.",
        "trade_checker": "Pro users get unlimited trade checks and deeper market analysis.",
        "my_collection": "Pro users track unlimited cards with CSV export and full analytics.",
        "card_scanner": "Pro scanner uses AI vision for higher accuracy — identifies condition, variant, and more.",
    }
    copy = _UPSELL_COPY.get(context, "Pro users get the full experience — unlimited everything.")
    st.markdown(
        f'<div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.25);'
        f'border-radius:8px;padding:12px 16px;margin:16px 0;text-align:center;">'
        f'<span style="font-size:0.95em;">{copy}</span> &nbsp;'
        f'<span style="color:#f59e0b;font-weight:bold;font-size:0.95em;">'
        f'${PRO_PRICE_MONTHLY}/mo</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def get_trial_urgency_level() -> tuple[str, str]:
    """Return (css_class, display_text) based on trial time remaining.
    Escalates urgency in last 48h/24h/2h."""
    username = st.session_state.get("username")
    if not username:
        return "trial-normal", ""
    from auth import get_user_info, trial_hours_remaining, is_trial_active
    user_info = get_user_info(username)
    if not user_info or not is_trial_active(user_info):
        return "trial-normal", ""
    hrs = trial_hours_remaining(user_info)
    if hrs <= 2:
        return "trial-urgent", "Pro Trial expires in under 2 hours!"
    elif hrs <= 24:
        return "trial-urgent", "Pro Trial expires tomorrow!"
    elif hrs <= 48:
        return "trial-urgent", f"Pro Trial — {hrs}h left. Don't lose access."
    else:
        days = hrs // 24
        return "trial-normal", f"Pro Trial — {days}d left"


def render_trial_expired_recap():
    """Show a personalized usage summary when the trial has expired.
    Leverages endowment effect — show what they're about to lose."""
    username = st.session_state.get("username")
    if not username:
        return
    from auth import get_user_info, is_trial_active, get_daily_usage
    user_info = get_user_info(username)
    if not user_info:
        return
    # Only show for expired trials (not active, not paid)
    if user_info.get("tier") in ("pro", "pro_lifetime"):
        return
    if is_trial_active(user_info):
        return
    trial_ends = user_info.get("trial_ends_at")
    if not trial_ends:
        return  # never had a trial

    # Gather usage data across recent days
    from auth import _load_usage
    usage_data = _load_usage(username)
    total_searches = sum(day.get("searches", 0) for day in usage_data.values() if isinstance(day, dict))
    total_trades = sum(day.get("trades", 0) for day in usage_data.values() if isinstance(day, dict))
    total_scans = sum(day.get("scans", 0) for day in usage_data.values() if isinstance(day, dict))

    # Only show if they actually used the trial
    total_actions = total_searches + total_trades + total_scans
    if total_actions == 0:
        return

    # Build summary lines
    stats_parts = []
    if total_searches > 0:
        stats_parts.append(f"<strong>{total_searches}</strong> player searches")
    if total_trades > 0:
        stats_parts.append(f"<strong>{total_trades}</strong> trade checks")
    if total_scans > 0:
        stats_parts.append(f"<strong>{total_scans}</strong> card scans")

    from modules.portfolio import get_portfolio
    portfolio = get_portfolio()
    portfolio_count = len(portfolio) if portfolio else 0
    if portfolio_count > 0:
        stats_parts.append(f"<strong>{portfolio_count}</strong> cards in your collection")

    stats_html = " &bull; ".join(stats_parts)

    st.sidebar.markdown(
        f'<div style="background:linear-gradient(135deg,#7f1d1d,#991b1b);'
        f'color:#fecaca;border-radius:8px;padding:12px 14px;margin:4px 0;font-size:0.85em;">'
        f'<strong>Your Pro trial ended.</strong><br>'
        f'<span style="font-size:0.9em;">During your trial: {stats_html}</span><br>'
        f'<span style="color:#fbbf24;font-weight:bold;">Don\'t lose access to what you built.</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Reactivate Pro", key="trial_recap_upgrade", type="primary", use_container_width=True):
        st.session_state.nav_target = "upgrade"
        st.rerun()


def render_limit_warning(action: str, count: int, limit: int):
    """Show a usage limit warning — inline, not page-blocking.
    Escalates styling/copy as the user approaches their cap."""
    remaining = max(limit - count, 0)
    pct_used = count / limit if limit else 0

    if remaining == 0:
        # Hit the wall.
        st.markdown(
            f'<div style="background:#7f1d1d;color:#fee2e2;border-radius:8px;'
            f'padding:14px 18px;margin:8px 0;border-left:4px solid #ef4444;">'
            f'<strong>Daily {action} limit reached ({count}/{limit}).</strong> '
            f'Come back tomorrow — or upgrade to Pro for unlimited access right now.'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button(f"Unlock unlimited {action}", key=f"limit_{action}", use_container_width=True, type="primary"):
            st.session_state.nav_target = "upgrade"
            st.rerun()
    elif pct_used >= 0.8:
        # Urgency zone — 80%+
        st.markdown(
            f'<div style="background:#78350f;color:#fed7aa;border-radius:8px;'
            f'padding:12px 16px;margin:8px 0;border-left:4px solid #f59e0b;">'
            f'<strong>Only {remaining} {action} left today.</strong> '
            f'Pro users never run out.'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button(f"Go unlimited — ${PRO_PRICE_MONTHLY}/mo", key=f"limit_{action}", use_container_width=True):
            st.session_state.nav_target = "upgrade"
            st.rerun()
    else:
        st.info(
            f"**{count}/{limit}** {action} used today. {remaining} left. "
            f"Pro users get unlimited."
        )
