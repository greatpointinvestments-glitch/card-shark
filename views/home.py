"""Home page — landing hero, deal radar, trending, feature cards."""

import streamlit as st

from modules.ui_helpers import (
    card_thumbnail, format_badge, deal_badge,
    ebay_button, gradient_divider,
)
from modules.affiliates import affiliate_url
from modules.deal_radar import get_top_deals, prepare_watchlist_data
from modules.breakout_engine import build_leaderboard
from modules.price_alerts import get_alerts
from modules.ebay_search import search_ebay_cards
from modules.affiliates import ebay_search_affiliate_url
from config.settings import ANON_SEARCH_LIMIT, SOCIAL_PROOF_STATS
from data.watchlists import NBA_BREAKOUT_WATCHLIST, NFL_BREAKOUT_WATCHLIST, MLB_BREAKOUT_WATCHLIST, LEGENDS_WATCHLIST
from tiers import is_pro


def render(current_user: str | None):
    # Impact.com site verification (visible to crawlers, invisible to users)
    st.markdown('<p style="font-size:1px;color:transparent;line-height:0;margin:0;padding:0;height:0;overflow:hidden;">Impact-Site-Verification: 7f5de73e-561a-4412-be25-6945fd4abeef</p>', unsafe_allow_html=True)

    # --- Landing Hero (for visitors) ---
    if not current_user:
        import base64, os
        _logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "card-shark-logo.png")
        with open(_logo_path, "rb") as _f:
            _logo_b64 = base64.b64encode(_f.read()).decode()
        st.markdown(f"""
        <div style="text-align:center; padding: 40px 20px 10px 20px;">
            <img src="data:image/png;base64,{_logo_b64}" style="width:120px;height:120px;margin-bottom:8px;" />
            <h1 style="font-size:3em; margin-bottom:0;">Card Shark</h1>
            <p style="font-size:1.4em; color:#9ca3af; margin-top:8px;">
                Scan any card. Know what it's worth. Find the deals everyone else misses.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Hero CTA — prominent signup button
        _hero_cta_col1, _hero_cta_col2, _hero_cta_col3 = st.columns([1, 2, 1])
        with _hero_cta_col2:
            if st.button("Get Started Free — 7 Days of Pro", type="primary", use_container_width=True, key="hero_cta"):
                st.session_state.auth_tab = "Sign Up"
                st.rerun()
            st.markdown(
                '<p style="text-align:center;color:#9ca3af;font-size:0.9em;margin-top:4px;">'
                'No credit card required</p>',
                unsafe_allow_html=True,
            )

        # Social proof strip
        st.markdown(
            f'<div class="social-proof-strip">'
            f'<div class="stat"><div class="stat-value">{SOCIAL_PROOF_STATS["cards_scanned"]}</div>'
            f'<div class="stat-label">Cards Scanned</div></div>'
            f'<div class="stat"><div class="stat-value">{SOCIAL_PROOF_STATS["active_users"]}</div>'
            f'<div class="stat-label">Active Users</div></div>'
            f'<div class="stat"><div class="stat-value">{SOCIAL_PROOF_STATS["deals_found"]}</div>'
            f'<div class="stat-label">Deals Found</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        hero_c1, hero_c2, hero_c3 = st.columns(3)
        with hero_c1:
            st.markdown("""
            <div style="text-align:center; padding:20px;">
                <div style="font-size:2.5em;">📷</div>
                <h3>AI Card Scanner</h3>
                <p style="color:#9ca3af;">Snap a photo — instant ID, value, and grading ROI</p>
            </div>
            """, unsafe_allow_html=True)
        with hero_c2:
            st.markdown("""
            <div style="text-align:center; padding:20px;">
                <div style="font-size:2.5em;">💰</div>
                <h3>Flip Finder</h3>
                <p style="color:#9ca3af;">Cards listed below sold prices — money on the table</p>
            </div>
            """, unsafe_allow_html=True)
        with hero_c3:
            st.markdown("""
            <div style="text-align:center; padding:20px;">
                <div style="font-size:2.5em;">🚀</div>
                <h3>Breakout Alerts</h3>
                <p style="color:#9ca3af;">Tomorrow's stars before the market catches on</p>
            </div>
            """, unsafe_allow_html=True)

        # Anonymous try-it search
        gradient_divider()
        st.markdown("### Try It — Search Any Player")
        anon_query = st.text_input("Player name", placeholder="e.g. LeBron James, Victor Wembanyama", key="anon_search")
        if anon_query:
            if st.session_state.anon_searches_used >= ANON_SEARCH_LIMIT:
                st.warning("Create a free account to keep searching — it takes 10 seconds.")
                if st.button("Sign Up Free", key="anon_gate_signup", type="primary", use_container_width=True):
                    st.session_state.auth_tab = "Sign Up"
                    st.rerun()
            else:
                with st.spinner(f"Searching for {anon_query}..."):
                    anon_results = search_ebay_cards(anon_query, "NBA", "Any", limit=3)
                st.session_state.anon_searches_used += 1
                if anon_results:
                    for listing in anon_results[:3]:
                        _ac1, _ac2 = st.columns([3, 1])
                        with _ac1:
                            st.write(f"**{listing['title'][:70]}**")
                        with _ac2:
                            st.write(f"${listing['total']:.2f}")
                    st.info("Sign up free to see full results, set price alerts, and track your collection.")
                    if st.button("Create Free Account", key="anon_results_signup", type="primary", use_container_width=True):
                        st.session_state.auth_tab = "Sign Up"
                        st.rerun()
                else:
                    st.info("No results found. Try a different name or sign up for the full search experience.")

        gradient_divider()
    else:
        st.image("assets/card-shark-logo.png", width=80)
        st.title("Card Shark")
        st.markdown("#### Find steals. Spot breakouts. Trade smarter.")

        # --- Collection Summary Card (logged-in users) ---
        from modules.portfolio import get_portfolio
        _home_portfolio = get_portfolio()
        if _home_portfolio:
            _pv = st.session_state.get("portfolio_values", {})
            _total_cards = len(_home_portfolio)
            _total_cost = sum(c.get("purchase_price", 0) * c.get("quantity", 1) for c in _home_portfolio)
            _total_current = 0
            _has_market_data = bool(_pv)
            if _has_market_data:
                for c in _home_portfolio:
                    mv = _pv.get(c["id"], 0)
                    _total_current += mv * c.get("quantity", 1) if mv > 0 else c.get("purchase_price", 0) * c.get("quantity", 1)
            else:
                _total_current = _total_cost

            _pl = _total_current - _total_cost
            _pl_pct = (_pl / _total_cost * 100) if _total_cost > 0 else 0
            _pl_color = "#22c55e" if _pl >= 0 else "#ef4444"
            _pl_sign = "+" if _pl >= 0 else ""

            st.markdown(
                f'<div style="background:linear-gradient(135deg,#1a1f2e,#2d3748);border-radius:12px;'
                f'padding:16px 20px;margin:10px 0;border:1px solid #3b4560;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">'
                f'<div>'
                f'<strong style="font-size:1.1em;">My Collection</strong> &nbsp;'
                f'<span style="color:#9ca3af;">{_total_cards} cards</span>'
                f'</div>'
                f'<div style="display:flex;gap:20px;align-items:center;">'
                f'<span style="color:#9ca3af;">Value: <strong>${_total_current:,.2f}</strong></span>'
                f'<span style="color:{_pl_color};font-weight:bold;">'
                f'{_pl_sign}${_pl:,.2f} ({_pl_sign}{_pl_pct:.1f}%)</span>'
                f'</div></div></div>',
                unsafe_allow_html=True,
            )
            if not _has_market_data:
                st.caption("Visit My Collection to refresh market values")
            _hc1, _hc2 = st.columns(2)
            with _hc1:
                if st.button("Open My Collection", key="home_coll_nav", use_container_width=True):
                    st.session_state.nav_target = "📁 My Collection"
                    st.rerun()
            with _hc2:
                st.write("")

        # First-visit onboarding banner
        if not st.session_state.get("onboarding_dismissed"):
            from auth import get_user_info
            user_info = get_user_info(current_user)
            if user_info:
                from datetime import datetime, timedelta
                created = user_info.get("created_at", "")
                try:
                    created_dt = datetime.fromisoformat(created)
                    is_new = (datetime.now() - created_dt) < timedelta(days=1)
                except (ValueError, TypeError):
                    is_new = False
                if is_new:
                    st.markdown(
                        '<div style="background:linear-gradient(135deg,#064e3b,#065f46);'
                        'border-radius:10px;padding:16px 20px;margin:10px 0;">'
                        '<strong style="font-size:1.1em;">Welcome to Card Shark!</strong>'
                        '<p style="color:#d1d5db;margin:8px 0 4px 0;">Get started in 3 steps:</p>'
                        '<ol style="color:#d1d5db;margin:0;padding-left:20px;">'
                        '<li>Search a player to see their card market</li>'
                        '<li>Add cards to your collection to track P&L</li>'
                        '<li>Set price alerts so you never miss a deal</li>'
                        '</ol></div>',
                        unsafe_allow_html=True,
                    )
                    if st.button("Got it!", key="dismiss_onboarding"):
                        st.session_state.onboarding_dismissed = True
                        st.rerun()

    # --- Alert Banner ---
    home_alerts = get_alerts()
    if home_alerts:
        triggered = [a for a in home_alerts if a.get("triggered")]
        if triggered:
            for ta in triggered[:3]:
                st.toast(f"🔔 {ta['player_name']} hit your ${ta['threshold_price']:.2f} {ta['alert_type']} alert!")

    # --- Daily Drop Teaser ---
    from modules.daily_drop import get_daily_card, get_user_vote, cast_vote, get_community_split, compute_user_streak
    drop = get_daily_card()
    if drop:
        drop_date = drop["drop_date"]
        drop_buy_url = ebay_search_affiliate_url(drop["player_name"], drop["sport"])
        drop_listing_url = drop.get("listing", {}).get("url", "")
        drop_link = affiliate_url(drop_listing_url) if drop_listing_url else drop_buy_url
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#7c2d12,#dc2626);border-radius:12px;'
            f'padding:16px 20px;margin:10px 0;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<div>'
            f'<strong style="font-size:1.1em;">Daily Drop</strong> &nbsp;'
            f'<span style="color:#fbbf24;font-size:0.9em;">{drop["player_name"]} ({drop["sport"]})</span><br>'
            f'<span style="color:#d1d5db;font-size:0.9em;">${drop["drop_price"]:.2f}</span> &nbsp;'
            f'<a href="{drop_link}" target="_blank" class="ebay-btn" '
            f'style="font-size:0.75em;padding:2px 10px;">Buy on eBay</a>'
            f'</div>'
            f'<div style="font-size:0.85em;color:#fbbf24;">BUY or PASS?</div>'
            f'</div>'
            f'<div style="color:#d1d5db;font-size:0.8em;margin-top:6px;">'
            f'We pick one card every day. You vote BUY or PASS. We check the price in 7 days. Get it right, build your streak.</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if current_user:
            existing_vote = get_user_vote(current_user, drop_date)
            if existing_vote:
                split = get_community_split(drop_date)
                streak = compute_user_streak(current_user)
                streak_text = f' &bull; {streak["current_streak"]} streak' if streak["current_streak"] > 0 else ""
                st.markdown(
                    f'<div style="text-align:center;padding:4px;">'
                    f'<span style="color:#9ca3af;">You voted <strong>{existing_vote}</strong> &bull; '
                    f'{split["buy_pct"]}% say BUY{streak_text}</span></div>',
                    unsafe_allow_html=True,
                )
            else:
                dd1, dd2, dd3 = st.columns([1, 1, 1])
                with dd1:
                    if st.button("BUY", key="home_drop_buy", type="primary"):
                        cast_vote(current_user, drop_date, "BUY")
                        st.rerun()
                with dd2:
                    if st.button("PASS", key="home_drop_pass"):
                        cast_vote(current_user, drop_date, "PASS")
                        st.rerun()
                with dd3:
                    if st.button("See Full Drop", key="home_drop_nav"):
                        st.session_state.nav_target = "🎯 Daily Drop"
                        st.rerun()
        else:
            if st.button("Vote Now — Sign Up Free", key="home_drop_signup"):
                st.session_state.auth_tab = "Sign Up"
                st.rerun()

    gradient_divider()

    # --- Feature cards ---
    # (title, css_class, button_label, button_key, nav_target, description, is_pro_feature)
    _FEATURE_CARDS = [
        ("🎯 Daily Drop", "feature-card-drop", "Vote Now", "home_drop", "🎯 Daily Drop",
         "BUY or PASS? Vote daily, build streaks, climb the leaderboard", False),
        ("🎰 Pack Simulator", "feature-card-packs", "Rip Packs", "home_packs", "🎰 Pack Simulator",
         "Rip virtual packs with real prices. Can you beat the odds?", False),
        ("🔍 Player Search", "feature-card-search", "Search Players", "home_search", "🔍 Player Search",
         "Look up any player — see their stats, card prices, and deals", False),
        ("🚀 Breakout Leaderboard", "feature-card-breakout", "View Breakouts", "home_breakout", "🚀 Breakout Leaderboard",
         "Tomorrow's stars before the market catches on", False),
        ("🏆 Legend Cards", "feature-card-legends", "Hunt Legends", "home_legends", "🏆 Legend Cards",
         "Undervalued GOAT cards hiding in plain sight", False),
        ("🔄 Trade Checker", "feature-card-trade", "Check a Trade", "home_trade", "🔄 Trade Checker",
         "Who's winning this trade? Find out instantly.", False),
        ("💰 Flip Finder", "feature-card-flip", "Find Flips", "home_flip", "💰 Flip Finder",
         "BIN listings below sold prices — money on the table", True),
        ("⚔️ Player Comparison", "feature-card-compare", "Compare Players", "home_compare", "⚔️ Player Comparison",
         "Wemby or Chet? Side-by-side investment verdict.", True),
        ("📁 My Collection", "feature-card-portfolio", "Open Collection", "home_portfolio", "📁 My Collection",
         "Know exactly what your collection is worth right now", False),
        ("💪 Collection Battles", "feature-card-battles", "Battle Now", "home_battles", "💪 Collection Battles",
         "Challenge a friend. 5 categories. 100 points. Who wins?", False),
        ("📐 Grading Calculator", "feature-card-grading", "Calculate ROI", "home_grading", "📐 Grading Calculator",
         "Should you send it to PSA? Find out before you spend.", True),
        ("🏅 Award Races", "feature-card-awards", "See Odds", "home_awards", "🥇 League Leaders",
         "MVP, ROY, Cy Young — who's winning the races and which cards to buy", False),
        ("🏟️ Live Games", "feature-card-games", "Track Games", "home_games", "🏟️ Live Games",
         "Your players in action — live scores, alerts when they go off", False),
        ("📷 Card Scanner", "feature-card-scanner", "Scan a Card", "home_scanner", "📷 Card Scanner",
         "Snap a photo — AI identifies your card instantly", False),
        ("📊 Price History", "feature-card-history", "View History", "home_history", "📊 Price History",
         "Interactive charts — track any card's price over time", True),
        ("📈 Market Movers", "feature-card-movers", "See Movers", "home_movers", "📈 Market Movers",
         "Who's hot, who's not — biggest weekly price swings", True),
        ("🔔 Price Alerts", "feature-card-alerts", "Set Alerts", "home_alerts", "🔔 Price Alerts",
         "Get notified when cards hit your target price", True),
    ]

    _user_is_pro = is_pro()
    for i in range(0, len(_FEATURE_CARDS), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(_FEATURE_CARDS):
                title, css, btn_label, btn_key, nav_target, desc, is_pro_feature = _FEATURE_CARDS[idx]
                with col:
                    pro_tag = ' <span class="pro-badge">PRO</span>' if (is_pro_feature and not _user_is_pro) else ""
                    st.markdown(f'<div class="feature-card {css}"><h3>{title}{pro_tag}</h3><p>{desc}</p></div>', unsafe_allow_html=True)
                    if st.button(btn_label, key=btn_key, use_container_width=True):
                        st.session_state.nav_target = nav_target
                        st.rerun()

    # --- What Pro Found Today (FOMO for free users) ---
    if current_user and not is_pro():
        gradient_divider()
        st.markdown(
            '<div style="background:linear-gradient(135deg,#1e3a5f,#1e40af);'
            'border-radius:10px;padding:16px 20px;margin:10px 0;">'
            '<strong style="font-size:1.1em;">What Pro Users Found Today</strong>'
            '<div style="display:flex;gap:24px;margin-top:10px;flex-wrap:wrap;">'
            '<div style="text-align:center;">'
            '<div style="font-size:1.5em;font-weight:900;color:#22c55e;">4</div>'
            '<div style="font-size:0.8em;color:#9ca3af;">Flip Opportunities</div></div>'
            '<div style="text-align:center;">'
            '<div style="font-size:1.5em;font-weight:900;color:#f59e0b;">23</div>'
            '<div style="font-size:0.8em;color:#9ca3af;">Cards Up 15%+ This Week</div></div>'
            '<div style="text-align:center;">'
            '<div style="font-size:1.5em;font-weight:900;color:#3b82f6;">7</div>'
            '<div style="font-size:0.8em;color:#9ca3af;">Price Alerts Triggered</div></div>'
            '<div style="text-align:center;">'
            '<div style="font-size:1.5em;font-weight:900;color:#a78bfa;">$340</div>'
            '<div style="font-size:0.8em;color:#9ca3af;">Total Flip Profit Found</div></div>'
            '</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("See What You're Missing", key="pro_fomo_upgrade", use_container_width=True):
            st.session_state.nav_target = "upgrade"
            st.rerun()

    gradient_divider()

    # --- Deal Radar ---
    st.markdown("### Today's Best Deals")
    st.caption("The best Buy It Now deals on breakout players — updates every 10 min")

    watchlist_map = {"NBA": NBA_BREAKOUT_WATCHLIST, "NFL": NFL_BREAKOUT_WATCHLIST, "MLB": MLB_BREAKOUT_WATCHLIST}
    wl_data = prepare_watchlist_data(watchlist_map)

    with st.spinner("Scanning for deals..."):
        top_deals = get_top_deals(wl_data)

    if top_deals:
        for deal in top_deals:
            dc0, dc1, dc2, dc3, dc4 = st.columns([0.5, 3, 1, 1, 1])
            with dc0:
                st.markdown(card_thumbnail(deal.get("image_url", "")), unsafe_allow_html=True)
            with dc1:
                fmt_bdg = format_badge(deal["buying_format"])
                d_badge = deal_badge(deal["vs_median"])
                aff = affiliate_url(deal["url"])
                st.markdown(
                    f'{fmt_bdg}{d_badge}<a href="{aff}" target="_blank" '
                    f'style="text-decoration:none">{deal["title"][:65]}</a>'
                    f'<br><small style="color:#9ca3af">{deal["player"]} • {deal["sport"]}</small>',
                    unsafe_allow_html=True,
                )
            with dc2:
                vs = deal["vs_median"]
                color = "#22c55e" if vs < -10 else "#facc15"
                st.markdown(f"**${deal['total']:.2f}** <span style='color:{color}'>({vs:+.0f}%)</span>", unsafe_allow_html=True)
            with dc3:
                st.markdown(ebay_button(deal["url"]), unsafe_allow_html=True)
            with dc4:
                st.write("")
    else:
        st.info("No standout BIN deals right now — check back soon!")

    gradient_divider()

    # --- Trending Now ---
    st.markdown("### Trending Now")
    tm1, tm2, tm3 = st.columns(3)
    for col, (sport_name, watchlist) in zip(
        [tm1, tm2, tm3],
        [("NBA", NBA_BREAKOUT_WATCHLIST), ("NFL", NFL_BREAKOUT_WATCHLIST), ("MLB", MLB_BREAKOUT_WATCHLIST)],
    ):
        lb = build_leaderboard(watchlist, sport_name)
        hot_count = sum(1 for p in lb if p["signal"] == "BUY") if lb else 0
        top_name = lb[0]["name"] if lb else "—"
        with col:
            col.metric(f"{sport_name} Hot Players", hot_count)
            if lb and hot_count > 0:
                top_buy = next((p for p in lb if p["signal"] == "BUY"), None)
                if top_buy:
                    st.caption(f"#1 {top_buy['name']} — Score: {top_buy['score']}")
            elif lb:
                st.caption(f"Top ranked: {top_name} (Watch)")
            else:
                st.caption("No data yet")

    gradient_divider()

    # Players We Track
    st.markdown("### Players We Track")
    total_players = len(NBA_BREAKOUT_WATCHLIST) + len(NFL_BREAKOUT_WATCHLIST) + len(MLB_BREAKOUT_WATCHLIST) + len(LEGENDS_WATCHLIST)
    wm1, wm2, wm3, wm4 = st.columns(4)
    wm1.metric("NBA", f"{len(NBA_BREAKOUT_WATCHLIST)} players")
    wm2.metric("NFL", f"{len(NFL_BREAKOUT_WATCHLIST)} players")
    wm3.metric("MLB", f"{len(MLB_BREAKOUT_WATCHLIST)} players")
    wm4.metric("Legends", f"{len(LEGENDS_WATCHLIST)} players")
    st.caption(f"{total_players} players tracked across all sports — and growing every week")


