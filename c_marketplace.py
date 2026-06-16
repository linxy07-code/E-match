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

    # Use the logged-in session region to avoid an extra read on every rerun.
    user_region = st.session_state.get("region", "All Regions")

    # ── CSS Layout Styles ─────────────────────────────────────────────────────
    st.markdown("""
    <style>
    [data-testid="stHorizontalBlock"] {
        align-items: flex-end !important;
    }
                
    /* ── READ MORE TOGGLE (COMPANY MARKETPLACE) ── */
    /* ── PURE CSS PUSH-BUTTON TOGGLE ── */
    .desc-toggle {
        display: none;
    }
    .desc-label {
        color: #2563eb;
        font-size: 0.78rem;
        font-weight: 600;
        cursor: pointer;
        display: inline-block;
        margin-top: 4px;
        text-decoration: underline;
    }
    .desc-label:hover {
        color: #166534;
    }
    .desc-full {
        display: none;
    }
    .desc-toggle:checked ~ .desc-full  { display: block; margin-bottom: 6px; }
    .desc-toggle:checked ~ .desc-label::after { content: "Read Less"; }
    .desc-toggle:not(:checked) ~ .desc-label::after { content: "Read More"; }
    
                
    [data-testid="stWidgetLabel"] p {
        font-size: 0.85rem !important;
        color: #475569 !important;
        font-weight: 500 !important;
        margin-bottom: 4px !important;
    }

    .mp-badge {
        display: inline-block; font-size: .75rem; font-weight: 700;
        padding: 4px 12px; border-radius: 999px; margin-right: 6px;
    }
    .mp-badge-free     { background:#dcfce7; color:#15803d; border:1px solid #bbf7d0; }
    .mp-badge-exchange { background:#ede9fe; color:#5b21b6; border:1px solid #c4b5fd; }
    .mp-badge-sell     { background:#fef9c3; color:#854d0e; border:1px solid #fde68a; }
    .expiry-ok         { background:#dcfce7; color:#15803d; border:1px solid #bbf7d0; }
    .expiry-urgent     { background:#fee2e2; color:#dc2626; border:1px solid #fca5a5; }

    .mp-card {
        background: #fff; border-radius: 20px; border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,.04); padding: 20px; margin-bottom: 4px;
        display: flex; flex-direction: column; height: 100%;
        flex: 1 1 auto; /* Forces structural alignment flexibility across the row */
    }
    .mp-card-title {
        font-size: 1.4rem; font-weight: 600; color: #1e293b;
        margin: 25px 0 12px 0; line-height: 1.3;
    }

    .mp-card-row { 
        font-size: .9rem; color: #475569; margin: 8px 0; 
        display: flex; align-items: center; gap: 8px;
    }
    .mp-card-row strong { color: #0f172a; font-weight: 600; }
    
    .mp-card-desc {
        font-size: .9rem; color: #475569; line-height: 1.5;
        margin-top: auto; /* Push down to keep bottom edges level */
        padding-top: 12px; border-top: 1px solid #e2e8f0;
    }

    .mp-img-frame {
        width: 100%; height: 230px; overflow: hidden; border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        background-color: #ffffff; /* 🌟 FIXED: Changed background from black to white to fix side margins */
        border: 1px solid #e2e8f0; margin-bottom: 15px; 
    }
    .mp-img-frame img {
        width: 100%; height: 100%; object-fit: contain; object-position: center;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Filters ──────────────────────────────────────────────────────────────
    f1, f2, f3, f4 = st.columns([2.5, 1.2, 1.2, 1.2])
    
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

    # ✅ FIXED REGION FILTER (auto user region default)
    with f4:
        regions = [
            "All Regions", "Johor", "Kedah", "Kelantan", "Kuala Lumpur",
            "Melaka", "Negeri Sembilan", "Pahang", "Perak", "Perlis",
            "Pulau Pinang", "Selangor", "Terengganu", "Sabah", "Sarawak"
        ]

        default_index = 0
        if user_region in regions:
            default_index = regions.index(user_region)

        filt_region = st.selectbox(
            "Region",
            regions,
            index=default_index,
            key="co_mp_region"
        )

    # ── Fetch ─────────────────────────────────────────────────────────────────
    type_map = {"💵 Sell": "sell", "🆓 Free": "free", "🔄 Exchange": "exchange"}
    db_res = db.get_all_company_items(
        search=search_q if search_q else None,
        category=filt_cat if filt_cat != "All Categories" else None,
        region=filt_region if filt_region != "All Regions" else None,
        listing_type=type_map.get(filt_type),
        exclude_user_id=user_id,
    )

    if not db_res.get("success"):
        st.error("Could not load company marketplace.")
        return

    items = db_res.get("items", [])
    current_user_id = user_id

    items = [i for i in items if i.get("user_id") != current_user_id]

    if filt_type in type_map:
        items = [i for i in items if i.get("listing_type") == type_map[filt_type]]

    target = filt_region.strip().lower()

    if target != "all regions":
        items = [
            i for i in items
            if (i.get("region") or "").strip().lower() == target
            or (
                target in ["pulau pinang", "penang"]
                and (i.get("region") or "").strip().lower() in ["pulau pinang", "penang"]
            )
        ]

    if not items:
        st.info("No company products found matching your filters.")
        return

    st.caption(f"{len(items)} product(s) found")

    row_chunks = [items[i:i + 3] for i in range(0, len(items), 3)]

    for row_items in row_chunks:
        cols_cards = st.columns(3)
        cols_buttons = st.columns(3)
        
        for col_idx, item in enumerate(row_items):
            item_id = item["item_id"]
            listing_type = item.get("listing_type") or "sell"
            price = item.get("price")
            region = item.get("region") or "—"
            category = item.get("category") or "—"
            quantity = item.get("quantity", 0)

            raw_desc = str(item.get('description') or "").strip()
            base_exchange_desc = raw_desc

            item_offer = ""
            item_want = ""

            if listing_type == "exchange":
                text = base_exchange_desc

                offer_split = re.split(r"OFFER\s*:", text, flags=re.IGNORECASE)
                if len(offer_split) > 1:
                    rest = offer_split[1]
                    want_split = re.split(r"WANT\s*:", rest, flags=re.IGNORECASE)

                    item_offer = want_split[0].strip() if len(want_split) > 0 else "Not specified"
                    item_want = want_split[1].strip() if len(want_split) > 1 else "Not specified"
                else:
                    item_offer = "Not specified"
                    item_want = "Not specified"

            raw_company = str(item.get('company_name') or item.get('seller_name') or "—").strip()

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

            if not raw_desc or raw_desc.lower() == "none":
                raw_desc = "No description provided."

            item_name_safe = html.escape(str(item.get('item_name', '')))
            company_name_clean = html.escape(raw_company)
            description_clean = html.escape(raw_desc)

            exp_cls, exp_label = _expiry_badge(item.get("expiry_date"))
            badge_html = _lt_badge(listing_type, price)
            expiry_badge_html = f'<span class="mp-badge {exp_cls}">{exp_label}</span>'

            img_url = item.get("image_path")
            if img_url:
                img_tag_html = f'<div class="mp-img-frame"><img src="{img_url}"></div>'
            else:
                img_tag_html = '<div class="mp-img-frame" style="font-size:3rem;">🏭</div>'


            # ── 6. ZERO-PREVIEW SEAMLESS EXPANDABLE TOGGLES ───────────────────
            if description_clean == "No description provided.":
                exchange_desc = '<span style="font-style: italic; color:#a3a3a3;">No description provided.</span>'
            else:
                if listing_type == "exchange":
                    clean_offer = html.escape(item_offer or "—")
                    clean_want = html.escape(item_want or "—")
                    full_html = f'📥 <strong>OFFER:</strong> {clean_offer}<br><span style="display:inline-block; margin-top:4px;">📤 <strong>WANT:</strong> {clean_want}</span>'
                else:
                    full_html = f'📥 {description_clean}'
                
                exchange_desc = f'<input type="checkbox" id="toggle_{item_id}" class="desc-toggle"><span class="desc-full">{full_html}</span><label for="toggle_{item_id}" class="desc-label"></label>'
            
            # ✅ FIXED: Completely removed price_row variable injection here to keep cards even
            full_card_html = (
                f'<div class="mp-card">'
                f'{img_tag_html}'
                f'<p class="mp-card-title">{item_name_safe}</p>'
                f'<div>{badge_html}{expiry_badge_html}</div>'
                f'<div class="mp-card-row">🏢 <strong>Company:</strong> {company_name_clean}</div>'
                f'<div class="mp-card-row">📍 <strong>Region:</strong> {region}</div>'
                f'<div class="mp-card-row">🏷️ <strong>Category:</strong> {category}</div>'
                f'<div class="mp-card-row">📦 <strong>Quantity:</strong> {quantity}</div>'
                f'<div class="mp-card-desc">{exchange_desc}</div>'
                f'</div>'
            )
            cols_cards[col_idx].markdown(full_card_html, unsafe_allow_html=True)

            with cols_buttons[col_idx]:
                btn_label = (
                    "🛍️ Request to Buy" if listing_type == "sell"
                    else "🔄 Offer Exchange" if listing_type == "exchange"
                    else "🙋 Claim Item"
                )

                with st.expander(btn_label, expanded=False):
                    msg_key = f"co_msg_{item_id}"
                    if msg_key not in st.session_state:
                        st.session_state[msg_key] = ""

                    msg = st.text_area(
                        "Message",
                        key=msg_key
                    )

                    if st.button(f"✅ Confirm", key=f"co_confirm_{item_id}"):

                        res = db.reserve_company_item(item_id, user_id)

                        if res.get("success"):

                            st.session_state["show_cart_popup"] = True
                            st.session_state["cart_popup_item"] = item.get("item_name", "Item")

                            st.rerun()

                        elif res.get("error") == "duplicate":
                            st.warning("⚠️ You already requested this item.")

                        else:
                            st.error(res.get("error"))

        st.write("")
