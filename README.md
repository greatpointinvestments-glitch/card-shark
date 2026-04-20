# Card Shark 🦈

Sports card investment analyzer built with Streamlit. Search players, find deals, scout breakout rookies, evaluate legend cards, and check trades — all powered by live eBay market data.

## Features

- **Player Search** — Look up any NBA/NFL/MLB player, see career stats, and browse eBay card listings with deal detection
- **Breakout Leaderboard** — Ranked young NBA players with the highest breakout potential, scored on trajectory, age, draft position, and market data
- **Legend Cards** — Retired player investment guide with hidden gem detection for undervalued HOF cards
- **Trade Checker** — Evaluate multi-card trades with eBay market valuations and letter grades

## Demo Mode

Card Shark works out of the box with realistic demo data — no API keys required. Add your own keys for live eBay listings.

## Setup

1. Clone and install:
   ```bash
   pip install -r requirements.txt
   ```

2. (Optional) Add API keys in a `.env` file:
   ```
   EBAY_CLIENT_ID=your_client_id
   EBAY_CLIENT_SECRET=your_client_secret
   BALLDONTLIE_API_KEY=your_key
   ```

3. Run:
   ```bash
   streamlit run app.py
   ```

## Streamlit Cloud

To deploy on Streamlit Community Cloud:

1. Push to GitHub
2. Connect the repo at [share.streamlit.io](https://share.streamlit.io)
3. Add your API keys in the app's Secrets settings (same format as `.env`)

The app automatically checks `st.secrets` first, then falls back to environment variables.

## Tech Stack

- **Streamlit** — UI framework
- **eBay Browse + Finding APIs** — Active and sold card listings
- **nba_api** — NBA player stats
- **ESPN + MLB Stats APIs** — NFL and MLB stats (free, no key needed)

## Built By

Sam & Son | Powered by Claude Code
