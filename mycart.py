# mycart.py
import streamlit as st
from database import EcoMatchDB

db = EcoMatchDB()


def render_cart_page():
    st.markdown(
        """<div class="page-header">
            <h1>🛒 My Cart</h1>
            <p>Items you have reserved from the marketplace</p>
        </div>""",
        unsafe_allow_html=True,
    )

    user_id  = st.session_state.get("user_id")
    db_result = db.get_cart_items(user_id)
    items    = db_result.get("items", [])

    if not items:
        st.info("Your cart is empty. Browse the **Marketplace** to reserve items.")
        return

    st.caption(f"{len(items)} reserved item(s)")

    for item in items:
        col1, col2 = st.columns([1, 2])

        with col1:
            if item.get("image_path"):
                st.image(item["image_path"], use_container_width=True)
            else:
                st.markdown(
                    "<div style='height:140px;background:#f0fdf4;border-radius:10px;"
                    "display:flex;align-items:center;justify-content:center;"
                    "font-size:2.5rem'>📦</div>",
                    unsafe_allow_html=True,
                )

        with col2:
            price_display   = f"RM {item['price']}" if item.get("price") else "Free / Exchange"
            phone_display   = f"\n📞 **Contact:** {item['phone_number']}" if item.get("phone_number") else ""
            seller_shipped  = item.get("seller_shipped", False)
            buyer_received  = item.get("buyer_received", False)

            st.markdown(f"""
### {item['item_name']}

👤 **Seller:** {item.get('seller_name', 'Unknown')}  
📍 **Region:** {item.get('region', '—')}  
🏷️ **Category:** {item.get('category', '—')}  
🔍 **Condition:** {item.get('condition', '—')}  
💰 **Price:** {price_display}{phone_display}  

💬 **Description:** {item.get('description', 'No description provided')}
            """)

            item_id = item["item_id"]

            # ── Show shipping status ─────────────────────────────────────────
            if seller_shipped and not buyer_received:
                st.success("📦 Seller has shipped your item! Please confirm receipt below.")
            elif not seller_shipped:
                st.info("⏳ Waiting for seller to ship the item.")

            received_key = f"received_clicked_{item_id}"
            if received_key not in st.session_state:
                st.session_state[received_key] = False

            if st.session_state[received_key]:
                st.info("✅ Receipt confirmed. Waiting for the transaction to be fully closed.")
            else:
                b1, b2 = st.columns(2)

                with b1:
                    if st.button("❌ Cancel Reservation", key=f"cancel_{item_id}"):
                        db.cancel_reservation(item_id)
                        st.warning("Reservation cancelled.")
                        st.rerun()

                with b2:
                    if st.button("✅ Received Item", key=f"received_{item_id}"):
                        result = db.mark_item_received(item_id)
                        if result.get("success"):
                            st.session_state[received_key] = True
                            # Trigger the transaction complete congratulations dialog
                            st.session_state["show_txn_complete_dialog"] = True
                            st.session_state["txn_complete_item"] = item.get("item_name", "item")
                            st.rerun()
                        else:
                            st.error(f"Could not update: {result.get('error')}")

        st.markdown("---")