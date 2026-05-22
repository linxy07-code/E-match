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

            # ── BUTTONS / STATUS ─────────────────────────────

            # ── TRANSACTION STATUS / BUTTONS ─────────────────────────────

            item_id = item["item_id"]

            # initialize temp state if not exists
            if f"received_clicked_{item_id}" not in st.session_state:
                st.session_state[f"received_clicked_{item_id}"] = False

            # ── AFTER CLICK STATE ─────────────────────────────
            if st.session_state[f"received_clicked_{item_id}"]:

                st.info("⏳ Waiting for seller to confirm transaction.")

            # ── NORMAL STATE ─────────────────────────────
            else:

                b1, b2 = st.columns(2)

                # ❌ CANCEL BUTTON
                with b1:
                    if st.button(
                        "❌ Cancel Reservation",
                        key=f"cancel_{item_id}"
                    ):
                        db.cancel_reservation(item_id)
                        st.warning("Reservation cancelled.")
                        st.rerun()

                # ✅ RECEIVED BUTTON
                with b2:
                    if st.button(
                        "✅ Received Item",
                        key=f"received_{item_id}"
                    ):
                        db.mark_item_received(item_id)

                        # store temporary UI state
                        st.session_state[f"received_clicked_{item_id}"] = True

                        st.rerun()