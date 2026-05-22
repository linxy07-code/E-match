import streamlit as st
import html
import re
from datetime import datetime, date
from database import EcoMatchDB

db = EcoMatchDB()

# ── Helpers ───────────────────────────────────────────────────────────────────

def expiry_badge(expiry_str):
    if not expiry_str:
        return "expiry-ok", "✅ No Expiry"
    try:
        expiry_dt = datetime.strptime(expiry_str, "%Y-%m-%d").date()
        days_left = (expiry_dt - date.today()).days
        if days_left < 0:
            return "expiry-urgent", "❌ EXPIRED"
        if days_left <= 3:
            return "expiry-urgent", f"🚨 {days_left}d left"
        return "expiry-ok", f"✅ {days_left}d left"
    except ValueError:
        return "expiry-ok", "✅ No Expiry"


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

    /* Card Layout structure */
    .mp-card {
        background:#fff; border-radius:14px; border:1px solid #bbf7d0;
        box-shadow:0 1px 3px rgba(0,0,0,.06); padding:16px; margin-bottom:4px;
        display: flex;
        flex-direction: column;
        height: 100%;
    }
    .mp-card-title {
        font-family:'Fraunces',serif; font-size:1.15rem; font-weight:600;
        color:#14532d; margin:0 0 10px 0; line-height:1.25;
        min-height: 44px;
    }
    .mp-card-meta { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px; align-items:center; }
    .mp-card-row  { font-size:.82rem; color:#404040; margin:4px 0; }
    .mp-card-row strong { color:#166534; }
    
    /* Box spacing parameters for descriptive paragraphs */
    .mp-card-desc {
        font-size:.85rem; color:#525252; line-height:1.55;
        margin:10px 0 4px 0; padding-top:10px; border-top:1px solid #f0fdf4;
    }
    .mp-card-seller { font-size:.75rem; color:#737373; margin-top:8px; margin-bottom:4px; }

    /* Custom Image Canvas Frame */
    .mp-img-frame {
        width: 100%;
        height: 320px; 
        overflow: hidden;
        border-radius: 10px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #f8fafc;
    }
    .mp-img-frame img {
        width: 100%;
        height: 100%;
        object-fit: cover; 
        padding: 0px;
    }

    /* ── PURE CSS PUSH-BUTTON TOGGLE (INSIDE THE CARD CONTAINER) ── */
    .desc-toggle {
        display: none;
    }
    .desc-label {
        color: #a3a3a3; /* Muted gray to make it less visible in color */
        font-size: 0.75rem;
        font-weight: 500;
        cursor: pointer;
        display: inline-block;
        margin-top: 4px;
        text-decoration: underline;
    }
    .desc-label:hover {
        color: #166534; /* Soft green highlight only on hover */
    }
    .desc-full {
        display: none;
    }
    /* Dynamic text segment toggles */
    .desc-toggle:checked ~ .desc-short { display: none; }
    .desc-toggle:checked ~ .desc-full  { display: inline; }
    .desc-toggle:checked ~ .desc-label::after { content: " Less"; }
    .desc-toggle:not(:checked) ~ .desc-label::after { content: " More"; }
    </style>
    """, unsafe_allow_html=True)

    # ── Filters ──────────────────────────────────────────────────────────────
    f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
    search_q = f1.text_input(
    "Search Marketplace Items", 
    placeholder="🔍 Search items…", 
    key="mp_search", 
    label_visibility="collapsed"
)
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
    filt_condition = f4.selectbox(
        "Condition",
        ["All Conditions", "Brand New", "Good", "Second Hand"],
        key="mp_condition"
    )

    # ── Fetch ─────────────────────────────────────────────────────────────────
    db_result = db.get_all_items(search=search_q if search_q else None)
    if not db_result["success"]:
        st.error("Could not load items from the database.")
        return

    items = list(db_result["items"])
    current_user_id = st.session_state.get("user_id")

    # SECURITY FILTER: Hide user's own items
    if current_user_id is not None:
        items = [i for i in items if i.get("user_id") != current_user_id]

    if filt_region != "All Regions":
        items = [i for i in items if i.get("region") == filt_region or (filt_region == "Pulau Pinang" and i.get("region") == "Penang")]
    
    type_map = {"🆓 Free": "free", "🔄 Exchange": "exchange", "💵 Sell": "sell"}
    if filt_type in type_map:
        items = [i for i in items if i.get("listing_type") == type_map[filt_type]]

    # ── Condition Filtering Logic Evaluation ──
    if filt_condition != "All Conditions":
        items = [i for i in items if i.get("condition") == filt_condition]

    if not items:
        st.info("No community items found matching selected filter criteria.")
        return

    st.caption(f"{len(items)} item(s) found")

    # ── Symmetrical Row Grid Rendering Engine ─────────────────────────────────
    row_chunks = [items[i:i + 3] for i in range(0, len(items), 3)]

    for row_items in row_chunks:
        cols_cards = st.columns(3)
        cols_buttons = st.columns(3)
        
        for col_idx, item in enumerate(row_items):
            item_id      = item["item_id"]
            listing_type = item.get("listing_type") or "free"
            price        = item.get("price")
            region       = item.get("region") or "—"
            category     = item.get("category") or "—"
            condition    = item.get("condition") or "—"
            seller_trust = item.get("seller_trust")

            # ── 1. EXTRACT DATA SAFELY FROM DATABASE ──────────────────────────
            raw_desc   = str(item.get('description') or "")
            raw_seller = str(item.get('seller_name') or "Unknown")

            # ── 2. BULLETPROOF REGEX TAG STRIPPER ─────────────────────────────
            if "<p" in raw_desc or "</p>" in raw_desc:
                raw_desc = re.sub(r'<[^>]*>', '', raw_desc).strip()
                
            if "<p" in raw_seller or "</p>" in raw_seller:
                if "Listed by" in raw_seller:
                    match = re.search(r'Listed by\s*<strong>(.*?)</strong>', raw_seller)
                    raw_seller = match.group(1) if match else re.sub(r'<[^>]*>', '', raw_seller)
                else:
                    raw_seller = re.sub(r'<[^>]*>', '', raw_seller)
                    
            raw_seller = raw_seller.replace("👤 Listed by", "").split("·")[0].strip()

            # ── 3. SANITIZE CONTENT OUTPUTS FOR DISPLAY ───────────────────────
            item_name_safe    = html.escape(str(item.get('item_name', '')))
            description_clean = html.escape(raw_desc)
            seller_name_clean = html.escape(raw_seller)

            exp_cls, exp_label = expiry_badge(item.get("expiry_date"))
            badge_html         = listing_badge_html(listing_type, price)
            expiry_badge_html  = f'<span class="mp-badge {exp_cls}">{exp_label}</span>'

            # 📦 RENDERING THE CARD ROW BLOCK
            with cols_cards[col_idx]:
                img_url = item.get("image_path")
                if img_url:
                    st.markdown(f'<div class="mp-img-frame"><img src="{img_url}"></div>', unsafe_allow_html=True)
                else:
                    st.markdown("<div class='mp-img-frame' style='font-size:3rem;'>📦</div>", unsafe_allow_html=True)

                price_row = f"<div class='mp-card-row'>💰 <strong>Price:</strong> RM {float(price):.2f}</div>" if (listing_type == "sell" and price) else ""
                trust_str = f"{float(seller_trust):.1f}/10" if seller_trust is not None else "10.0/10"

                # ── 4. CONDITIONAL HOOK FOR LESS VISIBLE TOGGLES ──────────────
                char_limit = 80
                
                if description_clean:
                    if len(description_clean) <= char_limit:
                        desc_inner_html = f'{description_clean}'
                    else:
                        desc_inner_html = f"""
                        <input type="checkbox" id="toggle_{item_id}" class="desc-toggle">
                        <span class="desc-short">{description_clean[:char_limit]}...</span>
                        <span class="desc-full">{description_clean}</span>
                        <label for="toggle_{item_id}" class="desc-label">Read</label>
                        """
                else:
                    desc_inner_html = '<span style="font-style: italic; color:#a3a3a3;">No description provided.</span>'

                # Complete composite card payload string block execution
                full_card_html = f"""
                <div class="mp-card">
                    <p class="mp-card-title">{item_name_safe}</p>
                    <div class="mp-card-meta">{badge_html}{expiry_badge_html}</div>
                    <div class="mp-card-row">📍 <strong>Region:</strong> {region}</div>
                    <div class="mp-card-row">🏷️ <strong>Category:</strong> {category}</div>
                    <div class="mp-card-row">🔍 <strong>Condition:</strong> {condition}</div>
                    {price_row}
                    <p class="mp-card-seller">👤 Listed by <strong>{seller_name_clean}</strong> · ⭐ {trust_str}</p>
                    <div class="mp-card-desc">{desc_inner_html}</div>
                </div>
                """
                st.markdown(full_card_html, unsafe_allow_html=True) # 🚀 Keep ONLY this line, aligned with full_card_html above!
                

            # 📥 RENDERING THE BUTTON ROW BLOCK
            with cols_buttons[col_idx]:
                btn_label = (
                    "🛍️ Request to Buy"   if listing_type == "sell"     else
                    "🔄 Offer Exchange"   if listing_type == "exchange" else
                    "🙋 Claim Item"
                )

                with st.expander(btn_label, expanded=False):
                    msg_key = f"msg_{item_id}"
                    if msg_key not in st.session_state:
                        st.session_state[msg_key] = ""

                    action_word = "buy" if listing_type == "sell" else "exchange" if listing_type == "exchange" else "claim"
                    msg = st.text_area(
                        "Add a message to the seller (optional)",
                        key=msg_key,
                        placeholder=f"Hi, I'd like to {action_word} this item…",
                        height=80,
                    )
                    
                    if st.button(f"✅ Confirm", key=f"confirm_{item_id}", width="stretch"):
                        if not current_user_id:
                            st.error("⚠️ Please log in to complete requests.")
                        else:
                            result = db.add_claim(
                                item_id=item_id,
                                claimer_id=current_user_id,
                                message=msg,
                            )
                            if result.get("success"):

                                # 🔒 lock item immediately so it disappears from marketplace
                                db.reserve_item(item_id=item_id, user_id=current_user_id)

                                # 🛒 trigger cart popup
                                st.session_state["show_cart_popup"] = True
                                st.session_state["cart_popup_item"] = item.get("item_name", "Item")

                                st.rerun()
                            elif result.get("error") == "duplicate":
                                st.warning("⚠️ You already have a pending request for this item.")
                            else:
                                st.error(f"Something went wrong: {result.get('error')}")
        
        st.write("")