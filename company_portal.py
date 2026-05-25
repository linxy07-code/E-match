import streamlit as st
import html as html_lib
import re
from datetime import datetime, date
import cloudinary
import cloudinary.uploader
import time

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _expiry_badge(expiry_str):
    if not expiry_str:
        return "expiry-ok", "✅ No Expiry"
    try:
        expiry_dt = datetime.strptime(expiry_str, "%Y-%m-%d").date()
        days_left = (expiry_dt - date.today()).days
        if days_left < 0:
            return "expiry-urgent", "❌ EXPIRED"
        if days_left <= 7:
            return "expiry-urgent", f"🚨 {days_left}d left"
        if days_left <= 14:
            return "expiry-warn", f"⚠️ {days_left}d left"
        return "expiry-ok", f"✅ {days_left}d left"
    except ValueError:
        return "expiry-ok", "✅ No Expiry"


def _lt_badge(listing_type, price=None):
    if listing_type == "sell":
        label = f"💵 RM {float(price):.2f}" if price else "💵 Sell"
        css   = "lt-sell"
    elif listing_type == "exchange":
        label, css = "🔄 Exchange", "lt-exchange"
    else:
        label, css = "🆓 Free", "lt-free"
    return f'<span class="lt-badge {css}">{label}</span>'


def _save_company_image(uploaded_file):
    if uploaded_file is None:
        return None
    ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        st.error(f"❌ Unsupported file type '.{ext}'")
        return None
    try:
        result = cloudinary.uploader.upload(
            uploaded_file,
            folder="ecomatch_company",
            transformation=[{
                "width": 500, "height": 500,
                "crop": "pad", "background": "white", "gravity": "center"
            }]
        )
        return result.get("secure_url")
    except Exception as e:
        st.error(f"❌ Image upload failed: {e}")
        return None


# ── Shared CSS ────────────────────────────────────────────────────────────────

COMPANY_CSS = """
<style>
.co-header {
    background:linear-gradient(135deg,#1e3a5f 0%,#0d6efd 100%);
    border-radius:14px; padding:32px 36px; margin-bottom:28px;
    box-shadow:0 10px 30px rgba(0,0,0,.10);
}
.co-header h1 {
    font-family:'Fraunces',serif !important; font-size:2rem !important;
    color:#fff !important; margin:0 0 6px !important;
}
.co-header p { color:rgba(255,255,255,.75) !important; font-size:.95rem; margin:0; }

.co-metric-row { display:flex; gap:16px; margin-bottom:24px; flex-wrap:wrap; }
.co-metric-card {
    flex:1; min-width:160px; background:white; border:1px solid #bfdbfe;
    border-radius:14px; padding:20px 22px;
    box-shadow:0 1px 3px rgba(0,0,0,.06); position:relative; overflow:hidden;
}
.co-metric-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background:linear-gradient(90deg,#2563eb,#60a5fa);
}
.co-metric-value {
    font-family:'Fraunces',serif; font-size:1.9rem; font-weight:600;
    color:#1e3a5f; line-height:1; margin-bottom:4px;
}
.co-metric-label { font-size:.78rem; color:#6b7280; text-transform:uppercase; font-weight:600; }

.co-alert-box {
    background:#fff7ed; border:1px solid #fdba74; border-left:4px solid #f97316;
    border-radius:10px; padding:14px 16px; margin-bottom:10px;
}
.co-alert-expired {
    background:#fee2e2; border:1px solid #fca5a5; border-left:4px solid #dc2626;
    border-radius:10px; padding:14px 16px; margin-bottom:10px;
}
.co-alert-title { font-weight:700; color:#9a3412; font-size:.9rem; margin:0 0 4px 0; }
.co-alert-body  { font-size:.82rem; color:#7c3a1e; margin:0; }

.co-item-card {
    background:#fff; border-radius:14px; border:1px solid #bfdbfe;
    box-shadow:0 1px 3px rgba(0,0,0,.06); padding:18px 20px; margin-bottom:8px;
}
.co-item-title {
    font-family:'Fraunces',serif; font-size:1.1rem; font-weight:600;
    color:#1e3a5f; margin:0 0 8px 0;
}
.co-item-row   { font-size:.83rem; color:#374151; margin:3px 0; }
.co-item-row strong { color:#1d4ed8; }

.lt-badge { display:inline-block; font-size:.75rem; font-weight:700;
            padding:3px 10px; border-radius:999px; margin-left:4px; }
.lt-free     { background:#dcfce7; color:#15803d; border:1px solid #bbf7d0; }
.lt-exchange { background:#ede9fe; color:#5b21b6; border:1px solid #c4b5fd; }
.lt-sell     { background:#fef9c3; color:#854d0e; border:1px solid #fde68a; }
.expiry-ok     { background:#dcfce7; color:#15803d; }
.expiry-warn   { background:#fff7ed; color:#c2410c; }
.expiry-urgent { background:#fee2e2; color:#dc2626; }
.mp-badge { display:inline-block; font-size:.75rem; font-weight:700;
            padding:3px 10px; border-radius:999px; margin-right:4px; }

.co-mp-card {
    background:#fff; border-radius:14px; border:1px solid #bfdbfe;
    box-shadow:0 1px 3px rgba(0,0,0,.06); padding:16px; margin-bottom:4px;
}
.co-mp-title {
    font-family:'Fraunces',serif; font-size:1.1rem; font-weight:600;
    color:#1e3a5f; margin:0 0 8px 0;
}
.co-mp-row   { font-size:.82rem; color:#374151; margin:3px 0; }
.co-mp-row strong { color:#1d4ed8; }
.co-mp-img-frame {
    width:100%; height:280px; overflow:hidden; border-radius:10px;
    margin-bottom:10px; display:flex; align-items:center;
    justify-content:center; background:#eff6ff;
}
.co-mp-img-frame img { width:100%; height:100%; object-fit:cover; }

/* expiry tracker row colours in inventory */
.expiry-row-red   { background:#fff0f0; border-left:3px solid #dc2626; padding:4px 8px; border-radius:6px; }
.expiry-row-amber { background:#fffbeb; border-left:3px solid #f97316; padding:4px 8px; border-radius:6px; }
.expiry-row-green { background:#f0fdf4; border-left:3px solid #22c55e; padding:4px 8px; border-radius:6px; }
</style>
"""


# ── 1. COMPANY DASHBOARD ──────────────────────────────────────────────────────

def render_company_dashboard(db, user_id):
    st.markdown(COMPANY_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="co-header">
        <h1>🏢 Company Dashboard</h1>
        <p>Inventory overview and expiry alert centre</p>
    </div>""", unsafe_allow_html=True)

    stats = db.get_company_stats(user_id)

    st.markdown(f"""
    <div class="co-metric-row">
        <div class="co-metric-card">
            <div class="co-metric-value">{stats['total_listings']}</div>
            <div class="co-metric-label">Active Listings</div>
        </div>
        <div class="co-metric-card">
            <div class="co-metric-value"
                 style="color:{'#dc2626' if stats['near_expiry'] > 0 else '#1e3a5f'}">
                {stats['near_expiry']}
            </div>
            <div class="co-metric-label">Expiring ≤ 14 Days</div>
        </div>
        <div class="co-metric-card">
            <div class="co-metric-value">{stats['completed_sales']}</div>
            <div class="co-metric-label">Completed Sales</div>
        </div>
        <div class="co-metric-card">
            <div class="co-metric-value">RM {stats['total_revenue']:,.2f}</div>
            <div class="co-metric-label">Total Revenue</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### ⏰ Expiry Alerts (Next 14 Days)")
    near_expiry_items = db.get_near_expiry_company_items(user_id, days=14)

    if not near_expiry_items:
        st.success("✅ All clear — no items expiring within the next 14 days.")
    else:
        st.warning(f"⚠️ {len(near_expiry_items)} item(s) are nearing expiry.")
        for item in near_expiry_items:
            exp_cls, exp_label = _expiry_badge(item.get("expiry_date"))
            box_cls = "co-alert-expired" if exp_cls == "expiry-urgent" else "co-alert-box"
            st.markdown(f"""
            <div class="{box_cls}">
                <p class="co-alert-title">
                    📦 {html_lib.escape(str(item.get('item_name','')))}
                    &nbsp;<span class="mp-badge {exp_cls}">{exp_label}</span>
                </p>
                <p class="co-alert-body">
                    Stock: <strong>{item.get('stock_name','—')}</strong> &nbsp;|&nbsp;
                    Qty: <strong>{item.get('quantity',1)}</strong> &nbsp;|&nbsp;
                    Expiry: <strong>{item.get('expiry_date','—')}</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)


# ── 2. MY UPLOADS / ITEMS (was "My Inventory") ───────────────────────────────
# FIX #2: renamed + FIX #1: sorted by expiry, expiry tracker shown

def render_company_inventory(db, user_id):
    st.markdown(COMPANY_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="co-header">
        <h1>🗂️ My Uploads / Items</h1>
        <p>All items your company has listed — sorted by expiry date</p>
    </div>""", unsafe_allow_html=True)

    items_res = db.get_company_inventory(user_id)
    items     = items_res.get("items", [])

    if not items:
        st.info("No inventory listed yet. Use **Upload Inventory** to add your first item.")
        return

    st.caption(f"{len(items)} active listing(s) — earliest expiry shown first")

    for item in items:
        lt    = item.get("listing_type") or "sell"
        price = item.get("price")
        exp_cls, exp_label = _expiry_badge(item.get("expiry_date"))
        badge = _lt_badge(lt, price)

        # ── FIX #1: expiry colour row ────────────────────────────────────────
        expiry_raw = item.get("expiry_date")
        if expiry_raw:
            try:
                from datetime import datetime as dt
                days_left = (dt.strptime(expiry_raw, "%Y-%m-%d").date() - date.today()).days
                if days_left < 0:
                    row_css = "expiry-row-red"
                    expiry_display = f"❌ EXPIRED ({expiry_raw})"
                elif days_left <= 7:
                    row_css = "expiry-row-red"
                    expiry_display = f"🚨 {days_left}d left — {expiry_raw}"
                elif days_left <= 14:
                    row_css = "expiry-row-amber"
                    expiry_display = f"⚠️ {days_left}d left — {expiry_raw}"
                else:
                    row_css = "expiry-row-green"
                    expiry_display = f"✅ {days_left}d left — {expiry_raw}"
            except Exception:
                row_css = "expiry-row-green"
                expiry_display = expiry_raw
        else:
            row_css = ""
            expiry_display = "No expiry"

        img_col, info_col = st.columns([1, 2])

        with img_col:
            if item.get("image_path"):
                st.image(item["image_path"], use_container_width=True)
            else:
                st.markdown(
                    "<div style='height:140px;background:#eff6ff;border-radius:10px;"
                    "display:flex;align-items:center;justify-content:center;"
                    "color:#93c5fd;font-size:2.5rem'>🏭</div>",
                    unsafe_allow_html=True,
                )

        with info_col:
            price_row = (
                f"<div class='co-item-row'>💰 <strong>Price:</strong> RM {float(price):.2f}</div>"
                if lt == "sell" and price else ""
            )
            phone_row = (
                f"<div class='co-item-row'>📞 <strong>Contact:</strong> {item['phone_number']}</div>"
                if item.get("phone_number") else ""
            )
            expiry_block = (
                f"<div class='co-item-row {row_css}'>📅 <strong>Expiry:</strong> {expiry_display}</div>"
                if expiry_raw else
                "<div class='co-item-row'>📅 <strong>Expiry:</strong> No expiry set</div>"
            )

            st.markdown(f"""
            <div class="co-item-card">
                <p class="co-item-title">
                    {html_lib.escape(str(item.get('item_name','')))} {badge}
                    &nbsp;<span class="mp-badge {exp_cls}">{exp_label}</span>
                </p>
                <div class="co-item-row">🗂️ <strong>Stock Name:</strong> {item.get('stock_name','—')}</div>
                <div class="co-item-row">🏷️ <strong>Category:</strong> {item.get('category','—')}</div>
                <div class="co-item-row">📍 <strong>Region:</strong> {item.get('region','—')}</div>
                <div class="co-item-row">📦 <strong>Quantity:</strong> {item.get('quantity',1)}</div>
                {expiry_block}
                {price_row}
                {phone_row}
            </div>
            """, unsafe_allow_html=True)

            seller_shipped = item.get("seller_shipped", False)
            buyer_received = item.get("buyer_received", False)

            if seller_shipped and not buyer_received:
                st.markdown("""
                <div style="background:#fff7ed;padding:10px;border-radius:10px;
                border:1px solid #fdba74;color:#9a3412;font-weight:600;margin-bottom:8px;">
                ⏳ Waiting for buyer to confirm receipt
                </div>""", unsafe_allow_html=True)
            elif not seller_shipped and buyer_received:
                st.markdown("""
                <div style="background:#eff6ff;padding:10px;border-radius:10px;
                border:1px solid #93c5fd;color:#1e3a8a;font-weight:600;margin-bottom:8px;">
                ⏳ Buyer confirmed — please ship the item
                </div>""", unsafe_allow_html=True)

            btn1, btn2 = st.columns(2)
            with btn1:
                if st.button("📦 Mark as Shipped", key=f"co_ship_{item['item_id']}", use_container_width=True):
                    result = db.mark_company_item_shipped(item["item_id"])
                    if result.get("success"):
                        st.success("✅ Marked as shipped.")
                        st.rerun()
                    else:
                        st.error(f"Error: {result.get('error')}")
            with btn2:
                if st.button("🗑️ Delete Listing", key=f"co_delete_{item['item_id']}", use_container_width=True):
                    result = db.delete_company_item(item["item_id"], st.session_state.user_id)
                    if result.get("success"):
                        st.success("🗑️ Deleted.")
                        st.rerun()
                    else:
                        st.error(f"Error: {result.get('error')}")


# ── 3. UPLOAD INVENTORY ───────────────────────────────────────────────────────

def render_company_upload(db, user_id):
    st.markdown(COMPANY_CSS, unsafe_allow_html=True)

    if "co_upload_success" not in st.session_state:
        st.session_state.co_upload_success = False

    if st.session_state.co_upload_success:
        st.balloons()
        st.markdown("""
        <div class="co-header">
            <h1>🎉 Inventory Listed Successfully!</h1>
            <p>Your item is now visible on the Company Marketplace</p>
        </div>""", unsafe_allow_html=True)
        st.success("Item added and published.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📦 View My Uploads / Items", use_container_width=True):
                st.session_state.co_upload_success = False
                st.session_state.current_page = "My Inventory"
                st.rerun()
        with c2:
            if st.button("➕ Add Another", use_container_width=True):
                st.session_state.co_upload_success = False
                st.rerun()
        return

    st.markdown("""
    <div class="co-header">
        <h1>📋 Upload Inventory Item</h1>
        <p>Add stock to your company inventory</p>
    </div>""", unsafe_allow_html=True)

    col_main, col_side = st.columns([2, 1])

    with col_main:
        item_name    = st.text_input("Product Name *", key="co_item_name")
        stock_name   = st.text_input("Stock / SKU Name", key="co_stock_name")
        category     = st.selectbox("Category *", [
            "Groceries & Food", "Household", "Electronics",
            "Fashion & Apparel", "Lifestyle & Hobbies", "Others"
        ], key="co_category")
        region = st.selectbox("Region *", [
            "Johor","Kedah","Kelantan","Melaka","Negeri Sembilan",
            "Pahang","Perak","Perlis","Pulau Pinang",
            "Selangor","Terengganu","Sabah","Sarawak"
        ], key="co_region")
        quantity     = st.number_input("Quantity *", min_value=1, value=1, step=1, key="co_quantity")
        phone_number = st.text_input("Contact Phone Number", placeholder="+60 12-345 6789", key="co_phone")
        description  = st.text_area("Description", key="co_description")
        has_expiry   = st.checkbox("This item has an expiry date", key="co_has_expiry")
        expiry_date  = st.date_input("Expiry Date", key="co_expiry") if has_expiry else None
        st.markdown("---")
        listing_opts = {
            "💵 Sell": "sell",
            "🆓 Free of Charge": "free",
            "🔄 Exchange / Swap": "exchange",
        }
        listing_label = st.radio("Listing Type *", list(listing_opts.keys()), horizontal=True, key="co_listing_type")
        listing_type  = listing_opts[listing_label]
        price = None
        if listing_type == "sell":
            price = st.number_input("Price (RM) *", min_value=0.01, step=0.50, format="%.2f", key="co_price")

    with col_side:
        st.markdown("### 🖼️ Product Image")
        uploaded_file = st.file_uploader("Upload image", type=list(ALLOWED_EXTENSIONS), key="co_image")
        if uploaded_file:
            st.image(uploaded_file, caption="Preview", use_container_width=True)

    if st.button("📤 Publish to Inventory", use_container_width=True):
        if not item_name:
            st.error("Please enter a product name.")
            return
        if not uploaded_file:
            st.error("Please upload a product image.")
            return
        if listing_type == "sell" and (price is None or price <= 0):
            st.error("Please enter a valid price.")
            return
        with st.spinner("Uploading image…"):
            image_url = _save_company_image(uploaded_file)
        if image_url:
            expiry_str = expiry_date.strftime("%Y-%m-%d") if expiry_date else None
            result = db.add_company_item(
                user_id=user_id, item_name=item_name, stock_name=stock_name,
                category=category, region=region, quantity=quantity,
                description=description, expiry_date=expiry_str, image_path=image_url,
                listing_type=listing_type,
                price=price if listing_type == "sell" else None,
                phone_number=phone_number if phone_number else None,
            )
            if result.get("success"):
                st.session_state.co_upload_success = True
                st.rerun()
            else:
                st.error(f"Could not save: {result.get('error')}")


# ── 4. COMPANY MARKETPLACE ────────────────────────────────────────────────────

def render_company_marketplace(db, user_id):
    st.markdown(COMPANY_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="co-header">
        <h1>🏭 Company Marketplace</h1>
        <p>Browse inventory listed by other companies</p>
    </div>""", unsafe_allow_html=True)

    f1, f2, f3 = st.columns([2, 1, 1])
    search_q  = f1.text_input("Search", placeholder="🔍 Search products…",
                               key="co_mp_search", label_visibility="collapsed")
    filt_cat  = f2.selectbox("Category", [
        "All Categories","Groceries & Food","Household","Electronics",
        "Fashion & Apparel","Lifestyle & Hobbies","Others"
    ], key="co_mp_cat")
    filt_type = f3.selectbox("Type", ["All Types","💵 Sell","🆓 Free","🔄 Exchange"],
                              key="co_mp_type")

    db_res = db.get_all_company_items(
        search=search_q if search_q else None,
        category=filt_cat if filt_cat != "All Categories" else None,
    )
    if not db_res["success"]:
        st.error("Could not load company marketplace.")
        return

    items = [i for i in db_res["items"] if i.get("user_id") != user_id]
    type_map = {"💵 Sell": "sell", "🆓 Free": "free", "🔄 Exchange": "exchange"}
    if filt_type in type_map:
        items = [i for i in items if i.get("listing_type") == type_map[filt_type]]

    if not items:
        st.info("No company products found matching your filters.")
        return

    st.caption(f"{len(items)} product(s) found")

    for row_items in [items[i:i+3] for i in range(0, len(items), 3)]:
        cols_cards   = st.columns(3)
        cols_buttons = st.columns(3)

        for col_idx, item in enumerate(row_items):
            item_id      = item["item_id"]
            listing_type = item.get("listing_type") or "sell"
            price        = item.get("price")
            exp_cls, exp_label = _expiry_badge(item.get("expiry_date"))
            badge_html   = _lt_badge(listing_type, price)
            exp_badge    = f'<span class="mp-badge {exp_cls}">{exp_label}</span>'
            raw_name     = html_lib.escape(str(item.get("item_name", "")))
            company_name = html_lib.escape(str(item.get("company_name") or item.get("seller_name") or "—"))
            price_row    = (
                f"<div class='co-mp-row'>💰 <strong>Price:</strong> RM {float(price):.2f}</div>"
                if listing_type == "sell" and price else ""
            )
            phone_row = (
                f"<div class='co-mp-row'>📞 <strong>Contact:</strong> {html_lib.escape(str(item.get('phone_number','—')))}</div>"
                if item.get("phone_number") else ""
            )

            with cols_cards[col_idx]:
                img_url = item.get("image_path")
                if img_url:
                    st.markdown(f'<div class="co-mp-img-frame"><img src="{img_url}"></div>', unsafe_allow_html=True)
                else:
                    st.markdown("<div class='co-mp-img-frame' style='font-size:3rem;'>🏭</div>", unsafe_allow_html=True)

                st.markdown(f"""
                <div class="co-mp-card">
                    <p class="co-mp-title">{raw_name}</p>
                    <div style="margin-bottom:8px;">{badge_html}{exp_badge}</div>
                    <div class="co-mp-row">🏢 <strong>Company:</strong> {company_name}</div>
                    <div class="co-mp-row">📍 <strong>Region:</strong> {item.get('region','—')}</div>
                    <div class="co-mp-row">🏷️ <strong>Category:</strong> {item.get('category','—')}</div>
                    <div class="co-mp-row">📦 <strong>Qty:</strong> {item.get('quantity',1)}</div>
                    {price_row}{phone_row}
                </div>
                """, unsafe_allow_html=True)

            with cols_buttons[col_idx]:
                btn_label = (
                    "🛍️ Request to Buy" if listing_type == "sell" else
                    "🔄 Offer Exchange"  if listing_type == "exchange" else
                    "🙋 Claim Item"
                )
                with st.expander(btn_label, expanded=False):
                    msg_key = f"co_msg_{item_id}"
                    if msg_key not in st.session_state:
                        st.session_state[msg_key] = ""
                    msg = st.text_area("Message to seller (optional)", key=msg_key, height=70)
                    if st.button("✅ Confirm", key=f"co_confirm_{item_id}", use_container_width=True):
                        res = db.reserve_company_item(item_id, user_id)
                        if res.get("success"):
                            st.session_state["show_cart_popup"] = True
                            st.session_state["cart_popup_item"] = item.get("item_name", "Item")
                            st.rerun()
                        else:
                            st.error(f"Could not reserve: {res.get('error')}")
        st.write("")


# ── 5. COMPANY CART ───────────────────────────────────────────────────────────

def render_company_cart(db, user_id):
    st.markdown(COMPANY_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="co-header">
        <h1>🛒 My Order Cart</h1>
        <p>Company items you have reserved from other sellers</p>
    </div>""", unsafe_allow_html=True)

    db_res = db.get_company_cart_items(user_id)
    items  = db_res.get("items", [])

    if not items:
        st.info("Your cart is empty. Browse the Company Marketplace to reserve items.")
        return

    st.caption(f"{len(items)} reserved item(s)")

    for item in items:
        col1, col2 = st.columns([1, 2])

        with col1:
            if item.get("image_path"):
                st.image(item["image_path"], use_container_width=True)
            else:
                st.markdown("🏭 No Image")

        with col2:
            company_display = item.get("company_name") or item.get("seller_name") or "—"
            price_display   = f"RM {float(item['price']):.2f}" if item.get("price") else "Free / Exchange"
            # Clean description of any HTML
            raw_desc = re.sub(r"<[^>]+>", "", str(item.get("description") or "—")).strip()

            st.markdown(f"### {html_lib.escape(str(item.get('item_name','')))}")
            st.markdown(
                f"🏢 **Seller Company:** {company_display}  \n"
                f"📍 **Region:** {item.get('region','—')}  \n"
                f"🏷️ **Category:** {item.get('category','—')}  \n"
                f"📦 **Quantity:** {item.get('quantity',1)}  \n"
                f"💰 **Price:** {price_display}  \n"
                f"💬 **Description:** {raw_desc}"
            )
            if item.get("phone_number"):
                st.markdown(f"📞 **Contact:** {item['phone_number']}")

            seller_shipped = item.get("seller_shipped", False)
            buyer_received = item.get("buyer_received", False)
            item_id        = item["item_id"]
            received_key   = f"co_received_{item_id}"

            if seller_shipped and not buyer_received:
                st.success("📦 Seller has shipped! Please confirm receipt below.")
            elif not seller_shipped:
                st.info("⏳ Waiting for seller to ship.")

            if received_key not in st.session_state:
                st.session_state[received_key] = False

            if st.session_state[received_key]:
                st.info("✅ Receipt confirmed — transaction is being processed.")
            else:
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("❌ Cancel Order", key=f"co_cancel_{item_id}"):
                        db.cancel_company_reservation(item_id)
                        st.warning("Order cancelled.")
                        st.rerun()
                with b2:
                    if st.button("✅ Received Item", key=f"co_recv_{item_id}"):
                        result = db.mark_company_item_received(item_id)
                        if result.get("success"):
                            st.session_state[received_key] = True
                            # FIX #6: balloons + congrats dialog
                            st.balloons()
                            st.session_state["show_txn_complete_dialog"] = True
                            st.session_state["txn_complete_item"] = item.get("item_name", "item")
                            st.rerun()
                        else:
                            st.error(f"Error: {result.get('error')}")

        st.markdown("---")


# ── 6. COMPANY PAST TRANSACTIONS ─────────────────────────────────────────────

def render_company_past_transactions(db, user_id):
    st.markdown(COMPANY_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="co-header">
        <h1>📜 Transaction History</h1>
        <p>Completed sales and purchases for your company account</p>
    </div>""", unsafe_allow_html=True)

    res          = db.get_past_transactions(user_id)
    transactions = res.get("transactions", [])

    if not transactions:
        st.info("No completed transactions yet.")
        return

    st.caption(f"{len(transactions)} completed transaction(s)")

    for t in transactions:
        seller_id  = str(t.get("seller_id") or "")
        buyer_id   = str(t.get("buyer_id")  or "")
        me         = str(user_id)
        role       = "🏪 You were the Seller" if seller_id == me else "🛒 You were the Buyer"
        price_disp = f"RM {float(t['price']):.2f}" if t.get("price") else "Free / Exchange"
        completed  = t.get("completed_at")
        date_str   = completed.strftime("%d %b %Y, %I:%M %p") if completed else "—"

        listing_badges = {
            "sell":     '<span style="background:#fef9c3;color:#854d0e;padding:3px 10px;border-radius:999px;font-size:.75rem;font-weight:700;">💵 Sell</span>',
            "exchange": '<span style="background:#ede9fe;color:#5b21b6;padding:3px 10px;border-radius:999px;font-size:.75rem;font-weight:700;">🔄 Exchange</span>',
            "free":     '<span style="background:#dcfce7;color:#15803d;padding:3px 10px;border-radius:999px;font-size:.75rem;font-weight:700;">🆓 Free</span>',
        }
        lt_badge = listing_badges.get(str(t.get("listing_type") or "free"), "")

        st.markdown(f"""
        <div style="background:white;padding:18px 20px;border-radius:14px;
        border:1px solid #bfdbfe;margin-bottom:12px;
        box-shadow:0 1px 3px rgba(0,0,0,.05);">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                <span style="font-family:'Fraunces',serif;font-size:1.1rem;
                font-weight:700;color:#1e3a5f;">🎉 {t.get('item_name','Unknown Item')}</span>
                {lt_badge}
            </div>
            <div style="font-size:.85rem;color:#374151;line-height:2;">
                {role}<br>
                💰 <strong>Amount:</strong> {price_disp}<br>
                🕒 <strong>Completed:</strong> {date_str}
            </div>
        </div>
        """, unsafe_allow_html=True)