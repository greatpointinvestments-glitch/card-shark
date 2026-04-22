"""Price History — real eBay sold data + Plotly chart builders.

Uses eBay Finding API (sold/completed items, 90-day lookback) to build
real price history. Falls back to cached data or demo data when the API
is unavailable or rate-limited.

Data is cached locally in data/price_cache/ as JSON files to avoid
hitting eBay on every page load. Cache TTL: 24 hours.
"""

import json
import os
import hashlib
from collections import defaultdict
from datetime import datetime, timedelta

import plotly.graph_objects as go
import streamlit as st

from modules.ebay_search import search_ebay_sold
from data.demo_price_history import generate_demo_price_history


_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "price_cache")
_CACHE_TTL_HOURS = 24

_PRICE_HISTORY_IS_DEMO = False  # Now using real data


def _cache_key(player: str, sport: str, card_type: str) -> str:
    raw = f"{player}|{sport}|{card_type}".lower()
    return hashlib.md5(raw.encode()).hexdigest()


def _load_cache(player: str, sport: str, card_type: str) -> list[dict] | None:
    """Load cached price history if fresh enough."""
    os.makedirs(_CACHE_DIR, exist_ok=True)
    path = os.path.join(_CACHE_DIR, f"{_cache_key(player, sport, card_type)}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            data = json.load(f)
        cached_at = datetime.fromisoformat(data.get("cached_at", "2000-01-01"))
        if datetime.now() - cached_at > timedelta(hours=_CACHE_TTL_HOURS):
            return None  # Stale
        return data.get("history", [])
    except (json.JSONDecodeError, IOError, ValueError):
        return None


def _save_cache(player: str, sport: str, card_type: str, history: list[dict]) -> None:
    """Save price history to local cache."""
    os.makedirs(_CACHE_DIR, exist_ok=True)
    path = os.path.join(_CACHE_DIR, f"{_cache_key(player, sport, card_type)}.json")
    try:
        with open(path, "w") as f:
            json.dump({
                "player": player,
                "sport": sport,
                "card_type": card_type,
                "cached_at": datetime.now().isoformat(),
                "history": history,
            }, f)
    except IOError:
        pass


def _sold_to_daily_prices(sold_listings: list[dict]) -> list[dict]:
    """Convert a list of sold listings into daily price history.

    Groups sold items by date, computes median price and volume per day.
    Returns sorted list of {date, price, volume} dicts.
    """
    if not sold_listings:
        return []

    # Group by sold date
    by_date = defaultdict(list)
    for item in sold_listings:
        date_str = item.get("sold_date", "")
        total = item.get("total", 0)
        if date_str and total > 0:
            by_date[date_str].append(total)

    if not by_date:
        return []

    # Compute daily median + volume
    daily = []
    for date_str in sorted(by_date.keys()):
        prices = sorted(by_date[date_str])
        mid = len(prices) // 2
        median = prices[mid] if len(prices) % 2 else (prices[mid - 1] + prices[mid]) / 2
        daily.append({
            "date": date_str,
            "price": round(median, 2),
            "volume": len(prices),
        })

    return daily


@st.cache_data(ttl=3600)
def get_price_history(
    player: str,
    sport: str = "NBA",
    card_type: str = "Any",
    days: int = 365,
) -> list[dict]:
    """Get price history for a player/card combo.

    Strategy:
    1. Check local file cache (24-hour TTL)
    2. If stale/missing, query eBay Finding API for sold items (90-day lookback)
    3. Convert sold listings to daily median prices
    4. Cache the result
    5. Fall back to demo data if eBay returns nothing
    """
    # Try cache first
    cached = _load_cache(player, sport, card_type)
    if cached:
        return cached

    # Query eBay sold listings
    sold = search_ebay_sold(player, sport, card_type, limit=100)
    history = _sold_to_daily_prices(sold)

    if history and len(history) >= 3:
        _save_cache(player, sport, card_type, history)
        return history

    # Not enough real data — return empty instead of fake demo data
    return []


def build_price_chart(
    history: list[dict],
    player_name: str,
    time_range: str = "1Y",
) -> go.Figure:
    """Build a Plotly line chart with volume bars."""
    range_days = {"7d": 7, "30d": 30, "90d": 90, "1Y": 365}.get(time_range, 365)
    cutoff = (datetime.now() - timedelta(days=range_days)).strftime("%Y-%m-%d")
    filtered = [h for h in history if h["date"] >= cutoff]

    if not filtered:
        filtered = history[-30:]

    dates = [h["date"] for h in filtered]
    prices = [h["price"] for h in filtered]
    volumes = [h.get("volume", 1) for h in filtered]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=dates, y=volumes, name="Volume",
        marker_color="rgba(99, 102, 241, 0.3)",
        yaxis="y2",
    ))

    fig.add_trace(go.Scatter(
        x=dates, y=prices, name="Price",
        mode="lines",
        line=dict(color="#22c55e", width=2),
        fill="tozeroy",
        fillcolor="rgba(34, 197, 94, 0.1)",
    ))

    fig.update_layout(
        title=f"{player_name} — Price History ({time_range})",
        xaxis_title="Date",
        yaxis=dict(title="Price ($)", side="left"),
        yaxis2=dict(title="Volume", side="right", overlaying="y", showgrid=False),
        template="plotly_dark",
        height=400,
        margin=dict(l=50, r=50, t=50, b=40),
        legend=dict(x=0.01, y=0.99),
        hovermode="x unified",
    )

    return fig


def build_portfolio_value_chart(portfolio_history: list[dict]) -> go.Figure:
    """Build a Plotly area chart for portfolio value over time."""
    if not portfolio_history:
        fig = go.Figure()
        fig.update_layout(template="plotly_dark", height=300,
                          annotations=[dict(text="No data yet", showarrow=False,
                                            xref="paper", yref="paper", x=0.5, y=0.5)])
        return fig

    dates = [h["date"] for h in portfolio_history]
    values = [h["value"] for h in portfolio_history]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=values, name="Portfolio Value",
        mode="lines",
        line=dict(color="#8b5cf6", width=2),
        fill="tozeroy",
        fillcolor="rgba(139, 92, 246, 0.15)",
    ))

    fig.update_layout(
        title="Portfolio Value Over Time",
        xaxis_title="Date",
        yaxis_title="Value ($)",
        template="plotly_dark",
        height=300,
        margin=dict(l=50, r=50, t=50, b=40),
        hovermode="x unified",
    )

    return fig


def build_sparkline(prices: list[float], width: int = 80, height: int = 20) -> str:
    """Build a tiny inline SVG sparkline from a list of prices."""
    if not prices or len(prices) < 2:
        return ""

    min_p = min(prices)
    max_p = max(prices)
    p_range = max_p - min_p if max_p != min_p else 1

    points = []
    for i, p in enumerate(prices):
        x = (i / (len(prices) - 1)) * width
        y = height - ((p - min_p) / p_range) * height
        points.append(f"{x:.1f},{y:.1f}")

    polyline = " ".join(points)
    color = "#22c55e" if prices[-1] >= prices[0] else "#ef4444"

    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="1.5"/>'
        f'</svg>'
    )


def compute_price_stats(history: list[dict], days: int = 365) -> dict:
    """Compute key price stats from history data."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    filtered = [h for h in history if h["date"] >= cutoff]

    if not filtered:
        return {"high_52w": 0, "low_52w": 0, "current": 0, "change_pct": 0}

    prices = [h["price"] for h in filtered]
    current = prices[-1]
    start = prices[0]
    change_pct = ((current - start) / start * 100) if start > 0 else 0

    return {
        "high_52w": max(prices),
        "low_52w": min(prices),
        "current": current,
        "change_pct": round(change_pct, 1),
    }
