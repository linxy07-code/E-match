# c_inventory.py
import streamlit as st
import html
from datetime import datetime, date
import time


def _expiry_badge(expiry_date):
    if not expiry_date:
        return "", "No Expiry"
    try:
        days_left = (datetime.strptime(expiry_date, "%Y-%m-%d").date() - date.today()).days
        if days_left < 0:
            return "lt-sell", f"❌ Expired"
        elif days_left <= 7:
            return "lt-sell", f"🚨 {days_left}d left"
        elif days_left <= 14:
            return "lt-exchange", f"⚠️ {days_left}d left"
        else:
            return "lt-free", f"✅ {days_left}d left"
    except Exception:
        return "", expiry_date


def _lt_badge(listing_type, price=None):
    if listing_type == "sell":
        label = f"💵 RM {float(price):.2f}" if price else "💵 Sell"
        css   = "lt-sell"
    elif listing_type == "exchange":
        label, css = "🔄 Exchange", "lt-exchange"
    else:
        label, css = "🆓 Free", "lt-free"
    return f'<span class="lt-badge {css}">{label}</span>'


def render_company_inventory(db, user_id):
    st.markdown("""
    <div class="page-header">
        <h1>🗂️ My Uploads / Items</h1>
        <p>All items your company has listed — sorted by expiry date</p>
    </div>""", unsafe_allow_html=True)

    items = db.get_company_inventory(user_id).get("items", [])

    if not items:
        st.info("No inventory listed yet. Go to **Upload Inventory** to add items!")
        return

    st.caption(f"{len(items)} active listing(s)")

    for item in items:
        lt    = item.get("listing_type") or "sell"
        price = item.get("price")
        badge = _lt_badge(lt, price)

        expiry_raw = item.get("expiry_date")
        exp_cls, exp_label = _expiry_badge(expiry_raw)

        if expiry_raw:
            try:
                days_left = (datetime.strptime(expiry_raw, "%Y-%m-%d").date() - date.today()).days
                if days_left < 0:
                    expiry_display = f"❌ EXPIRED ({expiry_raw})"
                elif days_left <= 7:
                    expiry_display = f"🚨 {days_left}d left — {expiry_raw}"
                elif days_left <= 14:
                    expiry_display = f"⚠️ {days_left}d left — {expiry_raw}"
                else:
                    expiry_display = f"✅ {days_left}d left — {expiry_raw}"
            except Exception:
                expiry_display = expiry_raw
        else:
            expiry_display = "No expiry date"

        price_row = (
            f"<div class='my-item-row'>💰 <strong>Price:</strong> RM {float(price):.2f}</div>"
            if lt == "sell" and price else ""
        )

        phone_row = (
            f"<div class='my-item-row'>📞 <strong>Contact:</strong> {item['phone_number']}</div>"
            if item.get("phone_number") else ""
        )

        stock_row = (
            f"<div class='my-item-row'>🏷️ <strong>Stock Name:</strong> {item['stock_name']}</div>"
            if item.get("stock_name") else ""
        )

        desc      = item.get("description") or ""
        desc_block = f"<p class='my-item-desc'>{desc}</p>" if desc else ""

        seller_shipped = item.get("seller_shipped", False)
        buyer_received = item.get("buyer_received", False)

        img_col, info_col = st.columns([1, 2])

        with img_col:
            if item.get("image_path"):
                st.image(item["image_path"], use_container_width=True)
            else:
                st.markdown(
                    "<div style='height:140px;background:#f0fdf4;border-radius:10px;"
                    "display:flex;align-items:center;justify-content:center;"
                    "color:#86efac;font-size:2.5rem'>🏭</div>",
                    unsafe_allow_html=True,
                )

        with info_col:
            st.markdown(f"""
            <div class="my-item-card">
                <p class="my-item-title">
                    {html.escape(item.get('item_name',''))} {badge}
                    <span class="lt-badge {exp_cls}">{exp_label}</span>
                </p>
                {stock_row}
                <div class="my-item-row">🏷️ <strong>Category:</strong> {item.get('category','—')}</div>
                <div class="my-item-row">📍 <strong>Region:</strong> {item.get('region','—')}</div>
                <div class="my-item-row">📦 <strong>Quantity:</strong> {item.get('quantity',1)}</div>
                <div class="my-item-row">📅 <strong>Expiry:</strong> {expiry_display}</div>
                {price_row}{phone_row}{desc_block}
            </div>
            """, unsafe_allow_html=True)

            item_id = item["item_id"]

            # ── TRANSACTION STATE DISPLAY ─────────────────────────────────────
            completed_key = f"co_inv_completed_{item_id}"
            if completed_key not in st.session_state:
                st.session_state[completed_key] = False

            if seller_shipped and buyer_received:
                st.success("🎉 Transaction completed!")
                if not st.session_state[completed_key]:
                    st.balloons()
                    st.toast(f"🎉 {item.get('item_name','')} completed!", icon="✅")
                    st.session_state[completed_key] = True

            elif seller_shipped and not buyer_received:
                st.success("📦 Shipped")
                st.info("⏳ Waiting for buyer to confirm receipt")

            elif not seller_shipped and buyer_received:
                st.info("📦 Buyer confirmed receipt")
                st.info("⏳ Waiting for your shipment confirmation")

            else:
                st.info("⏳ Waiting for buyers")

            # ── ACTION BUTTONS ────────────────────────────────────────────────
            reserved = item.get("status") in ["reserved", "waiting_seller", "waiting_buyer"] \
                       or item.get("buyer_received") or item.get("seller_shipped")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("📦 Shipped / Sent Out", key=f"co_ship_{item_id}"):
                    # check if anyone has reserved it
                    cart_check = db.get_company_cart_items(user_id)
                    cart_ids   = [i["item_id"] for i in cart_check.get("items", [])]
                    # use buyer_received as proxy for "reserved" since company items
                    # don't have a separate is_item_reserved method
                    item_row = db.get_company_inventory(user_id)
                    item_live = next(
                        (i for i in item_row.get("items", []) if i["item_id"] == item_id), None
                    )
                    if item_live and item_live.get("seller_shipped"):
                        st.warning("Already marked as shipped.")
                    else:
                        result = db.mark_company_item_shipped(item_id)
                        if result.get("success"):
                            st.success("Item marked as shipped.")
                            st.rerun()
                        else:
                            st.error(result.get("error"))

            with col2:
                if st.button("🗑️ Delete Listing", key=f"co_del_{item_id}"):
                    result = db.delete_company_item(item_id, user_id)
                    if result.get("success"):
                        st.success("Listing deleted.")
                        st.rerun()
                    else:
                        st.error(result.get("error"))

        st.markdown("---")