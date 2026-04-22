"""My Collection page."""

import streamlit as st
import plotly.graph_objects as go

from urllib.parse import quote_plus
from modules.ui_helpers import gradient_divider, score_progress_bar, supplies_button, render_fuzzy_suggestions, card_thumbnail, market_signal_badge
from modules.affiliates import supplies_affiliate_url, SUPPLIES_LINKS
from modules.ebay_search import search_ebay_cards
from modules.pokemon_tcg import search_pokemon_cards
from modules.listing_quality import extract_parallel, extract_grade, is_graded
from modules.portfolio import add_card, remove_card, update_card_image, get_portfolio, bulk_import_cards, find_duplicate, increment_quantity
from modules.collection_analytics import compute_collection_analytics, compute_portfolio_timeline, export_portfolio_csv
from modules.trade_analyzer import get_card_market_value
from modules.card_types import get_card_type_options
from modules.price_history import get_price_history, build_portfolio_value_chart, build_sparkline
from modules.collection_insights import (
    compute_set_completion, compute_rarity_distribution,
    compute_investment_timeline, compute_projected_value, compute_diversification_score,
)
from tiers import is_pro, can_access


def render(current_user: str | None):
    st.title("📁 My Collection")
    st.caption("See what you paid, what it's worth now, and whether you're up or down")

    if not current_user:
        st.warning("You're not logged in — your collection won't be saved between sessions. Sign up in the sidebar to keep it.")

    _GRADE_COMPANIES = ["PSA", "BGS", "CGC", "SGC", "HGA"]

    # --- "Add another from set" pre-fill ---
    _prefill_year = st.session_state.pop("search_prefill_year", "")
    _prefill_set = st.session_state.pop("search_prefill_set", "")
    _prefill_sport = st.session_state.pop("search_prefill_sport", "NBA")
    _prefill_player = st.session_state.pop("search_prefill_player", "")

    # Scanner pre-fill
    if st.session_state.get("scanner_to_collection"):
        scan_data = st.session_state.pop("scanner_to_collection")
        _prefill_player = scan_data.get("player_name", "")
        _prefill_year = scan_data.get("year", "")
        _prefill_sport = scan_data.get("sport", "NBA")
        st.session_state["search_auto_trigger"] = True

    # --- Search to Add ---
    st.markdown("**Add a Card**")
    sb1, sb2, sb3, sb4 = st.columns([3, 1.5, 1, 2])
    with sb1:
        search_player = st.text_input("Player Name", value=_prefill_player, placeholder="e.g. Victor Wembanyama", key="search_add_player")
    with sb2:
        search_year = st.text_input("Year (optional)", value=_prefill_year, placeholder="e.g. 2023-24", key="search_add_year")
    with sb3:
        search_cardnum = st.text_input("Card # (optional)", placeholder="e.g. 275", key="search_add_cardnum")
    with sb4:
        _sport_opts = ["NBA", "NFL", "MLB", "Pokemon"]
        _sport_idx = _sport_opts.index(_prefill_sport) if _prefill_sport in _sport_opts else 0
        search_sport = st.radio("Sport", _sport_opts, index=_sport_idx, horizontal=True, key="search_add_sport")

    # Fuzzy suggestion
    if search_player:
        _fz_suggestion = render_fuzzy_suggestions(search_player, search_sport, key_prefix="mc_search_fz")
        if _fz_suggestion:
            st.session_state["search_add_player"] = _fz_suggestion
            st.rerun()

    search_clicked = st.button("Search Cards", type="primary", use_container_width=True)
    auto_trigger = st.session_state.pop("search_auto_trigger", False)

    if search_clicked or auto_trigger:
        if not search_player:
            st.warning("Enter a player name to search.")
        else:
            with st.spinner("Searching for matching cards..."):
                if search_sport == "Pokemon":
                    raw_results = search_pokemon_cards(search_player, set_name=_prefill_set or None, limit=30)
                    # Normalize Pokemon results to common format
                    results = []
                    for p in raw_results:
                        results.append({
                            "title": f"{p['name']} - {p['set_name']} #{p['number']}",
                            "price": p.get("market_price", 0),
                            "image_url": p.get("image_small", ""),
                            "set_name": p.get("set_name", ""),
                            "card_number": p.get("number", ""),
                            "year": p.get("set_release_date", "")[:4] if p.get("set_release_date") else "",
                            "variant": p.get("rarity", "Base"),
                            "sport": "Pokemon",
                            "player_name": p.get("name", search_player),
                        })
                else:
                    query = search_player
                    if search_year:
                        query = f"{search_year} {query}"
                    raw_results = search_ebay_cards(query, search_sport, "Any", year=search_year or None, limit=30)
                    results = []
                    for r in raw_results:
                        variant = extract_parallel(r["title"])
                        grade_info = extract_grade(r["title"])
                        results.append({
                            "title": r["title"],
                            "price": r.get("total", r.get("price", 0)),
                            "image_url": r.get("image_url", ""),
                            "set_name": _prefill_set or "",
                            "card_number": search_cardnum or "",
                            "year": search_year or "",
                            "variant": variant,
                            "grade_detected": grade_info,
                            "sport": search_sport,
                            "player_name": search_player,
                            "ebay_url": r.get("url", ""),
                        })

            # Filter by card number if provided
            if search_cardnum:
                filtered = [r for r in results if search_cardnum in r.get("title", "")]
                if filtered:
                    results = filtered

            st.session_state["search_add_results"] = results
            st.session_state["search_add_meta"] = {
                "player": search_player, "year": search_year,
                "sport": search_sport, "set": _prefill_set,
            }

    # --- Display search results ---
    results = st.session_state.get("search_add_results", [])
    if results:
        st.markdown(f"**Found {len(results)} cards** — click one to add it")
        for row_start in range(0, min(len(results), 12), 3):
            row = results[row_start:row_start + 3]
            cols = st.columns(3)
            for j, card_result in enumerate(row):
                with cols[j]:
                    # Thumbnail
                    img_url = card_result.get("image_url", "")
                    if img_url:
                        st.markdown(card_thumbnail(img_url), unsafe_allow_html=True)

                    # Title (truncated)
                    title = card_result.get("title", "")
                    display_title = title[:60] + "..." if len(title) > 60 else title
                    st.markdown(f"**{display_title}**")

                    # Badges
                    badges = ""
                    variant = card_result.get("variant", "base")
                    if variant and variant != "base":
                        badges += f'<span style="background:#7c3aed;color:#fff;padding:2px 6px;border-radius:4px;font-size:0.75em;margin-right:4px;">{variant.replace("_", " ").title()}</span>'
                    grade_det = card_result.get("grade_detected")
                    if grade_det:
                        badges += f'<span style="background:#3b82f6;color:#fff;padding:2px 6px;border-radius:4px;font-size:0.75em;">{grade_det}</span>'
                    if badges:
                        st.markdown(badges, unsafe_allow_html=True)

                    price = card_result.get("price", 0)
                    if price > 0:
                        st.caption(f"${price:.2f}")

                    if st.button("Add This Card", key=f"add_result_{row_start + j}", use_container_width=True):
                        st.session_state["confirm_add_card"] = card_result
                        st.rerun()

        if len(results) > 12:
            st.caption(f"Showing 12 of {len(results)} results")

    # --- Confirmation Panel ---
    confirm_card = st.session_state.get("confirm_add_card")
    if confirm_card:
        st.markdown("---")
        st.markdown("### Confirm & Add to Collection")

        cf1, cf2 = st.columns([1, 2])
        with cf1:
            img = confirm_card.get("image_url", "")
            if img:
                st.markdown(card_thumbnail(img), unsafe_allow_html=True)
        with cf2:
            st.markdown(f"**{confirm_card.get('title', '')}**")
            variant = confirm_card.get("variant", "base")
            if variant and variant != "base":
                st.caption(f"Variant: {variant.replace('_', ' ').title()}")

        # Auto-populated fields
        cp1, cp2, cp3 = st.columns(3)
        with cp1:
            conf_player = st.text_input("Player", value=confirm_card.get("player_name", ""), key="conf_player")
        with cp2:
            conf_year = st.text_input("Year", value=confirm_card.get("year", ""), key="conf_year")
        with cp3:
            conf_cardnum = st.text_input("Card #", value=confirm_card.get("card_number", ""), key="conf_cardnum")

        cp4, cp5 = st.columns(2)
        with cp4:
            conf_set = st.text_input("Set", value=confirm_card.get("set_name", ""), key="conf_set")
        with cp5:
            conf_variant = st.text_input("Variant", value=variant.replace("_", " ").title() if variant != "base" else "Base", key="conf_variant")

        # Raw / Graded toggle
        grade_det = confirm_card.get("grade_detected")
        default_graded = grade_det is not None
        conf_condition = st.radio("Condition", ["Raw", "Graded"], index=1 if default_graded else 0, horizontal=True, key="conf_condition")

        conf_grade_co = None
        conf_grade_val = None
        if conf_condition == "Graded":
            gc1, gc2 = st.columns(2)
            with gc1:
                # Try to pre-fill from detected grade
                default_co_idx = 0
                if grade_det:
                    for i, co in enumerate(_GRADE_COMPANIES):
                        if co.lower() in grade_det.lower():
                            default_co_idx = i
                            break
                conf_grade_co = st.selectbox("Grading Company", _GRADE_COMPANIES, index=default_co_idx, key="conf_grade_co")
            with gc2:
                default_grade = ""
                if grade_det:
                    import re
                    _gm = re.search(r'(\d+\.?\d*)', grade_det)
                    if _gm:
                        default_grade = _gm.group(1)
                conf_grade_val = st.text_input("Grade", value=default_grade, placeholder="e.g. 10, 9.5", key="conf_grade_val")

        # Purchase price — pre-fill with market avg_sold
        _prefill_price = confirm_card.get("price", 0)
        # Try to get actual sold price
        if conf_player:
            _market_key = f"_market_{conf_player}_{confirm_card.get('sport', '')}"
            if _market_key not in st.session_state:
                with st.spinner("Looking up sold prices..."):
                    _mkt = get_card_market_value(
                        conf_player, confirm_card.get("sport", "NBA"), conf_variant or "Base",
                        year=conf_year or None, set_name=conf_set or None,
                    )
                    st.session_state[_market_key] = _mkt
            else:
                _mkt = st.session_state[_market_key]

            if _mkt.get("avg_sold", 0) > 0:
                _prefill_price = _mkt["avg_sold"]
                st.markdown(market_signal_badge(_mkt.get("market_signal", "N/A")), unsafe_allow_html=True)
                st.caption(f"Pre-filled with avg sold price (${_mkt['avg_sold']:.2f})")

        pp1, pp2 = st.columns(2)
        with pp1:
            conf_price = st.number_input("Purchase Price ($)", min_value=0.0, value=round(_prefill_price, 2), step=1.0, key="conf_price")
        with pp2:
            conf_date = st.date_input("Purchase Date", key="conf_date")

        # Duplicate check
        _dup = find_duplicate(conf_player, conf_year or None, conf_cardnum or None, confirm_card.get("sport", "NBA"))
        if _dup:
            st.warning(f"You already have this card (qty: {_dup.get('quantity', 1)}). Increase quantity instead?")
            dc1, dc2 = st.columns(2)
            with dc1:
                if st.button("Yes, increase quantity", key="dup_inc", use_container_width=True):
                    increment_quantity(_dup["id"])
                    st.success(f"Increased {conf_player} quantity to {_dup.get('quantity', 1) + 1}!")
                    st.session_state.pop("confirm_add_card", None)
                    st.session_state.pop("search_add_results", None)
                    st.rerun()
            with dc2:
                if st.button("No, add as new card", key="dup_new", use_container_width=True):
                    st.session_state["force_add_new"] = True
                    st.rerun()

        # Confirm & Add button
        can_add = not _dup or st.session_state.pop("force_add_new", False)
        if can_add:
            if st.button("Confirm & Add", type="primary", use_container_width=True, key="confirm_add_btn"):
                if not conf_player:
                    st.warning("Player name is required.")
                else:
                    if not is_pro():
                        from config.settings import FREE_TIER_LIMITS
                        current_count = len(get_portfolio())
                        max_cards = FREE_TIER_LIMITS.get("portfolio_max_cards", 25)
                        if current_count >= max_cards:
                            st.error(f"Free accounts can hold {max_cards} cards. Upgrade to Pro for unlimited.")
                            st.stop()

                    add_card(
                        conf_player,
                        confirm_card.get("sport", "NBA"),
                        conf_variant or "Base",
                        conf_price,
                        str(conf_date),
                        1,
                        year=conf_year or None,
                        set_name=conf_set or None,
                        card_number=conf_cardnum or None,
                        variant=conf_variant or None,
                        grade_company=conf_grade_co,
                        grade_value=conf_grade_val,
                        image_url=confirm_card.get("image_url") or None,
                    )
                    st.success(f"Added {conf_player} to your collection!")
                    # Set up "Add another from this set" shortcut
                    if conf_set:
                        st.session_state["last_added_set"] = conf_set
                        st.session_state["last_added_year"] = conf_year
                        st.session_state["last_added_sport"] = confirm_card.get("sport", "NBA")
                    st.session_state.pop("confirm_add_card", None)
                    st.session_state.pop("search_add_results", None)
                    st.rerun()

        if st.button("Cancel", key="cancel_confirm"):
            st.session_state.pop("confirm_add_card", None)
            st.rerun()

    # --- "Add another from this set" shortcut ---
    _last_set = st.session_state.pop("last_added_set", None)
    _last_year = st.session_state.pop("last_added_year", None)
    _last_sport = st.session_state.pop("last_added_sport", None)
    if _last_set:
        if st.button(f"Add another from {_last_set}", key="add_another_set", use_container_width=True):
            st.session_state["search_prefill_year"] = _last_year or ""
            st.session_state["search_prefill_set"] = _last_set
            st.session_state["search_prefill_sport"] = _last_sport or "NBA"
            st.rerun()

    # --- Manual add fallback ---
    with st.expander("Can't find your card? Add manually"):
        with st.form("manual_add_card_form", clear_on_submit=True):
            ac1, ac2, ac3 = st.columns(3)
            with ac1:
                pf_player = st.text_input("Player Name", placeholder="e.g. Victor Wembanyama", key="manual_player")
            with ac2:
                pf_sport = st.selectbox("Sport", ["NBA", "NFL", "MLB", "Pokemon"], key="manual_sport")
            with ac3:
                pf_type = st.selectbox("Card Type", get_card_type_options(), key="manual_type")

            ac4, ac5, ac6 = st.columns(3)
            with ac4:
                pf_year = st.text_input("Year", placeholder="e.g. 2023-24", key="manual_year")
            with ac5:
                pf_set = st.text_input("Set", placeholder="e.g. Prizm", key="manual_set")
            with ac6:
                pf_cardnum = st.text_input("Card #", placeholder="e.g. 275", key="manual_cardnum")

            ac7, ac8, ac9 = st.columns(3)
            with ac7:
                pf_price = st.number_input("Purchase Price ($)", min_value=0.0, step=1.0, key="manual_price")
            with ac8:
                pf_date = st.date_input("Purchase Date", key="manual_date")
            with ac9:
                pf_qty = st.number_input("Quantity", min_value=1, value=1, step=1, key="manual_qty")

            gc1, gc2 = st.columns(2)
            with gc1:
                pf_grade_company = st.selectbox("Grading Company", [""] + _GRADE_COMPANIES, key="manual_grade_co",
                                                help="Leave blank for raw/ungraded cards")
            with gc2:
                pf_grade_value = st.text_input("Grade", placeholder="e.g. 10, 9.5, 9", key="manual_grade_val",
                                               help="PSA: 1-10 | BGS/CGC/SGC: 1-10 with half grades")

            pf_submit = st.form_submit_button("Add to Collection")

        if pf_submit and pf_player and pf_price > 0:
            if not is_pro():
                from config.settings import FREE_TIER_LIMITS
                current_count = len(get_portfolio())
                max_cards = FREE_TIER_LIMITS.get("portfolio_max_cards", 25)
                if current_count >= max_cards:
                    st.error(f"Free accounts can hold {max_cards} cards. Upgrade to Pro for unlimited.")
                    st.stop()
            add_card(
                pf_player, pf_sport, pf_type, pf_price, str(pf_date), pf_qty,
                year=pf_year or None,
                set_name=pf_set or None,
                card_number=pf_cardnum or None,
                grade_company=pf_grade_company or None,
                grade_value=pf_grade_value or None,
            )
            st.success(f"Added {pf_player} to your collection!")
            st.rerun()

    # --- CSV Import Section ---
    with st.expander("Import Collection (CSV)"):
        st.caption("Upload a CSV exported from another app (Ludex, CollX, TCDB, Cardbase, etc.)")
        uploaded = st.file_uploader("Choose a CSV file", type=["csv"], key="csv_import")
        if uploaded is not None:
            import pandas as pd
            try:
                df = pd.read_csv(uploaded)
            except Exception as e:
                st.error(f"Could not read CSV: {e}")
                df = None

            if df is not None and not df.empty:
                # Normalize headers
                col_map_raw = {c: c.strip().lower().replace("_", " ") for c in df.columns}
                df.columns = [col_map_raw[c] for c in df.columns]

                # Column matching patterns
                PATTERNS = {
                    "player_name": ["player", "player name", "name"],
                    "year": ["year", "card year"],
                    "set_name": ["set", "set name", "brand", "product"],
                    "card_number": ["card number", "card num", "card #", "number", "#"],
                    "card_type": ["card type", "type", "category type"],
                    "variant": ["variant", "parallel", "insert", "refractor"],
                    "sport": ["sport", "category"],
                    "value": ["value", "price", "estimated value", "est value", "market value"],
                    "quantity": ["quantity", "qty", "count"],
                    "grade": ["grade", "condition", "graded"],
                }

                def _match_column(patterns, columns):
                    """Find the best matching column: exact first, then substring."""
                    for p in patterns:
                        for c in columns:
                            if c == p:
                                return c
                    for p in patterns:
                        for c in columns:
                            if p in c:
                                return c
                    return None

                detected = {}
                for field, pats in PATTERNS.items():
                    match = _match_column(pats, list(df.columns))
                    if match:
                        detected[field] = match

                if "player_name" not in detected:
                    st.error("Could not find a player name column. Make sure your CSV has a column like 'Player', 'Player Name', or 'Name'.")
                else:
                    # Show detected mapping
                    st.markdown("**Detected column mapping:**")
                    mapping_text = "  \n".join(
                        f"- **{field}** ← `{col}`" for field, col in detected.items()
                    )
                    st.markdown(mapping_text)

                    # Build preview
                    preview_cols = [detected[f] for f in detected if detected[f] in df.columns]
                    preview_df = df[preview_cols].head(10)
                    st.markdown(f"**Preview** (first {min(10, len(df))} of {len(df)} cards):")
                    st.dataframe(preview_df, use_container_width=True)

                    # Tier limit check
                    from config.settings import FREE_TIER_LIMITS
                    current_count = len(get_portfolio())
                    max_cards = None
                    warning_msg = ""
                    if not is_pro():
                        max_cards = FREE_TIER_LIMITS.get("portfolio_max_cards", 25)
                        remaining = max(0, max_cards - current_count)
                        if remaining < len(df):
                            warning_msg = f"Free tier limit: {max_cards} cards. You have {current_count}, so only the first {remaining} of {len(df)} cards will be imported. Upgrade to Pro for unlimited."
                            st.warning(warning_msg)

                    st.markdown(f"**Ready to import {len(df)} cards.**")
                    if st.button("Import All", key="csv_import_btn", type="primary"):
                        from datetime import datetime as _dt
                        today = str(_dt.now().date())

                        card_list = []
                        for _, row in df.iterrows():
                            # Resolve card_type: prefer card_type column, fall back to variant, then "Base"
                            if detected.get("card_type"):
                                ct = str(row.get(detected["card_type"], "Base"))
                            elif detected.get("variant"):
                                ct = str(row.get(detected["variant"], "Base"))
                            else:
                                ct = "Base"

                            card = {
                                "player_name": str(row.get(detected.get("player_name", ""), "")),
                                "sport": str(row.get(detected.get("sport", ""), "NBA")) if detected.get("sport") else "NBA",
                                "card_type": ct,
                                "purchase_price": float(row.get(detected.get("value", ""), 0) or 0),
                                "purchase_date": today,
                                "quantity": int(row.get(detected.get("quantity", ""), 1) or 1),
                                "year": str(row.get(detected.get("year", ""), "")) if detected.get("year") else None,
                                "set_name": str(row.get(detected.get("set_name", ""), "")) if detected.get("set_name") else None,
                                "card_number": str(row.get(detected.get("card_number", ""), "")) if detected.get("card_number") else None,
                                "variant": str(row.get(detected.get("variant", ""), "")) if detected.get("variant") else None,
                            }
                            # Clean up "nan" strings from pandas
                            for k in ["year", "set_name", "card_number", "variant"]:
                                if card[k] and card[k].lower() == "nan":
                                    card[k] = None
                            card_list.append(card)

                        result = bulk_import_cards(card_list, max_allowed=max_cards)
                        if result["limit_hit"]:
                            st.warning(f"Imported {result['imported']} cards. {result['skipped']} skipped (tier limit reached). Upgrade to Pro for unlimited.")
                        elif result["skipped"] > 0:
                            st.success(f"Imported {result['imported']} cards. {result['skipped']} skipped (missing player name or errors).")
                        else:
                            st.success(f"Successfully imported {result['imported']} cards!")
                        st.rerun()

    gradient_divider()

    portfolio = get_portfolio()

    if not portfolio:
        st.markdown("""
        <div style="text-align:center; padding:30px 20px; border:1px dashed #3b4560; border-radius:12px; margin:10px 0;">
            <div style="font-size:2em; margin-bottom:8px;">📁</div>
            <p style="font-size:1.1em;">Your collection is empty</p>
            <p style="color:#9ca3af;">Here's what it looks like once you start adding cards:</p>
        </div>
        """, unsafe_allow_html=True)

        # Example portfolio row to show value
        st.markdown(
            '<div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:12px 16px;margin:10px 0;">'
            '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">'
            '<div><strong>Victor Wembanyama</strong> (Rookie) &bull; NBA</div>'
            '<div style="display:flex;gap:20px;">'
            '<span>Cost: <strong>$45.00</strong></span>'
            '<span>Now: <strong>$62.50</strong></span>'
            '<span class="pl-positive">+$17.50 (+38.9%)</span>'
            '</div></div></div>',
            unsafe_allow_html=True,
        )
        st.caption("(Example — add your first card to start tracking real P&L)")

        gradient_divider()
        st.markdown("**Get started:**")
        _es1, _es2, _es3 = st.columns(3)
        with _es1:
            if st.button("📷 Scan a Card", use_container_width=True, key="empty_scan"):
                st.session_state.nav_target = "📷 Card Scanner"
                st.rerun()
        with _es2:
            if st.button("🔍 Search a Player", use_container_width=True, key="empty_search"):
                st.session_state.nav_target = "🔍 Player Search"
                st.rerun()
        with _es3:
            st.markdown(
                '<p style="text-align:center;color:#9ca3af;padding-top:8px;">'
                'Or use the form above to add manually</p>',
                unsafe_allow_html=True,
            )
        return

    # --- View Toggle & Filters ---
    vt1, vt2, vt3 = st.columns([1, 1, 2])
    with vt1:
        view_mode = st.radio("View", ["List", "Grid"], horizontal=True, key="coll_view_mode")
    with vt2:
        if st.button("Refresh Market Values", use_container_width=True):
            st.session_state.portfolio_values = {}
            st.rerun()

    with st.expander("Filters"):
        flt1, flt2, flt3, flt4 = st.columns(4)
        with flt1:
            _all_sports = sorted(set(c.get("sport", "") for c in portfolio))
            flt_sports = st.multiselect("Sport", _all_sports, default=_all_sports, key="coll_flt_sport")
        with flt2:
            flt_condition = st.selectbox("Condition", ["All", "Graded", "Raw"], key="coll_flt_cond")
        with flt3:
            flt_min_val = st.number_input("Min Value ($)", min_value=0.0, value=0.0, step=5.0, key="coll_flt_min")
        with flt4:
            flt_sort = st.selectbox("Sort By", ["Name", "Value", "P&L %", "Date", "Sport"], key="coll_flt_sort")

    # Fetch market values
    if "portfolio_values" not in st.session_state:
        st.session_state.portfolio_values = {}

    missing = [c for c in portfolio if c["id"] not in st.session_state.portfolio_values]
    if missing:
        with st.spinner(f"Looking up market values for {len(missing)} card(s)..."):
            for card in missing:
                market = get_card_market_value(
                    card["player_name"], card["sport"], card["card_type"],
                    year=card.get("year"), set_name=card.get("set_name"),
                )
                val = market["avg_sold"] if market["avg_sold"] > 0 else market["avg_active"]
                st.session_state.portfolio_values[card["id"]] = val
                # Save card image if we got one and the card doesn't have one yet
                if market.get("image_url") and not card.get("image_url"):
                    update_card_image(card["id"], market["image_url"])
                    card["image_url"] = market["image_url"]  # update in-memory too

    analytics = compute_collection_analytics(portfolio, st.session_state.portfolio_values)

    st.markdown(f"*{analytics['summary_statement']}*")

    sm1, sm2, sm3 = st.columns(3)
    sm1.metric("Total Invested", f"${analytics['total_invested']:,.2f}")
    sm2.metric("Current Value", f"${analytics['total_current']:,.2f}")
    pl_color = "normal" if analytics["total_pl"] >= 0 else "inverse"
    sm3.metric("Total P&L", f"${analytics['total_pl']:,.2f}", f"{analytics['pl_pct']:+.1f}%", delta_color=pl_color)

    em1, em2, em3, em4 = st.columns(4)
    em1.metric("Total Cards", analytics["total_cards"])
    em2.metric("Avg Card Value", f"${analytics['avg_card_value']:,.2f}")
    if analytics["top_gainer"]:
        tg = analytics["top_gainer"]
        em3.metric("Top Gainer", tg["player_name"], f"{tg['pl_pct']:+.1f}%")
    else:
        em3.metric("Top Gainer", "—")
    if analytics["biggest_dip"]:
        bd = analytics["biggest_dip"]
        em4.metric("Biggest Dip", bd["player_name"], f"{bd['pl_pct']:+.1f}%", delta_color="inverse")
    else:
        em4.metric("Biggest Dip", "—")

    portfolio_timeline = compute_portfolio_timeline(portfolio, st.session_state.portfolio_values)
    if portfolio_timeline:
        pv_fig = build_portfolio_value_chart(portfolio_timeline)
        st.plotly_chart(pv_fig, use_container_width=True)

    if analytics["sport_breakdown"]:
        st.markdown("**Value by Sport**")
        sports = list(analytics["sport_breakdown"].keys())
        values = list(analytics["sport_breakdown"].values())
        pie_colors = {"NBA": "#f97316", "NFL": "#22c55e", "MLB": "#3b82f6", "Pokemon": "#ed64a6"}
        fig_pie = go.Figure(data=[go.Pie(
            labels=sports, values=values,
            marker=dict(colors=[pie_colors.get(s, "#6b7280") for s in sports]),
            textinfo="label+percent",
            hole=0.4,
        )])
        fig_pie.update_layout(
            template="plotly_dark", height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    if can_access("csv_export"):
        csv_data = export_portfolio_csv(portfolio, st.session_state.portfolio_values)
        st.download_button(
            label="Download Portfolio CSV",
            data=csv_data,
            file_name="card_shark_portfolio.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        if st.button("Download CSV (Pro)", use_container_width=True, disabled=True):
            pass
        st.caption("Upgrade to Pro to export your collection")

    gradient_divider()

    # --- Apply Filters ---
    filtered_portfolio = portfolio
    if flt_sports:
        filtered_portfolio = [c for c in filtered_portfolio if c.get("sport", "") in flt_sports]
    if flt_condition == "Graded":
        filtered_portfolio = [c for c in filtered_portfolio if c.get("grade_company")]
    elif flt_condition == "Raw":
        filtered_portfolio = [c for c in filtered_portfolio if not c.get("grade_company")]
    if flt_min_val > 0:
        filtered_portfolio = [c for c in filtered_portfolio
                              if st.session_state.portfolio_values.get(c["id"], 0) * c.get("quantity", 1) >= flt_min_val]

    # Sort
    def _sort_key(c):
        mv = st.session_state.portfolio_values.get(c["id"], 0) * c.get("quantity", 1)
        cost = c.get("purchase_price", 0) * c.get("quantity", 1)
        pl_pct = ((mv - cost) / cost * 100) if cost > 0 else 0
        if flt_sort == "Value":
            return -mv
        elif flt_sort == "P&L %":
            return -pl_pct
        elif flt_sort == "Date":
            return c.get("purchase_date", "")
        elif flt_sort == "Sport":
            return c.get("sport", "")
        return c.get("player_name", "").lower()

    filtered_portfolio = sorted(filtered_portfolio, key=_sort_key)

    if len(filtered_portfolio) < len(portfolio):
        st.caption(f"Showing {len(filtered_portfolio)} of {len(portfolio)} cards")

    # --- Grid View ---
    if view_mode == "Grid":
        _SPORT_ICONS = {"NBA": "🏀", "NFL": "🏈", "MLB": "⚾", "Pokemon": "⚡"}
        for row_start in range(0, len(filtered_portfolio), 3):
            row_cards = filtered_portfolio[row_start:row_start + 3]
            cols = st.columns(3)
            for j, card in enumerate(row_cards):
                current_val = st.session_state.portfolio_values.get(card["id"], 0)
                qty = card.get("quantity", 1)
                cost = card["purchase_price"] * qty
                market_val = current_val * qty
                pl = market_val - cost
                pl_pct = (pl / cost * 100) if cost > 0 else 0
                pl_color = "#22c55e" if pl >= 0 else "#ef4444"
                pl_sign = "+" if pl >= 0 else ""

                # Grade badge
                grade_html = ""
                if card.get("grade_company") and card.get("grade_value"):
                    grade_html = (
                        f'<span style="background:#3b82f6;color:#fff;padding:2px 6px;'
                        f'border-radius:4px;font-size:0.75em;font-weight:bold;">'
                        f'{card["grade_company"]} {card["grade_value"]}</span> '
                    )

                # Image or placeholder
                img_url = card.get("image_url", "")
                sport_icon = _SPORT_ICONS.get(card.get("sport", ""), "🃏")
                if img_url:
                    img_html = f'<img src="{img_url}" style="width:100%;height:160px;object-fit:cover;border-radius:8px 8px 0 0;" />'
                else:
                    img_html = (
                        f'<div style="width:100%;height:160px;background:linear-gradient(135deg,#1a1f2e,#2d3748);'
                        f'border-radius:8px 8px 0 0;display:flex;align-items:center;justify-content:center;'
                        f'font-size:3em;">{sport_icon}</div>'
                    )

                with cols[j]:
                    st.markdown(
                        f'<div style="border:1px solid #3b4560;border-radius:12px;overflow:hidden;'
                        f'transition:transform 0.2s,box-shadow 0.2s;margin-bottom:8px;">'
                        f'{img_html}'
                        f'<div style="padding:10px 12px;">'
                        f'{grade_html}'
                        f'<strong>{card["player_name"]}</strong><br>'
                        f'<span style="color:#9ca3af;font-size:0.85em;">'
                        f'{card.get("card_type", "Base")} &bull; {card.get("sport", "")}</span><br>'
                        f'<span style="font-size:1.1em;font-weight:bold;">${market_val:.2f}</span> '
                        f'<span style="color:{pl_color};font-size:0.85em;">'
                        f'{pl_sign}${pl:.2f} ({pl_sign}{pl_pct:.1f}%)</span>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )
                    if st.button("Remove", key=f"grid_rm_{card['id']}"):
                        remove_card(card["id"])
                        st.session_state.portfolio_values.pop(card["id"], None)
                        st.rerun()
    else:
        # --- List View (original) ---
        for card in filtered_portfolio:
            current_val = st.session_state.portfolio_values.get(card["id"], 0)
            qty = card.get("quantity", 1)
            cost = card["purchase_price"] * qty
            market_val = current_val * qty
            pl = market_val - cost
            pl_pct = (pl / cost * 100) if cost > 0 else 0

            # Grade badge for list view
            grade_tag = ""
            if card.get("grade_company") and card.get("grade_value"):
                grade_tag = f" [{card['grade_company']} {card['grade_value']}]"

            card_history = get_price_history(card["player_name"], card["sport"], card["card_type"], days=30)
            spark_prices = [h["price"] for h in card_history[-14:]]
            spark_svg = build_sparkline(spark_prices)

            pc0, pc1, pc2, pc3, pc4, pc5, pc6, pc7, pc8 = st.columns([2.5, 0.8, 1, 1, 1, 1, 0.8, 0.7, 0.4])
            with pc0:
                st.write(f"**{card['player_name']}** ({card['card_type']}){grade_tag} • {card['sport']}")
            with pc1:
                if spark_svg:
                    st.markdown(spark_svg, unsafe_allow_html=True)
            with pc2:
                st.write(f"${cost:.2f}")
            with pc3:
                st.write(f"${market_val:.2f}")
            with pc4:
                css = "pl-positive" if pl >= 0 else "pl-negative"
                st.markdown(f'<span class="{css}">${pl:+.2f}</span>', unsafe_allow_html=True)
            with pc5:
                css = "pl-positive" if pl_pct >= 0 else "pl-negative"
                st.markdown(f'<span class="{css}">{pl_pct:+.1f}%</span>', unsafe_allow_html=True)
            with pc6:
                st.caption(card.get("purchase_date", ""))
            with pc7:
                sell_title_parts = [card["player_name"]]
                if card.get("year"):
                    sell_title_parts.append(card["year"])
                if card.get("set_name"):
                    sell_title_parts.append(card["set_name"])
                if card.get("card_type") and card["card_type"] != "Any":
                    sell_title_parts.append(card["card_type"])
                sell_title_parts.append(card["sport"])
                sell_title_parts.append("Card")
                sell_query = quote_plus(" ".join(sell_title_parts))
                sell_url_raw = f"https://www.ebay.com/sell/create?title={sell_query}"
                from modules.affiliates import affiliate_url as _aff_url
                sell_url = _aff_url(sell_url_raw)
                st.markdown(f'<a href="{sell_url}" target="_blank" class="ebay-btn" style="font-size:0.75em;padding:3px 10px;">Sell</a>', unsafe_allow_html=True)
            with pc8:
                if st.button("X", key=f"rm_pf_{card['id']}"):
                    remove_card(card["id"])
                    st.session_state.portfolio_values.pop(card["id"], None)
                    st.rerun()

    # Collection Insights
    gradient_divider()
    st.markdown("### Collection Insights")

    set_comp = compute_set_completion(portfolio)
    if set_comp:
        st.markdown("**Set Completion**")
        for sc in set_comp[:10]:
            sci1, sci2, sci3 = st.columns([3, 1, 1])
            with sci1:
                st.write(sc["set_key"])
            with sci2:
                st.write(f"{sc['count']} cards")
            with sci3:
                st.markdown(score_progress_bar(sc["completion_pct"]), unsafe_allow_html=True)

    rarity_dist = compute_rarity_distribution(portfolio)
    if rarity_dist:
        st.markdown("**Card Type Distribution**")
        rd_fig = go.Figure(data=[go.Pie(
            labels=list(rarity_dist.keys()),
            values=list(rarity_dist.values()),
            textinfo="label+value",
            hole=0.3,
        )])
        rd_fig.update_layout(
            template="plotly_dark", height=280,
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
        )
        st.plotly_chart(rd_fig, use_container_width=True)

    inv_timeline = compute_investment_timeline(portfolio)
    if inv_timeline:
        st.markdown("**Investment Timeline**")
        inv_dates = [t["date"] for t in inv_timeline]
        inv_values = [t["cumulative_spent"] for t in inv_timeline]
        inv_fig = go.Figure()
        inv_fig.add_trace(go.Scatter(
            x=inv_dates, y=inv_values, mode="lines+markers",
            line=dict(color="#f97316", width=2),
            fill="tozeroy", fillcolor="rgba(249, 115, 22, 0.1)",
        ))
        inv_fig.update_layout(
            template="plotly_dark", height=250,
            xaxis_title="Date", yaxis_title="Cumulative Spent ($)",
            margin=dict(l=50, r=20, t=20, b=40),
        )
        st.plotly_chart(inv_fig, use_container_width=True)

    st.markdown("**Projected Value**")
    proj_growth = st.slider("Annual Growth Rate (%)", 0, 50, 10, key="proj_growth") / 100
    proj_months = st.select_slider("Projection Horizon", [6, 12, 24, 36], value=12, key="proj_months")
    projection = compute_projected_value(portfolio, st.session_state.portfolio_values, proj_growth, proj_months)
    pj1, pj2, pj3 = st.columns(3)
    pj1.metric("Current Value", f"${projection['current_value']:,.2f}")
    pj2.metric(f"Projected ({proj_months}mo)", f"${projection['projected_value']:,.2f}")
    pj3.metric("Projected Gain", f"${projection['projected_gain']:,.2f}")

    gradient_divider()
    div_score = compute_diversification_score(portfolio)
    st.markdown("**Diversification Score**")
    ds1, ds2, ds3, ds4 = st.columns(4)
    ds1.metric("Overall", f"{div_score['total_score']}/100")
    ds2.metric("Sport", f"{div_score['sport_score']}/35")
    ds3.metric("Era", f"{div_score['era_score']}/35")
    ds4.metric("Type", f"{div_score['type_score']}/30")
    st.markdown(score_progress_bar(div_score["total_score"]), unsafe_allow_html=True)
    for suggestion in div_score["suggestions"]:
        st.caption(f"- {suggestion}")

    # --- Protect Your Collection (supplies affiliates) ---
    gradient_divider()
    st.markdown("### Protect Your Collection")
    sup1, sup2, sup3 = st.columns(3)
    for col, key in zip([sup1, sup2, sup3], ["bcw", "zion", "cardshellz"]):
        info = SUPPLIES_LINKS[key]
        url = supplies_affiliate_url(key)
        with col:
            st.markdown(f"**{info['name']}**")
            st.caption(info["description"])
            st.markdown(supplies_button(url, "Shop"), unsafe_allow_html=True)


