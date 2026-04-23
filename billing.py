"""Stripe billing — checkout sessions and subscription management."""

import json
import os
import tempfile
from datetime import datetime

import streamlit as st

from config.settings import (
    STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY,
    STRIPE_PRICE_MONTHLY, STRIPE_PRICE_YEARLY, STRIPE_PRICE_LIFETIME,
    STRIPE_PRICE_MONTHLY_DISCOUNT, STRIPE_PRICE_YEARLY_DISCOUNT,
    PRO_PRICE_MONTHLY, PRO_PRICE_YEARLY, PRO_PRICE_LIFETIME,
    ABANDON_COUPON_CODE, ABANDON_COUPON_DISCOUNT_PCT, ABANDON_TRIGGER_VISITS,
    LIFETIME_DEAL_CAP,
)


_LIFETIME_COUNTER_PATH = os.path.join(os.path.dirname(__file__), "data", "lifetime_sold.json")


def stripe_is_configured() -> bool:
    """Check if Stripe keys are set."""
    return bool(STRIPE_SECRET_KEY and STRIPE_PRICE_MONTHLY)


def lifetime_spots_remaining() -> int:
    """Return how many LTD spots are left."""
    if not os.path.exists(_LIFETIME_COUNTER_PATH):
        return LIFETIME_DEAL_CAP
    try:
        with open(_LIFETIME_COUNTER_PATH, "r") as f:
            data = json.load(f)
        sold = int(data.get("sold", 0))
        return max(0, LIFETIME_DEAL_CAP - sold)
    except (json.JSONDecodeError, IOError, ValueError):
        return LIFETIME_DEAL_CAP


def increment_lifetime_sold() -> None:
    """Increment the LTD sold counter. Called by webhook/success handler."""
    os.makedirs(os.path.dirname(_LIFETIME_COUNTER_PATH), exist_ok=True)
    sold = 0
    if os.path.exists(_LIFETIME_COUNTER_PATH):
        try:
            with open(_LIFETIME_COUNTER_PATH, "r") as f:
                sold = int(json.load(f).get("sold", 0))
        except (json.JSONDecodeError, IOError, ValueError):
            sold = 0
    fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(_LIFETIME_COUNTER_PATH), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump({"sold": sold + 1, "updated_at": datetime.now().isoformat()}, f)
        os.replace(tmp_path, _LIFETIME_COUNTER_PATH)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _track_upgrade_visit() -> int:
    """Increment the session upgrade-page visit counter. Returns visit count."""
    st.session_state["_upgrade_visits"] = st.session_state.get("_upgrade_visits", 0) + 1
    return st.session_state["_upgrade_visits"]


def should_show_abandon_coupon() -> bool:
    """After N upgrade-page visits without a purchase, unlock the discount coupon."""
    return st.session_state.get("_upgrade_visits", 0) >= ABANDON_TRIGGER_VISITS


def create_checkout_url(plan: str, username: str, use_discount: bool = False) -> str | None:
    """Create a Stripe Checkout Session and return the URL.

    plan: 'monthly', 'yearly', or 'lifetime'
    use_discount: apply abandoned-checkout coupon
    """
    if not stripe_is_configured():
        return None

    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
    except ImportError:
        return None

    if plan == "lifetime":
        price_id = STRIPE_PRICE_LIFETIME
        mode = "payment"
    elif plan == "yearly":
        price_id = STRIPE_PRICE_YEARLY_DISCOUNT if use_discount and STRIPE_PRICE_YEARLY_DISCOUNT else STRIPE_PRICE_YEARLY
        mode = "subscription"
    else:
        price_id = STRIPE_PRICE_MONTHLY_DISCOUNT if use_discount and STRIPE_PRICE_MONTHLY_DISCOUNT else STRIPE_PRICE_MONTHLY
        mode = "subscription"

    if not price_id:
        st.error("This plan is not configured yet.")
        return None

    try:
        # Determine base URL for success/cancel (fall back to cardhawkapp.com in prod)
        base_url = st.session_state.get("_base_url", "https://cardhawkapp.com")
        session = stripe.checkout.Session.create(
            mode=mode,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{base_url}/?upgrade=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/?upgrade=cancel",
            client_reference_id=username,
            metadata={"username": username, "plan": plan, "discount": str(use_discount)},
        )
        return session.url
    except Exception as e:
        st.error(f"Payment setup failed: {e}")
        return None


def verify_and_activate_subscription(session_id: str) -> tuple[bool, str, dict | None]:
    """Verify a Stripe Checkout Session completed successfully and return details.

    Returns (success, message, session_data). session_data includes username,
    plan, subscription_id, customer_id.
    """
    if not stripe_is_configured():
        return False, "Stripe not configured", None

    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
    except ImportError:
        return False, "Stripe SDK unavailable", None

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        return False, f"Could not verify checkout session: {e}", None

    if session.get("payment_status") not in ("paid", "no_payment_required"):
        return False, "Payment not completed", None

    metadata = session.get("metadata") or {}
    username = session.get("client_reference_id") or metadata.get("username")
    plan = metadata.get("plan", "monthly")

    if not username:
        return False, "Missing username on checkout session", None

    return True, "Verified", {
        "username": username,
        "plan": plan,
        "subscription_id": session.get("subscription"),
        "customer_id": session.get("customer"),
        "mode": session.get("mode"),
    }


def handle_stripe_return(query_params: dict) -> None:
    """Handle redirect from Stripe Checkout. Updates user tier if payment verified.
    Call this early in app.py when query params contain ?upgrade=success&session_id=..."""
    session_id = query_params.get("session_id")
    if not session_id:
        st.warning("Missing session identifier — if you were charged, contact support.")
        return

    ok, msg, data = verify_and_activate_subscription(session_id)
    if not ok or not data:
        st.error(f"Couldn't confirm your payment: {msg}. If you were charged, email hello@cardhawkapp.com with your receipt.")
        return

    # Sanity: ensure session user matches who's logged in
    current = st.session_state.get("username")
    if current and current != data["username"]:
        st.warning("Logged-in user doesn't match the checkout account. Log in as the purchasing account to activate Pro.")
        return

    from auth import update_user_tier, get_user_info, effective_tier
    new_tier = "pro_lifetime" if data["plan"] == "lifetime" else "pro"
    update_user_tier(data["username"], new_tier, data.get("subscription_id"))

    if data["plan"] == "lifetime":
        increment_lifetime_sold()

    # Refresh session tier
    user_info = get_user_info(data["username"])
    st.session_state.user_tier = effective_tier(user_info)

    st.success(f"Welcome to Pro! Your {data['plan']} plan is active. Thanks for supporting CardHawk.")
    st.balloons()


def _savings_badge(monthly: float, yearly: float) -> str:
    """Dollar savings for paying annually vs monthly."""
    return f"${int(monthly * 12 - yearly)}"


def render_pricing_page():
    """Render the Pro upgrade / pricing page."""
    _track_upgrade_visit()
    show_coupon = should_show_abandon_coupon()
    lifetime_left = lifetime_spots_remaining()
    username = st.session_state.get("username")
    annual_savings = _savings_badge(PRO_PRICE_MONTHLY, PRO_PRICE_YEARLY)

    st.title("Upgrade to Pro")
    st.markdown("#### One good flip pays for a year.")

    # Lifetime deal urgency banner
    if lifetime_left > 0 and lifetime_left <= LIFETIME_DEAL_CAP:
        pct_sold = int(((LIFETIME_DEAL_CAP - lifetime_left) / LIFETIME_DEAL_CAP) * 100)
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#7c2d12,#991b1b);'
            f'color:white;padding:14px 18px;border-radius:10px;margin:10px 0;'
            f'display:flex;justify-content:space-between;align-items:center;">'
            f'<span><strong>Lifetime Launch Deal</strong> — '
            f'${PRO_PRICE_LIFETIME:.0f} one-time. Never pay again.</span>'
            f'<span style="background:#fbbf24;color:#1f2937;padding:6px 12px;'
            f'border-radius:6px;font-weight:bold;">'
            f'Only {lifetime_left} of {LIFETIME_DEAL_CAP} left</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Abandoned-checkout coupon
    if show_coupon:
        st.markdown(
            f'<div style="background:#fef3c7;border-left:4px solid #f59e0b;'
            f'color:#78350f;padding:12px 16px;border-radius:6px;margin:10px 0;">'
            f'<strong>Still thinking?</strong> Use code <code>{ABANDON_COUPON_CODE}</code> '
            f'for {ABANDON_COUPON_DISCOUNT_PCT}% off your first year. Applied automatically below.'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    col_free, col_pro = st.columns(2)

    with col_free:
        st.markdown("### Free")
        st.markdown("**$0 / forever**")
        st.markdown("""
- Unlimited card scanning
- Player search (10/day)
- Breakout leaderboard (top 10)
- Portfolio tracker (25 cards)
- Trade checker (3/day)
- Live games
- Legend cards (view only)
        """)

    with col_pro:
        st.markdown("### Pro &nbsp; <span class='best-value-badge'>BEST VALUE</span>", unsafe_allow_html=True)
        yearly_per_month_display = PRO_PRICE_YEARLY / 12
        st.markdown(
            f'<div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;">'
            f'<span style="font-size:1.6em;font-weight:bold;">${PRO_PRICE_MONTHLY}/mo</span>'
            f'<span style="color:#6b7280;">or</span>'
            f'<span style="font-size:1.3em;font-weight:bold;">${PRO_PRICE_YEARLY}/yr</span>'
            f'<span style="background:#10b981;color:white;padding:3px 8px;'
            f'border-radius:4px;font-weight:bold;font-size:0.85em;">'
            f'Save {annual_savings}/year</span>'
            f'</div>'
            f'<p style="color:#9ca3af;font-size:0.9em;margin-top:4px;">'
            f'That\'s just ${yearly_per_month_display:.2f}/mo billed annually</p>',
            unsafe_allow_html=True,
        )
        st.markdown("""
- **Everything in Free, plus:**
- Unlimited searches, trades, portfolio
- Flip Finder (arbitrage scanner)
- Market Movers (weekly gainers/losers)
- Grading Calculator with EV analysis
- Player Comparison tool
- Price Alerts with notifications
- Live price history (real eBay data)
- PSA Population data
- CSV export
        """)

        if not username:
            st.warning("Log in or create an account to upgrade.")
        elif stripe_is_configured():
            yearly_per_month = PRO_PRICE_YEARLY / 12
            plan_options = [f"Yearly — ${PRO_PRICE_YEARLY} (BEST VALUE — save {annual_savings})", f"Monthly — ${PRO_PRICE_MONTHLY}"]
            if STRIPE_PRICE_LIFETIME and lifetime_left > 0:
                plan_options.append(f"Lifetime — ${PRO_PRICE_LIFETIME:.0f} one-time")
            plan_choice = st.radio(
                "Billing", plan_options, index=0, horizontal=False, key="plan_choice",
            )
            if "Lifetime" in plan_choice:
                plan = "lifetime"
            elif "Yearly" in plan_choice:
                plan = "yearly"
            else:
                plan = "monthly"

            cta_label = "Claim Lifetime Deal" if plan == "lifetime" else "Start Subscription"
            if st.button(cta_label, type="primary", use_container_width=True):
                url = create_checkout_url(plan, username, use_discount=show_coupon and plan != "lifetime")
                if url:
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={url}">', unsafe_allow_html=True)
                    st.info("Redirecting to secure checkout...")
            st.caption("Cancel anytime. Secure checkout by Stripe.")
        else:
            st.info("Stripe payments are not yet configured. Pro features will be available soon!")
            st.caption("Contact support to get early Pro access.")
