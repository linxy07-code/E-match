# c_marketplace.py
import streamlit as st
import html
import re
from datetime import datetime, date
from c_styles import COMPANY_CSS  # Uses your company specific style loader if needed

# ── Helpers ───────────────────────────────────────────────────────────────────

def _expiry_badge(expiry_str):
    if not expiry_str:
        return "expiry-ok", "✅ No Expiry"
    try:
        if "EXPIRED" in str(expiry_str):
            return "expiry-urgent", "❌ EXPIRED"
        
        expiry_dt = datetime.strptime(str(expiry_str), "%Y-%m-%d").date()
        days_left = (expiry_dt - date.today()).days
        if days_left < 0:
            return "expiry-urgent", "❌ EXPIRED"
        if days_left <= 3:
            return "expiry-urgent", f"🚨 {days_left}d left"
        return "expiry-ok", f"✅ {days_left}d left"
    except ValueError:
        return "expiry-ok", "✅ No Expiry"


def _lt_badge(listing_type, price=None):
    if listing_type == "sell":
        label = f"💵 RM {float(price):.2f}" if price else "💵 Sell"
        css   = "mp-badge-sell"
    elif listing_type == "exchange":
        label, css = "🔄 Exchange", "mp-badge-exchange"
    else:
        label, css = "🆓 Free", "mp-badge-free"
    return f'<span class="mp-badge {css}">{label}</span>'


# ── Page ──────────────────────────────────────────────────────────────────────

def render_company_marketplace(db, user_id):
    st.markdown(COMPANY_CSS, unsafe_allow_html=True)

    st.markdown(
        """<div class="co-header"><h1>🏭 Company Marketplace</h1>
        <p>Browse inventory listed by other companies</p></div>""",
        unsafe_allow_html=True,
    )

    # ── CSS Layout Styles - ONE SINGLE CLEAN BOX WRAPPER ──────────────────────
    st.markdown("""
    <style>
    /* Baseline Flexbox Alignment for Filters */
    [data-testid="stHorizontalBlock"] {
        align-items: flex-end !important;
    }
    
    /* Clean up Filter Label hierarchy styling */
    [data-testid="stWidgetLabel"] p {
        font-size: 0.85rem !important;
        color: #475569 !important;
        font-weight: 500 !important;
        margin-bottom: 4px !important;
    }

    /* Badges */
    .mp-badge {
        display: inline-block; font-size: .75rem; font-weight: 700;
        padding: 4px 12px; border-radius: 999px; margin-right: 6px;
    }
    .mp-badge-free     { background:#dcfce7; color:#15803d; border:1px solid #bbf7d0; }
    .mp-badge-exchange { background:#ede9fe; color:#5b21b6; border:1px solid #c4b5fd; }
    .mp-badge-sell     { background:#fef9c3; color:#854d0e; border:1px solid #fde68a; }
    .expiry-ok         { background:#dcfce7; color:#15803d; border:1px solid #bbf7d0; }
    .expiry-urgent     { background:#fee2e2; color:#dc2626; border:1px solid #fca5a5; }

    /* The Only Outer Box Container */
    .mp-card {
        background: #fff; border-radius: 20px; border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,.04); padding: 20px; margin-bottom: 4px;
        display: flex; flex-direction: column; height: 100%;
    }
    .mp-card-title {
        font-size: 1.3rem; font-weight: 700; color: #1e293b;
        margin: 14px 0 12px 0; line-height: 1.3;
    }

    /* Content Layout Rows (No extra backgrounds, no double borders) */
    .mp-card-row { 
        font-size: .9rem; color: #475569; margin: 8px 0; 
        display: flex; align-items: center; gap: 8px;
    }
    .mp-card-row strong { color: #0f172a; font-weight: 600; }
    
    .mp-card-desc {
        font-size: .9rem; color: #475569; line-height: 1.5;
        margin-top: 12px; padding-top: 12px; border-top: 1px solid #e2e8f0;
    }

    /* Fixed Image Canvas Frame */
    .mp-img-frame {
        width: 100%; height: 230px; overflow: hidden; border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        background-color: #000000; border: 1px solid #e2e8f0;
    }
    .mp-img-frame img {
        width: 100%; height: 100%; object-fit: contain; object-position: center;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Filters ──────────────────────────────────────────────────────────────
    f1, f2, f3 = st.columns([2.5, 1.2, 1.2])
    
    with f1:
        search_q = st.text_input(
            "Search",
            placeholder="🔍 Search products…",
            key="co_mp_search",
            label_visibility="collapsed"
        )

    with f2:
        filt_cat = st.selectbox(
            "Category",
            ["All Categories","Groceries & Food","Household","Electronics",
             "Fashion & Apparel","Lifestyle & Hobbies","Others"],
            key="co_mp_cat"
        )

    with f3:
        filt_type = st.selectbox(
            "Type",
            ["All Types","💵 Sell","🆓 Free","🔄 Exchange"],
            key="co_mp_type"
        )

    # ── Fetch ─────────────────────────────────────────────────────────────────
    db_res = db.get_all_company_items(
        search=search_q if search_q else None,
        category=filt_cat if filt_cat != "All Categories" else None,
    )

    if not db_res.get("success"):
        st.error("Could not load company marketplace.")
        return

    items = db_res.get("items", [])
    current_user_id = user_id

    # SECURITY FILTER: Hide company's own items
    items = [i for i in items if i.get("user_id") != current_user_id]

    type_map = {"💵 Sell": "sell", "🆓 Free": "free", "🔄 Exchange": "exchange"}
    if filt_type in type_map:
        items = [i for i in items if i.get("listing_type") == type_map[filt_type]]

    if not items:
        st.info("No company products found matching your filters.")
        return

    st.caption(f"{len(items)} product(s) found")

    # ── Symmetrical Row Grid Rendering Engine ─────────────────────────────────
    row_chunks = [items[i:i + 3] for i in range(0, len(items), 3)]

    for row_items in row_chunks:
        cols_cards = st.columns(3)
        cols_buttons = st.columns(3)
        
        for col_idx, item in enumerate(row_items):
            item_id      = item["item_id"]
            listing_type = item.get("listing_type") or "sell"
            price        = item.get("price")
            region       = item.get("region") or "—"
            category     = item.get("category") or "—"

            # ── 1. EXTRACT DATA SAFELY FROM DATABASE ──────────────────────────
            raw_desc    = str(item.get('description') or "").strip()
            raw_company = str(item.get('company_name') or item.get('seller_name') or "—").strip()

            # ── 2. DATA EXTRACTION CLEANUP ────────────────────────────────────
            if "(" in str(price):
                price_match = re.search(r"RM\s*([\d\.]+)", str(price))
                price = price_match.group(1) if price_match else None

            raw_desc = re.sub(r'<[^>]*>', ' ', raw_desc)
            raw_desc = re.sub(r"\(?[‘'’]?lt-\w+[‘'’]?\s*,\s*.*?\)?", "", raw_desc)
            raw_desc = re.sub(r'(Description:|Item to give:|Item to receive:)', ' ', raw_desc, flags=re.IGNORECASE)
            raw_desc = html.unescape(raw_desc)
            raw_desc = re.sub(r'\s+', ' ', raw_desc).strip()

            raw_company = re.sub(r'<[^>]*>', ' ', raw_company)
            raw_company = html.unescape(raw_company)
            raw_company = re.sub(r'\s+', ' ', raw_company).strip()

            if not raw_desc or raw_desc.lower() == "none" or raw_desc == "No description provided.":
                raw_desc = "No description provided."

            item_name_safe = html.escape(str(item.get('item_name', '')))
            company_name_clean = html.escape(raw_company)
            description_clean = html.escape(raw_desc)

            # ── 3. RESOLVE BADGES & DICTIONARY ENTRIES ────────────────────────
            exp_cls, exp_label = _expiry_badge(item.get("expiry_date"))
            badge_html         = _lt_badge(listing_type, price)
            expiry_badge_html  = f'<span class="mp-badge {exp_cls}">{exp_label}</span>'
            
            if listing_type == "sell" and price:
                price_row = f'<div class="mp-card-row">💰 <strong>Price:</strong> RM {float(price):.2f}</div>'
            else:
                price_row = ""

            # ── 4. EMBED IMAGE COMPONENT ──────────────────────────────────────
            img_url = item.get("image_path")
            if img_url:
                img_tag_html = f'<div class="mp-img-frame"><img src="{img_url}"></div>'
            else:
                img_tag_html = '<div class="mp-img-frame" style="font-size:3rem; background-color:#f1f5f9;">🏭</div>'

            # ── 5. DESCRIPTION FORMAT CONTAINER ───────────────────────────────
            if listing_type == "exchange":
                offer_match = re.search(r"OFFER:\s*(.*)", raw_desc, re.IGNORECASE)
                want_match  = re.search(r"WANT:\s*(.*)", raw_desc, re.IGNORECASE)
                item_offer = offer_match.group(1).strip() if offer_match else (item.get("exchange_offer") or raw_desc)
                item_want  = want_match.group(1).strip() if want_match else (item.get("exchange_want") or "Any item")
                
                exchange_desc = f'<div>📤 <strong>Item to give:</strong> {html.escape(str(item_offer))}</div><div style="margin-top: 4px;">📥 <strong>Item to receive:</strong> {html.escape(str(item_want))}</div>'
            else:
                if description_clean == "No description provided.":
                    exchange_desc = f'<span style="font-style: italic; color:#94a3b8;">No description provided.</span>'
                else:
                    exchange_desc = f'📝 <strong>Description:</strong> {description_clean}'

            # Complete single-box layout without the inner box container lines
            full_card_html = f"""
<div class="mp-card">
    {img_tag_html}
    <p class="mp-card-title">{item_name_safe}</p>
    <div style="margin-bottom: 12px; display: flex; align-items: center;">
        {badge_html}{expiry_badge_html}
    </div>
    <div class="mp-card-row">🏢 <strong>Company:</strong> {company_name_clean}</div>
    <div class="mp-card-row">📍 <strong>Region:</strong> {region}</div>
    <div class="mp-card-row">🏷️ <strong>Category:</strong> {category}</div>
    {price_row}
    <div class="mp-card-desc">
        {exchange_desc}
    </div>
</div>
"""
            cols_cards[col_idx].markdown(full_card_html, unsafe_allow_html=True)

            # ── 6. BUTTON BLOCK ROW CONTROLLER ────────────────────────────────
            with cols_buttons[col_idx]:
                btn_label = (
                    "🛍️ Request to Buy"   if listing_type == "sell"     else
                    "🔄 Offer Exchange"   if listing_type == "exchange" else
                    "🙋 Claim Item"
                )

                with st.expander(btn_label, expanded=False):
                    msg_key = f"co_msg_{item_id}"
                    if msg_key not in st.session_state:
                        st.session_state[msg_key] = ""

                    action_word = "buy" if listing_type == "sell" else "exchange" if listing_type == "exchange" else "claim"
                    msg = st.text_area(
                        "Add a message to the seller (optional)",
                        key=msg_key,
                        placeholder=f"Hi, I'd like to {action_word} this item…",
                        height=80,
                    )
                    
                    if st.button(f"✅ Confirm", key=f"co_confirm_{item_id}"):
                        res = db.reserve_company_item(item_id, user_id)
                        

                        if res.get("success"):
                            st.session_state["show_cart_popup"] = True
                            st.session_state["cart_popup_item"] = item.get("item_name", "Item")
                             
  
                        else:
                            st.error(res.get("error"))
        
        st.write("")