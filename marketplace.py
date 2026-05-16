import streamlit as st
from datetime import datetime, date
from database import EcoMatchDB

db = EcoMatchDB()


# ── Helpers ───────────────────────────────────────────────────────────────────

def expiry_badge(expiry_str):
    if not expiry_str:
        return "expiry-ok", "✅ No Expiry"
    expiry_dt = datetime.strptime(expiry_str, "%Y-%m-%d").date()
    days_left = (expiry_dt - date.today()).days
    if days_left < 0:
        return "expiry-urgent", "❌ EXPIRED"
    if days_left <= 3:
        return "expiry-urgent", f"🚨 {days_left}d left"
    return "expiry-ok", f"✅ {days_left}d left"


def listing_badge_html(listing_type, price=None):
    if listing_type == "sell":
        label = f"💵 RM {float(price):.2f}" if price else "💵 Sell"
        css   = "mp-badge-sell"
    elif listing_type == "exchange":
        label, css = "🔄 Exchange", "mp-badge-exchange"
    else:
        label, css = "🆓 Free", "mp-badge-free"
    return f'<span class="mp-badge {css}">{label}</span>'


# ── Page ──────────────────────────────────────────────────────────────────────

def render_marketplace_page():
    st.markdown(
        """<div class="page-header"><h1>🛒 Marketplace</h1>
        <p>Browse and request items from the community</p></div>""",
        unsafe_allow_html=True,
    )

    # ── CSS injected once ────────────────────────────────────────────────────
    st.markdown("""
    <style>
    /* Badges */
    .mp-badge {
        display: inline-block; font-size: .75rem; font-weight: 700;
        padding: 3px 10px; border-radius: 999px; margin-right: 4px;
    }
    .mp-badge-free     { background:#dcfce7; color:#15803d; border:1px solid #bbf7d0; }
    .mp-badge-exchange { background:#ede9fe; color:#5b21b6; border:1px solid #c4b5fd; }
    .mp-badge-sell     { background:#fef9c3; color:#854d0e; border:1px solid #fde68a; }
    .expiry-ok         { background:#dcfce7; color:#15803d; }
    .expiry-urgent     { background:#fee2e2; color:#dc2626; }
    .mp-badge.expiry-ok, .mp-badge.expiry-urgent { font-size:.75rem; }

    /* Card */
    .mp-card {
        background:#fff; border-radius:14px; border:1px solid #bbf7d0;
        box-shadow:0 1px 3px rgba(0,0,0,.06); padding:16px; margin-bottom:4px;
    }
    .mp-card-title {
        font-family:'Fraunces',serif; font-size:1.15rem; font-weight:600;
        color:#14532d; margin:0 0 10px 0; line-height:1.25;
    }
    .mp-card-meta { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px; align-items:center; }
    .mp-card-row  { font-size:.82rem; color:#404040; margin:4px 0; }
    .mp-card-row strong { color:#166534; }
    .mp-card-desc {
        font-size:.85rem; color:#525252; line-height:1.55;
        margin:10px 0 0 0; padding-top:10px; border-top:1px solid #f0fdf4;
    }
    .mp-card-seller { font-size:.75rem; color:#737373; margin-top:8px; }
    </style>
    """, unsafe_allow_html=True)

    # ── Filters ──────────────────────────────────────────────────────────────
    f1, f2, f3 = st.columns([3, 1, 1])
    search_q    = f1.text_input("", placeholder="🔍 Search items…", key="mp_search")
    filt_region = f2.selectbox(
        "Region",
        ["All Regions", "Johor", "Kedah", "Kelantan", "Melaka", "Negeri Sembilan",
         "Pahang", "Perak", "Perlis", "Pulau Pinang", "Selangor", "Terengganu",
         "Sabah", "Sarawak"],
        key="mp_region",
    )
    filt_type = f3.selectbox(
        "Type",
        ["All Types", "🆓 Free", "🔄 Exchange", "💵 Sell"],
        key="mp_type",
    )

    # ── Fetch ─────────────────────────────────────────────────────────────────
    db_result = db.get_all_items(search=search_q if search_q else None)
    if not db_result["success"]:
        st.error("Could not load items from the database.")
        return

    items = list(db_result["items"])

    # Client-side filters
    if filt_region != "All Regions":
        items = [i for i in items if i.get("region") == filt_region]
    type_map = {"🆓 Free": "free", "🔄 Exchange": "exchange", "💵 Sell": "sell"}
    if filt_type in type_map:
        items = [i for i in items if i.get("listing_type") == type_map[filt_type]]

    if not items:
        st.info("No items found. Try adjusting the filters.")
        return

    st.caption(f"{len(items)} item(s) found")

    # ── Grid ──────────────────────────────────────────────────────────────────
    cols = st.columns(3)
    current_user_id = st.session_state.get("user_id")

    for idx, item in enumerate(items):
        item_id      = item["item_id"]
        listing_type = item.get("listing_type") or "free"
        price        = item.get("price")
        description  = item.get("description") or ""
        region       = item.get("region") or "—"
        category     = item.get("category") or "—"
        condition    = item.get("condition") or "—"
        seller_name  = item.get("seller_name") or "Unknown"
        seller_trust = item.get("seller_trust")

        exp_cls, exp_label = expiry_badge(item.get("expiry_date"))
        badge_html         = listing_badge_html(listing_type, price)
        expiry_badge_html  = f'<span class="mp-badge {exp_cls}">{exp_label}</span>'

        is_own_item = (current_user_id is not None and item.get("user_id") == current_user_id)

        with cols[idx % 3]:
            # Image
            img_url = item.get("image_path")
            if img_url:
                st.image(img_url, use_container_width=True)
            else:
                st.markdown(
                    "<div style='height:160px;background:#f0fdf4;border-radius:10px;"
                    "display:flex;align-items:center;justify-content:center;"
                    "color:#86efac;font-size:2rem;margin-bottom:4px'>📦</div>",
                    unsafe_allow_html=True,
                )

            # Card body — all details
            price_row = (
                f"<div class='mp-card-row'>💰 <strong>Price:</strong> RM {float(price):.2f}</div>"
                if listing_type == "sell" and price
                else ""
            )
            trust_str = f"{seller_trust:.1f}/10" if seller_trust is not None else "—"

            st.markdown(f"""
<div class="mp-card">
    <p class="mp-card-title">{item['item_name']}</p>

    <div class="mp-card-meta">
        {badge_html}
        {expiry_badge_html}
    </div>

    <div class="mp-card-row">📍 <strong>Region:</strong> {region}</div>
    <div class="mp-card-row">🏷️ <strong>Category:</strong> {category}</div>
    <div class="mp-card-row">🔍 <strong>Condition:</strong> {condition}</div>
    {price_row}

    <p class="mp-card-desc">{description[:180]}{"…" if len(description) > 180 else ""}</p>

    <p class="mp-card-seller">👤 Listed by <strong>{seller_name}</strong> · ⭐ {trust_str}</p>
</div>
""", unsafe_allow_html=True)

            # Action button — disabled for own items
            if is_own_item:
                st.button("✏️ Your listing", key=f"own_{item_id}", disabled=True, use_container_width=True)
            else:
                btn_label = (
                    "🛍️ Request to Buy"   if listing_type == "sell"     else
                    "🔄 Offer Exchange"   if listing_type == "exchange" else
                    "🙋 Claim Item"
                )

                # Expander for optional message
                with st.expander(btn_label, expanded=False):
                    msg_key = f"msg_{item_id}"
                    if msg_key not in st.session_state:
                        st.session_state[msg_key] = ""

                    action_word = (
                        "buy"      if listing_type == "sell"     else
                        "exchange" if listing_type == "exchange" else
                        "claim"
                    )
                    msg = st.text_area(
                        "Add a message to the seller (optional)",
                        key=msg_key,
                        placeholder=f"Hi, I'd like to {action_word} this item…",
                        height=80,
                    )
                    confirm_key = f"confirm_{item_id}"
                    if st.button(f"✅ Confirm {btn_label}", key=confirm_key, use_container_width=True):
                        result = db.add_claim(
                            item_id=item_id,
                            claimer_id=current_user_id,
                            message=msg,
                        )
                        if result["success"]:
                            st.success("✅ Request sent! The seller has been notified.")
                        elif result.get("error") == "duplicate":
                            st.warning("⚠️ You already have a pending request for this item.")
                        else:
                            st.error(f"Something went wrong: {result.get('error')}")