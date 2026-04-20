"""Live Games page."""

import streamlit as st

from modules.ui_helpers import gradient_divider, ebay_button
from modules.portfolio import get_portfolio
from modules.live_games import get_todays_games, match_players_to_games, build_watch_links, get_game_card_impact
from data.watchlists import NBA_BREAKOUT_WATCHLIST, NFL_BREAKOUT_WATCHLIST, MLB_BREAKOUT_WATCHLIST


def render():
    st.title("🏟️ Live Game Tracker")
    st.caption("See which of your players are in action today — live scores, watch links, and card-market impact")

    gf1, gf2, gf3 = st.columns([2, 2, 1])
    with gf1:
        game_sports = st.multiselect("Sports", ["NBA", "NFL", "MLB"], default=["NBA", "NFL", "MLB"], key="game_sports")
    with gf2:
        game_source = st.radio("Players from", ["Both", "My Portfolio", "Watchlist"], horizontal=True, key="game_source")
    with gf3:
        auto_refresh = st.toggle("Auto-refresh (2 min)", value=False, key="game_auto_refresh")

    gradient_divider()

    player_list = []
    if game_source in ("My Portfolio", "Both"):
        portfolio = get_portfolio()
        for card in portfolio:
            player_list.append({
                "player_name": card["player_name"],
                "sport": card["sport"],
                "card_type": card.get("card_type", ""),
                "source": "Portfolio",
            })
    if game_source in ("Watchlist", "Both"):
        wl_map = {"NBA": NBA_BREAKOUT_WATCHLIST, "NFL": NFL_BREAKOUT_WATCHLIST, "MLB": MLB_BREAKOUT_WATCHLIST}
        for sport in game_sports:
            for p in wl_map.get(sport, []):
                if not any(pl["player_name"].lower() == p["name"].lower() for pl in player_list):
                    player_list.append({
                        "player_name": p["name"],
                        "sport": sport,
                        "team": p["team"],
                        "card_type": "",
                        "source": "Watchlist",
                    })

    all_games = []
    for sport in game_sports:
        all_games.extend(get_todays_games(sport))

    matched = match_players_to_games(player_list, all_games)
    playing = [m for m in matched if m["is_playing_today"]]
    not_playing = [m for m in matched if not m["is_playing_today"]]

    games_live = sum(1 for g in all_games if g["status"] == "In Progress")
    games_final = sum(1 for g in all_games if g["status"] == "Final")
    games_upcoming = sum(1 for g in all_games if g["status"] == "Scheduled")

    sm1, sm2, sm3, sm4 = st.columns(4)
    sm1.metric("Players in Action", len(playing))
    sm2.metric("Games Live", games_live)
    sm3.metric("Games Final", games_final)
    sm4.metric("Games Upcoming", games_upcoming)

    gradient_divider()

    if playing:
        st.markdown("### Your Players in Action")
        for m in playing:
            game = m["game"]
            links = build_watch_links(game)
            impact = get_game_card_impact(m["player_name"], game)

            if game["status"] == "In Progress":
                status_html = '<span class="game-live">LIVE</span>'
            elif game["status"] == "Final":
                status_html = '<span class="game-final">FINAL</span>'
            else:
                status_html = '<span class="game-scheduled">UPCOMING</span>'

            score_text = f'{game["away_team"]} **{game["away_score"]}** — **{game["home_score"]}** {game["home_team"]}'

            pc1, pc2, pc3 = st.columns([3, 2, 2])
            with pc1:
                st.markdown(f"**{m['player_name']}** — {m['team']}")
                st.markdown(f"{status_html} &nbsp; {game['status_detail']}", unsafe_allow_html=True)
                st.caption(f"vs {m['opponent']}")
            with pc2:
                st.markdown(score_text)
                if game["broadcast"]:
                    st.caption(f"📺 {game['broadcast']}")
            with pc3:
                gc_url = links["gamecast"]
                yt_url = links["youtube_highlights"]
                dk_url = links["draftkings"]
                gc_label = "MLB Gameday" if game.get("sport") == "MLB" else "ESPN"
                st.markdown(
                    f'<a href="{gc_url}" target="_blank" class="ebay-btn" style="margin-right:6px">{gc_label}</a>'
                    f'<a href="{yt_url}" target="_blank" class="ebay-btn" style="background:linear-gradient(135deg,#dc2626,#ef4444);margin-right:6px">Highlights</a>'
                    f'<a href="{dk_url}" target="_blank" class="ebay-btn" style="background:linear-gradient(135deg,#2d6b3f,#4ade80);margin-right:6px">DraftKings</a>',
                    unsafe_allow_html=True,
                )

            if impact:
                st.info(impact)

            gradient_divider()

    if not_playing:
        with st.expander(f"Not playing today ({len(not_playing)})"):
            for m in not_playing:
                st.caption(f"{m['player_name']} — {m.get('team', 'N/A')} ({m.get('source', '')})")

    if not player_list:
        st.info("Add cards to your portfolio or use the watchlist to track players during games.")


render()
