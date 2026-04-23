"""Authentication & user management for CardHawk."""

import json
import os
import hashlib
import re
import tempfile
import uuid
from datetime import datetime, timedelta

import bcrypt

TRIAL_DAYS = 7

import streamlit as st

# User data directory
_USERS_DIR = os.path.join(os.path.dirname(__file__), "data", "users")
_USERS_DB = os.path.join(os.path.dirname(__file__), "data", "users.json")


def _safe_json_load(path: str, default_factory=dict):
    """Load JSON with corruption detection. Backs up corrupt files."""
    if not os.path.exists(path):
        return default_factory()
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        backup = path + ".corrupt"
        try:
            os.replace(path, backup)
        except OSError:
            pass
        return default_factory()
    except IOError:
        return default_factory()


def _load_users() -> dict:
    """Load the user database."""
    return _safe_json_load(_USERS_DB, dict)


def _atomic_json_write(path: str, data) -> None:
    """Write JSON atomically: write to temp file, then os.replace()."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _save_users(users: dict) -> None:
    """Save the user database."""
    _atomic_json_write(_USERS_DB, users)


_LEGACY_SALT = "cardshark_2024"

# Login rate limiting: {username: (fail_count, lockout_until)}
_login_attempts: dict[str, tuple[int, datetime]] = {}
_MAX_LOGIN_ATTEMPTS = 5
_LOCKOUT_MINUTES = 15


def _hash_password(password: str) -> str:
    """Hash a password with bcrypt (per-user salt, modern cost factor)."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def _legacy_hash(password: str) -> str:
    """Old SHA-256 hash — retained only to verify + upgrade existing accounts."""
    return hashlib.sha256(f"{_LEGACY_SALT}{password}".encode()).hexdigest()


def _verify_password(password: str, stored: str) -> tuple[bool, bool]:
    """Return (is_valid, needs_rehash).
    If the stored hash is bcrypt, verify normally.
    If it's the old SHA-256 format, verify legacy and signal a rehash is needed.
    """
    if not stored:
        return False, False
    # bcrypt hashes always start with $2a$ / $2b$ / $2y$
    if stored.startswith("$2"):
        try:
            return bcrypt.checkpw(password.encode(), stored.encode()), False
        except ValueError:
            return False, False
    # Legacy SHA-256 — 64 hex chars
    if len(stored) == 64 and all(c in "0123456789abcdef" for c in stored.lower()):
        return stored == _legacy_hash(password), True
    return False, False


def _get_user_dir(username: str) -> str:
    """Get the data directory for a specific user."""
    user_dir = os.path.join(_USERS_DIR, username)
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_-]{3,32}$")


def signup(username: str, email: str, password: str) -> tuple[bool, str]:
    """Create a new user account. Returns (success, message)."""
    if not _USERNAME_RE.match(username):
        return False, "Username must be 3-32 characters: letters, numbers, _ or - only"

    users = _load_users()

    if username.lower() in {u.lower() for u in users}:
        return False, "Username already taken"
    if any(u.get("email", "").lower() == email.lower() for u in users.values()):
        return False, "Email already registered"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"

    trial_ends = (datetime.now() + timedelta(days=TRIAL_DAYS)).isoformat()
    users[username] = {
        "email": email,
        "password_hash": _hash_password(password),
        "tier": "free",
        "trial_ends_at": trial_ends,
        "created_at": datetime.now().isoformat(),
        "stripe_customer_id": None,
        "stripe_subscription_id": None,
    }
    _save_users(users)
    _get_user_dir(username)  # create their data directory
    return True, "Account created!"


def login(username: str, password: str) -> tuple[bool, str]:
    """Authenticate a user. Returns (success, message).
    Auto-upgrades legacy SHA-256 hashes to bcrypt on successful login."""
    # Rate limiting check
    attempts = _login_attempts.get(username)
    if attempts:
        fail_count, lockout_until = attempts
        if fail_count >= _MAX_LOGIN_ATTEMPTS and datetime.now() < lockout_until:
            mins_left = max(1, int((lockout_until - datetime.now()).total_seconds() // 60))
            return False, f"Too many failed attempts. Try again in {mins_left} minutes."

    users = _load_users()
    user = users.get(username)
    if not user:
        _record_failed_login(username)
        return False, "Invalid username or password"

    valid, needs_rehash = _verify_password(password, user.get("password_hash", ""))
    if not valid:
        _record_failed_login(username)
        return False, "Invalid username or password"

    # Success — clear rate limit and rehash if needed
    _login_attempts.pop(username, None)

    if needs_rehash:
        user["password_hash"] = _hash_password(password)
        users[username] = user
        _save_users(users)

    return True, "Welcome back!"


def _record_failed_login(username: str) -> None:
    """Track a failed login attempt."""
    attempts = _login_attempts.get(username)
    if attempts:
        fail_count, lockout_until = attempts
        if datetime.now() >= lockout_until:
            fail_count = 0  # lockout expired, reset
        fail_count += 1
    else:
        fail_count = 1
    _login_attempts[username] = (fail_count, datetime.now() + timedelta(minutes=_LOCKOUT_MINUTES))


def get_user_info(username: str) -> dict | None:
    """Get user profile info."""
    users = _load_users()
    return users.get(username)


def is_trial_active(user_info: dict | None) -> bool:
    """Return True if the user has an active 7-day Pro trial."""
    if not user_info:
        return False
    ends = user_info.get("trial_ends_at")
    if not ends:
        return False
    try:
        return datetime.now() < datetime.fromisoformat(ends)
    except (ValueError, TypeError):
        return False


def trial_hours_remaining(user_info: dict | None) -> int:
    """Hours remaining on the trial. 0 if expired or no trial."""
    if not user_info:
        return 0
    ends = user_info.get("trial_ends_at")
    if not ends:
        return 0
    try:
        delta = datetime.fromisoformat(ends) - datetime.now()
        return max(0, int(delta.total_seconds() // 3600))
    except (ValueError, TypeError):
        return 0


def effective_tier(user_info: dict | None) -> str:
    """Return 'pro' if paid or trial active, else 'free'."""
    if not user_info:
        return "free"
    tier = user_info.get("tier", "free")
    if tier in ("pro", "pro_lifetime"):
        return "pro"
    if is_trial_active(user_info):
        return "pro"
    return "free"


def update_user_tier(username: str, tier: str, stripe_sub_id: str | None = None) -> bool:
    """Update a user's subscription tier."""
    users = _load_users()
    if username not in users:
        return False
    users[username]["tier"] = tier
    if stripe_sub_id:
        users[username]["stripe_subscription_id"] = stripe_sub_id
    _save_users(users)
    return True


def get_user_portfolio_path(username: str) -> str:
    """Get the portfolio JSON path for a specific user."""
    return os.path.join(_get_user_dir(username), "portfolio.json")


def get_user_alerts_path(username: str) -> str:
    """Get the alerts JSON path for a specific user."""
    return os.path.join(_get_user_dir(username), "alerts.json")


def get_user_usage_path(username: str) -> str:
    """Get the daily usage counters path for a specific user."""
    return os.path.join(_get_user_dir(username), "usage.json")


# --- Usage Tracking ---

def _load_usage(username: str) -> dict:
    """Load daily usage counters for a user."""
    return _safe_json_load(get_user_usage_path(username), dict)


def _save_usage(username: str, usage: dict) -> None:
    """Save daily usage counters."""
    _atomic_json_write(get_user_usage_path(username), usage)


def get_daily_usage(username: str, action: str) -> int:
    """Get today's count for a specific action (e.g. 'searches', 'trades')."""
    usage = _load_usage(username)
    today = datetime.now().strftime("%Y-%m-%d")
    return usage.get(today, {}).get(action, 0)


def increment_usage(username: str, action: str) -> int:
    """Increment today's count for an action. Returns the new count."""
    usage = _load_usage(username)
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in usage:
        usage[today] = {}
    if action not in usage[today]:
        usage[today][action] = 0
    usage[today][action] += 1
    _save_usage(username, usage)
    return usage[today][action]


# --- Streamlit Auth UI ---

def render_auth_ui() -> str | None:
    """Render login/signup UI in sidebar. Returns username if logged in, None otherwise."""
    if "username" in st.session_state and st.session_state.username:
        # Already logged in — compact display
        user_info = get_user_info(st.session_state.username)
        paid = user_info and user_info.get("tier") in ("pro", "pro_lifetime")
        on_trial = is_trial_active(user_info)

        if paid:
            tier_label = "PRO"
        elif on_trial:
            tier_label = "TRIAL"
        else:
            tier_label = "FREE"

        st.sidebar.markdown(f"**{st.session_state.username}** &nbsp; `{tier_label}`")

        if on_trial and not paid:
            from tiers import get_trial_urgency_level
            urgency_css, urgency_text = get_trial_urgency_level()
            if urgency_text:
                st.sidebar.markdown(
                    f'<div class="{urgency_css}">{urgency_text}</div>',
                    unsafe_allow_html=True,
                )
            if st.sidebar.button("Keep Pro", key="trial_upgrade_btn", use_container_width=True):
                st.session_state.nav_target = "upgrade"
                st.rerun()

        # Expired trial recap — endowment effect
        if not paid and not on_trial and user_info and user_info.get("trial_ends_at"):
            from tiers import render_trial_expired_recap
            render_trial_expired_recap()

        if st.sidebar.button("Log Out", key="logout_btn"):
            st.session_state.clear()
            st.rerun()
        return st.session_state.username

    # Not logged in — subtle expander (doesn't block the sidebar)
    with st.sidebar.expander("Log In / Sign Up"):
        auth_tab = st.radio("", ["Log In", "Sign Up"], horizontal=True, key="auth_tab", label_visibility="collapsed")

        if auth_tab == "Log In":
            with st.form("login_form"):
                username = st.text_input("Username", key="login_user")
                password = st.text_input("Password", type="password", key="login_pass")
                submitted = st.form_submit_button("Log In", use_container_width=True)

            if submitted and username and password:
                success, msg = login(username, password)
                if success:
                    st.session_state.username = username
                    user_info = get_user_info(username)
                    st.session_state.user_tier = effective_tier(user_info)
                    st.rerun()
                else:
                    st.error(msg)

        else:
            with st.form("signup_form"):
                username = st.text_input("Username", key="signup_user")
                email = st.text_input("Email", key="signup_email")
                password = st.text_input("Password", type="password", key="signup_pass")
                submitted = st.form_submit_button("Create Free Account", use_container_width=True)

            if submitted and username and email and password:
                success, msg = signup(username, email, password)
                if success:
                    st.session_state.username = username
                    user_info = get_user_info(username)
                    st.session_state.user_tier = effective_tier(user_info)
                    st.success(f"{msg} 7 days of Pro unlocked.")
                    st.rerun()
                else:
                    st.error(msg)

        st.caption("Sign up — 7 days of Pro free, no card required")

    return None
