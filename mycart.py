import streamlit as st
from database import EcoMatchDB

db = EcoMatchDB()


def render_cart_page():
    st.markdown(
        """
        <div class="page-header">
            <h1>🛒 My Cart</h1>
            <p>Items you have reserved</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_id = st.session_state.get("user_id")

    db_result = db.get_cart_items(user_id)
    items = db_result.get("items", [])

    if not items:
        st.info("Your cart is empty.")
        return

    st.caption(f"{len(items)} reserved item(s)")

    for item in items:

        col1, col2 = st.columns([1, 2])

        # ── IMAGE COLUMN ─────────────────────────────
        with col1:

            if item.get("image_path"):
                st.image(
                    item["image_path"],
                    use_container_width=True
                )
            else:
                st.markdown("📦 No Image")

        # ── INFO COLUMN ──────────────────────────────
        with col2:

            st.markdown(f"""
### {item['item_name']}

👤 **Seller:** {item.get('seller_name', 'Unknown')}  
📍 **Region:** {item.get('region', '—')}  
🏷️ **Category:** {item.get('category', '—')}  
🔍 **Condition:** {item.get('condition', '—')}  

💬 **Description:**  
{item.get('description', 'No description provided')}

💰 **Price:** {"RM " + str(item['price']) if item.get("price") else "Free / Exchange"}
            """)

            # ── BUTTONS ─────────────────────────────
            b1, b2 = st.columns(2)

            # ✅ RECEIVED BUTTON
            with b1:

                if st.button(
                    "✅ Received Item",
                    key=f"received_{item['item_id']}"
                ):

                    db.complete_reservation(item["item_id"])

                    st.success("Item marked as received!")
                    st.rerun()

            # ❌ CANCEL BUTTON
            with b2:

                if st.button(
                    "❌ Cancel Reservation",
                    key=f"cancel_{item['item_id']}"
                ):

                    db.cancel_reservation(item["item_id"])

                    st.warning("Reservation cancelled.")
                    st.rerun()

        st.markdown("---")