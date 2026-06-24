import streamlit as st
import time


def render_my_items_page(db, user_id, get_transaction_status, _lt_badge):
    st.markdown(
        '<div class="page-header"><h1>🧾 My Uploads / Items</h1>'
        "<p>All items you have posted to the marketplace</p></div>",
        unsafe_allow_html=True,
    )

    items_res = db.get_user_items(user_id)
    items = items_res.get("items", [])

    for item in items:
        item["reserved"] = db.is_item_reserved(item["item_id"])

    def priority(item):
        reserved = item["reserved"]
        seller_shipped = item.get("seller_shipped", False)

        # 1. reserved + not shipped (HIGHEST)
        if reserved and not seller_shipped:
            return 0

        # 2. reserved + shipped
        if reserved and seller_shipped:
            return 1

        # 3. not reserved
        return 2


    items.sort(key=priority)

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
        expiry_row = (
            f"<div class='my-item-row'>📅 <strong>Expires:</strong> {exp}</div>"
            if exp
            else ""
        )

        desc = item.get("description") or ""
        desc_block = f"<p class='my-item-desc'>{desc}</p>" if desc else ""

        img_col, info_col = st.columns([1, 2])

        with img_col:
            if item.get("image_path"):
                st.image(item["image_path"], use_container_width=True)
            else:
                st.markdown(
                    "<div style='height:140px;background:#f0fdf4;border-radius:10px;"
                    "display:flex;align-items:center;justify-content:center;"
                    "color:#86efac;font-size:2.5rem'>📦</div>",
                    unsafe_allow_html=True,
                )

        with info_col:
            st.markdown(f"""
            <div class="my-item-card">
                <p class="my-item-title">{item['item_name']} {badge}</p>
                <div class="my-item-row">🏷️ <strong>Category:</strong> {item.get('category','—')}</div>
                <div class="my-item-row">📍 <strong>Region:</strong> {item.get('region','—')}</div>
                <div class="my-item-row">🔍 <strong>Condition:</strong> {item.get('condition','—')}</div>
                <div class="my-item-row">📦 <strong>Quantity:</strong> {item.get('quantity',1)}</div>
                {price_row}{phone_row}{expiry_row}{desc_block}
            </div>
            """, unsafe_allow_html=True)

            item_id = item["item_id"]

            seller_shipped = item.get("seller_shipped", False)
            buyer_received = item.get("buyer_received", False)

            reserved = item["reserved"]

            # ─────────────────────────────────────────────
            # SESSION FLAGS
            # ─────────────────────────────────────────────

            completed_key = f"completed_{item_id}"
            buyer_first_key = f"buyer_first_{item_id}"
            seller_first_key = f"seller_first_{item_id}"

            if completed_key not in st.session_state:
                st.session_state[completed_key] = False

            if buyer_first_key not in st.session_state:
                st.session_state[buyer_first_key] = False

            if seller_first_key not in st.session_state:
                st.session_state[seller_first_key] = False

            # ─────────────────────────────────────────────
            # TRANSACTION LOGIC
            # ─────────────────────────────────────────────

            # CASE 3: FULL COMPLETE
            if seller_shipped and buyer_received:
                st.success("🎉 Transaction completed!")

                if not st.session_state[completed_key]:
                    st.balloons()
                    st.toast(f"🎉 {item['item_name']} completed!", icon="✅")
                    st.session_state[completed_key] = True

            # CASE 1: seller shipped first
            elif seller_shipped and not buyer_received:
                st.success("📦 Shipped")
                st.info("⏳ Waiting for buyer to confirm transaction")

            # ⭐ CASE 2: buyer confirmed first → SELLER SHOULD GET POPUP
            elif buyer_received and not seller_shipped:
                st.info("📦 Received by buyer")
                st.info("⏳ Please confirm shipment")

                if not st.session_state[buyer_first_key]:
                    st.session_state[buyer_first_key] = True
                    st.balloons()
                    st.toast(f"📦 Buyer confirmed {item['item_name']}!", icon="🎉")

            # DEFAULT
            else:
                if reserved:
                    st.info("🛒 Item is reserved by a buyer")
                else:
                    st.info("⏳ Waiting for buyers")

            # ─────────────────────────────────────────────
            # ACTION BUTTONS
            # ─────────────────────────────────────────────


            col1, col2 = st.columns(2)

            with col1:
                if st.button("📦 Shipped / Sent Out", key=f"ship_{item_id}"):

                    if not reserved:
                        st.error("❌ Cannot ship: Item is not reserved.")
                        time.sleep(2)
                        st.rerun()
                    else:
                        result = db.mark_item_shipped(item_id)

                        if result.get("success"):
                            st.success("Item marked as shipped.")
                            st.rerun()
                        else:
                            st.error(result.get("error"))

            with col2:
                if st.button("🗑️ Delete Listing", key=f"del_{item_id}"):

                    result = db.delete_item(item_id, user_id)

                    if result.get("success"):
                        st.success("Listing deleted.")
                        st.rerun()
                    else:
                        st.error(result.get("error"))

        st.markdown("---")