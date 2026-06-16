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
        css = "lt-sell"
    elif listing_type == "exchange":
        label, css = "🔄 Exchange", "lt-exchange"
    else:
        label, css = "🆓 Free", "lt-free"
    return f'<span class="lt-badge {css}">{label}</span>'


def render_company_items(db, user_id):
    # Blue Header Section
    st.markdown(
        """
        <div class="page-header" style="background: linear-gradient(135deg, #1e40af, #3b82f6); color: white; padding: 2rem; border-radius: 20px; margin-bottom: 1.5rem;">
            <h1 style="color: white; margin: 0; font-size: 2.2rem;">🧾 My Uploads / Items</h1>
            <p style="color: #e0f2fe; margin: 0.5rem 0 0 0; opacity: 0.9;">All items your company has posted to the marketplace</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    items_res = db.get_company_items(user_id)
    items = items_res.get("items", [])

    if not items:
        st.info("You haven't posted any items yet. Go to **Upload Item** to get started!")
        return

    st.caption(f"{len(items)} active listing(s)")

    for item in items:
        lt = item.get("listing_type") or "free"
        price = item.get("price")
        badge = _lt_badge(lt, price)

        price_row = (
            f"<div class='my-item-row'>💰 <strong>Price:</strong> RM {float(price):.2f}</div>"
            if lt == "sell" and price
            else ""
        )

        phone_row = (
            f"<div class='my-item-row'>📞 <strong>Contact:</strong> {item['phone_number']}</div>"
            if item.get("phone_number")
            else ""
        )

        exp = item.get("expiry_date")
        desc = item.get("description") or ""
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
                <p class="my-item-title">{item['item_name']} {badge}</p>
                <div class="my-item-row">🏷️ <strong>Category:</strong> {item.get('category','—')}</div>
                <div class="my-item-row">📍 <strong>Region:</strong> {item.get('region','—')}</div>
                <div class="my-item-row">📦 <strong>Quantity:</strong> {item.get('quantity',1)}</div>
                <div class="my-item-row">📅 <strong>Expiry:</strong> {exp or 'No expiry date'}</div>
                {price_row}{phone_row}{desc_block}
            </div>
            """, unsafe_allow_html=True)

            item_id = item["item_id"]
            reserved = db.is_company_item_reserved(item_id)

            completed_key = f"co_completed_{item_id}"
            if completed_key not in st.session_state:
                st.session_state[completed_key] = False

            # TRANSACTION STATUS LOGIC
            if seller_shipped and buyer_received:
                st.success("🎉 Transaction completed!")
                if not st.session_state.get(completed_key):
                    st.session_state[completed_key] = True
                    st.balloons()
                    st.toast(f"🎉 {item['item_name']} completed!", icon="✅")

            elif seller_shipped:
                st.success("📦 Shipped")
                st.info("⏳ Waiting for buyer to confirm receipt")

            elif reserved:
                st.info("📦 Item reserved by buyer")
                st.info("⏳ Waiting for seller to ship")

            else:
                # UPDATED: This now matches the blue "Waiting for buyers" style
                st.info("⏳ Waiting for buyers")

            # ACTION BUTTONS
            col1, col2 = st.columns(2)

            with col1:
                if st.button("📦 Shipped / Sent Out", key=f"co_ship_{item_id}"):
                    if not reserved:
                        st.error("❌ Cannot ship: Item is not reserved.")
                        time.sleep(2)
                        st.rerun()
                    else:
                        result = db.mark_company_item_shipped(item_id)
                        if result.get("success"):
                            updated = db.get_company_items(user_id)
                            item_live = next((i for i in updated.get("items", []) if i["item_id"] == item_id), {})
                            if item_live.get("buyer_received"):
                                st.balloons()
                                st.session_state["show_txn_complete_dialog"] = True
                                st.session_state["txn_complete_item"] = item["item_name"]
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