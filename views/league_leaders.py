"""League Leaders — real-time stat leaders by sport with Buy Cards links."""

import streamlit as st

from modules.league_leaders import (
    get_leaders, get_award_odds, get_award_season,
    is_nba_offseason, get_nba_display_season,
    is_mlb_offseason, get_mlb_display_season,
    is_nfl_offseason, get_nfl_display_season,
    SPORT_CATEGORIES,
)
from modules.affiliates import ebay_search_affiliate_url
from modules.ui_helpers import gradient_divider
from tiers import is_pro, render_teaser_gate, render_upgrade_banner


def render():
    st.title("League Leaders")
    st.caption("Top performers across MLB, NBA, and NFL — every row is a card to chase")

    # --- Sport selector ---
    sport = st.radio("Sport", ["MLB", "NBA", "NFL"], horizontal=True, key="ll_sport")

    # --- Offseason banners ---
    if sport == "NBA" and is_nba_offseason():
        _, nba_label = get_nba_display_season()
        st.info(f"NBA offseason — showing **{nba_label}** final leaders.")
    elif sport == "MLB" and is_mlb_offseason():
        _, mlb_label = get_mlb_display_season()
        st.info(f"MLB offseason — showing **{mlb_label}** final leaders.")
    elif sport == "NFL" and is_nfl_offseason():
        _, nfl_label = get_nfl_display_season()
        st.info(f"NFL offseason — showing **{nfl_label}** final leaders.")

    # --- Tabs: stat categories + Award Races ---
    _is_pro = is_pro()
    stat_categories = list(SPORT_CATEGORIES.get(sport, {}).keys())
    tab_names = stat_categories + ["Award Races"]
    tabs = st.tabs(tab_names)

    # Stat category tabs
    for i, category in enumerate(stat_categories):
        with tabs[i]:
            _render_stat_leaders(sport, category, _is_pro)

    # Award Races tab (last tab)
    with tabs[-1]:
        _render_award_odds(sport, _is_pro)


def _render_stat_leaders(sport: str, category: str, _is_pro: bool):
    """Render a stat leaders table for a given sport + category."""
    row_limit = 20 if _is_pro else 5

    with st.spinner("Loading leaders..."):
        leaders = get_leaders(sport, category, limit=20)

    if not leaders:
        st.warning(f"No {sport} leader data available right now. Try again later.")
        return

    # --- Metrics row ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Sport", sport)
    m2.metric("Category", category)
    m3.metric("Players Shown", f"{min(len(leaders), row_limit)} of {len(leaders)}")

    gradient_divider()

    # Header row
    h1, h2, h3, h4, h5 = st.columns([0.5, 2.5, 1.5, 1.5, 1.5])
    h1.markdown("**#**")
    h2.markdown("**Player**")
    h3.markdown("**Team**")
    h4.markdown("**Value**")
    h5.markdown("**Buy Cards**")

    # Visible rows
    visible = leaders[:row_limit]
    for row in visible:
        c1, c2, c3, c4, c5 = st.columns([0.5, 2.5, 1.5, 1.5, 1.5])
        c1.write(row["rank"])
        c2.write(row["player"])
        c3.write(row["team"])
        c4.write(row["value"])
        buy_url = ebay_search_affiliate_url(row["player"], sport)
        c5.markdown(
            f'<a href="{buy_url}" target="_blank" class="ebay-btn">Buy Cards</a>',
            unsafe_allow_html=True,
        )

    # --- Teaser blur for free users ---
    if not _is_pro and len(leaders) > row_limit:
        st.markdown('<div class="teaser-blur">', unsafe_allow_html=True)
        for row in leaders[row_limit:row_limit + 5]:
            t1, t2, t3, t4, t5 = st.columns([0.5, 2.5, 1.5, 1.5, 1.5])
            t1.write(row["rank"])
            t2.write(row["player"])
            t3.write(row["team"])
            t4.write(row["value"])
            t5.write("---")
        st.markdown('</div>', unsafe_allow_html=True)
        render_teaser_gate("League Leaders", "Unlock the full top 20 with Pro")


def _render_award_odds(sport: str, _is_pro: bool):
    """Render the Award Odds section with podium-style display."""
    season_year = get_award_season(sport)
    odds_source = "FanDuel" if sport == "MLB" else "ESPN BET"
    if sport == "NBA":
        season_label = f"{season_year - 1}-{str(season_year)[-2:]}"
    else:
        season_label = str(season_year)

    st.markdown(
        f'<div style="text-align:center;padding:10px 0;">'
        f'<h2 style="margin-bottom:4px;">Award Races</h2>'
        f'<span style="color:#9ca3af;">{season_label} season &bull; Odds via {odds_source}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    with st.spinner("Loading award odds..."):
        odds_data = get_award_odds(sport)

    if not odds_data or all(len(v) == 0 for v in odds_data.values()):
        st.info("Odds not yet available for this season.")
        return

    # Determine which awards to show based on tier
    if sport == "MLB":
        mvp_awards = ["AL MVP", "NL MVP"]
        pro_awards = ["AL ROY", "NL ROY", "AL Cy Young", "NL Cy Young"]
    elif sport == "NBA":
        mvp_awards = ["MVP"]
        pro_awards = ["ROY"]
    else:  # NFL
        mvp_awards = ["MVP"]
        pro_awards = ["Offensive ROY", "Defensive ROY"]

    # Always show MVP awards with podium styling
    _render_award_podium(odds_data, mvp_awards, sport)

    # Pro-only awards
    if _is_pro:
        gradient_divider()
        _render_award_podium(odds_data, pro_awards, sport)
    else:
        gradient_divider()
        pro_label = "ROY & Cy Young" if sport == "MLB" else "Rookie of the Year"
        render_upgrade_banner("Award Odds", f"{pro_label} odds")


def _render_award_podium(odds_data: dict, award_names: list[str], sport: str):
    """Render award odds with podium-style top 3 cards."""
    active = [(name, odds_data.get(name, [])) for name in award_names]

    for i in range(0, len(active), 2):
        pair = active[i:i + 2]
        cols = st.columns(len(pair))
        for col, (award_name, entries) in zip(cols, pair):
            with col:
                st.markdown(
                    f'<div style="text-align:center;padding:8px 0;">'
                    f'<h3 style="margin-bottom:8px;">{award_name}</h3></div>',
                    unsafe_allow_html=True,
                )
                if not entries:
                    st.caption("Not yet available")
                    continue

                # Podium top 3
                medal_icons = ["🥇", "🥈", "🥉"]
                medal_gradients = [
                    "linear-gradient(135deg,#854d0e,#ca8a04)",
                    "linear-gradient(135deg,#4b5563,#9ca3af)",
                    "linear-gradient(135deg,#7c2d12,#c2410c)",
                ]
                for j, entry in enumerate(entries[:3]):
                    player = entry["player"]
                    team = f" ({entry['team']})" if entry.get("team") else ""
                    odds = _format_odds(entry["odds"])
                    buy_url = ebay_search_affiliate_url(player, sport)
                    icon = medal_icons[j] if j < 3 else ""
                    bg = medal_gradients[j] if j < 3 else "linear-gradient(135deg,#1a1f2e,#2d3748)"
                    font_size = "1.1em" if j == 0 else "1em"
                    st.markdown(
                        f'<div style="background:{bg};border-radius:10px;padding:12px 16px;'
                        f'margin:6px 0;display:flex;justify-content:space-between;align-items:center;">'
                        f'<div>'
                        f'<span style="font-size:1.2em;">{icon}</span> '
                        f'<strong style="font-size:{font_size};">{player}</strong>'
                        f'<span style="color:#d1d5db;">{team}</span>'
                        f'</div>'
                        f'<div style="display:flex;align-items:center;gap:10px;">'
                        f'<span style="font-weight:bold;font-size:1.1em;">{odds}</span>'
                        f'<a href="{buy_url}" target="_blank" class="ebay-btn" '
                        f'style="font-size:0.75em;padding:3px 10px;">Buy Cards</a>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )

                # Remaining entries (4-5) in simpler format
                for entry in entries[3:]:
                    player = entry["player"]
                    team = f" ({entry['team']})" if entry.get("team") else ""
                    odds = _format_odds(entry["odds"])
                    buy_url = ebay_search_affiliate_url(player, sport)
                    st.markdown(
                        f'<div style="padding:6px 16px;margin:2px 0;">'
                        f'#{entry["rank"]} {player}{team} — {odds} &nbsp; '
                        f'<a href="{buy_url}" target="_blank" class="ebay-btn" '
                        f'style="font-size:0.7em;padding:2px 8px;">Buy</a></div>',
                        unsafe_allow_html=True,
                    )


def _format_odds(odds) -> str:
    """Format odds with + prefix if positive."""
    if odds and not str(odds).startswith("-") and not str(odds).startswith("+"):
        try:
            float(odds)
            return f"+{odds}"
        except ValueError:
            pass
    return str(odds)
