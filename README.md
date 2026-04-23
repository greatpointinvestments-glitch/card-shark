# CardHawk 🦅

**Sports & Pokemon card investment analyzer.** Scan cards with AI, find underpriced deals, track your portfolio, and make smarter trades — powered by live eBay and TCGPlayer market data.

## What It Does

### Discover
- **Player Search** — Look up any NBA/NFL/MLB player or Pokemon, see stats and card listings with deal detection
- **What Can I Get?** — Budget-first card finder (set $25, find the best cards you can afford)
- **Breakout Leaderboard** — Young players ranked by breakout potential (trajectory, age, draft position, market data)
- **Legend Cards** — Retired player + iconic Pokemon investment guide with hidden gem detection
- **Live Games** — Real-time NBA/NFL/MLB scores with card impact alerts

### Tools
- **Card Scanner** — AI-powered card identification (Claude Vision). Snap a photo → instant ID, value, and condition estimate
- **Trade Checker** — Scan or enter cards on both sides, get a letter grade (A-F) with breakout upside bonuses
- **Player Comparison** — Side-by-side stats, market data, and investment verdict
- **Grading Calculator** — "Should I send this to PSA?" Expected value analysis with grade probability

### Market
- **Flip Finder** — BIN listings priced below recent sold prices with confidence scoring and seller verification
- **Market Movers** — Biggest price swings in the last 24-72 hours
- **Price History** — Interactive charts tracking any card's price over time
- **Price Alerts** — Set target prices, get notified when cards hit your buy/sell point

### My Stuff
- **My Collection** — Track what you paid, what it's worth now, P&L, diversification score, projected value
- **CSV Import** — Bulk import from Ludex, CollX, TCDB, Cardbase, or any CSV format

## Revenue Model

- **Freemium SaaS:** Free tier (10 searches/day, 25 cards) → Pro ($7.99/mo or $59.99/yr or $149 lifetime)
- **Affiliate commissions:** eBay Partner Network, TCGPlayer (Pokemon), PWCC, COMC, Fanatics Collect, Alt, Goldin
- **Pro features gated:** Flip Finder, Market Movers, Grading Calculator, Player Comparison, Price Alerts, Price History (90d+), CSV Export

## Tech Stack

- **Frontend:** Streamlit (Python)
- **APIs:** eBay Browse + Finding APIs, Pokemon TCG API, nba_api, ESPN, MLB Stats API
- **AI:** Anthropic Claude Vision (card scanning)
- **Payments:** Stripe (subscriptions + one-time lifetime deal)
- **Auth:** Custom auth with bcrypt, per-user data isolation
- **Affiliates:** 7 marketplace integrations with unified link handler

## Architecture

```
cardhawk/                ← Streamlit web app (this repo)
cardhawk-api/            ← FastAPI backend for mobile app (separate repo)
```

The FastAPI backend mirrors all business logic for the future React Native mobile app (iOS + Android). Both share the same eBay/TCGPlayer/stats APIs.

## Supported Categories

| Category | Data Source | Pricing |
|----------|-----------|---------|
| NBA | eBay + nba_api | eBay market data |
| NFL | eBay + ESPN | eBay market data |
| MLB | eBay + MLB Stats API | eBay market data |
| Pokemon | Pokemon TCG API + eBay | TCGPlayer prices (primary) + eBay graded (secondary) |

## Key Metrics Targets

| Metric | Month 1 | Month 6 |
|--------|---------|---------|
| Signups | 500 | 10,000 |
| Pro conversion | 8% | 15% |
| MRR | $300 | $6,000 |
| Lifetime deals | 15 | 100 (capped) |

## Status

- **Web app:** Live (v6.1 + Pokemon support)
- **API backend:** Built (67 files, 14 routes, PostgreSQL + Redis)
- **Mobile app:** Pending (React Native, post-DUNS approval)
- **Stripe:** Test mode configured
- **eBay Partner Network:** Application submitted
- **Domain:** cardhawkapp.com registered
- **Email:** hello@cardhawkapp.com (Zoho)

## Local Development

```bash
pip install -r requirements.txt
# Add API keys to .env (see .env.example)
streamlit run app.py
```

---

Built by Sam Heide | Powered by Claude Code
