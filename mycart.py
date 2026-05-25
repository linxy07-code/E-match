# mycart.py
import streamlit as st
from database import EcoMatchDB
import re
import html as html_lib

db = EcoMatchDB()


def render_cart_page():
    st.markdown("""
    <div class="page-header">
        <h1>🛒 My Cart</h1>
        <p>Items you have reserved from the marketplace</p>
    </div>""", unsafe_allow_html=True)

    user_id = st.session_state.get("user_id")
    db_result = db.get_cart_items(user_id)
    items = db_result.get("items", [])

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
            item_name = str(item.get("item_name") or "")
            seller_name = str(item.get("seller_name") or "Unknown")
            region = str(item.get("region") or "—")
            category = str(item.get("category") or "—")
            condition = str(item.get("condition") or "—")
            raw_desc = str(item.get("description") or "No description provided")

            seller_shipped = item.get("seller_shipped", False)
            buyer_received = item.get("buyer_received", False)

            raw_desc = re.sub(r"<[^>]+>", "", raw_desc).strip()
            raw_desc = html_lib.unescape(raw_desc)

            price_display = (
                f"RM {float(item['price']):.2f}" if item.get("price") else "Free / Exchange"
            )

            st.markdown(f"### {item_name}")

            info_lines = [
                f"👤 **Seller:** {seller_name}",
                f"📍 **Region:** {region}",
                f"🏷️ **Category:** {category}",
                f"🔍 **Condition:** {condition}",
                f"💰 **Price:** {price_display}",
            ]

            if item.get("phone_number"):
                info_lines.append(f"📞 **Contact:** {item['phone_number']}")

            st.markdown("  \n".join(info_lines))
            st.markdown(f"💬 **Description:** {raw_desc}")

            # ─────────────────────────────────────────────
            # TRANSACTION STATUS LOGIC (FIXED)
            # ─────────────────────────────────────────────

            item_id = item["item_id"]

            completed_key = f"txn_completed_{item_id}"
            if completed_key not in st.session_state:
                st.session_state[completed_key] = False

            # CASE 3: COMPLETED (ONLY WHEN BOTH TRUE)
            if seller_shipped and buyer_received:

                st.success("🎉 Transaction completed!")

                # trigger only once
                if not st.session_state[completed_key]:
                    st.balloons()
                    st.toast(f"🎉 {item_name} transaction completed!", icon="✅")
                    st.session_state[completed_key] = True

            # CASE 1: seller shipped first
            elif seller_shipped and not buyer_received:
                st.success("📦 Seller has shipped your item! Please confirm receipt.")

            # CASE 2: buyer received first (NO POPUP HERE ANYMORE)
            elif not seller_shipped and buyer_received:
                st.info("⏳ Waiting for seller to confirm transaction")

            # DEFAULT
            else:
                pass

            # ─────────────────────────────────────────────
            # ACTION BUTTONS
            # ─────────────────────────────────────────────

            received_key = f"received_clicked_{item_id}"
            if received_key not in st.session_state:
                st.session_state[received_key] = False

            if st.session_state[received_key]:
                st.info("✅ Receipt confirmed — transaction is being processed.")
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

                            # ONLY SHOW POPUP IF BOTH CONDITIONS ARE TRUE NOW
                            if seller_shipped:
                                st.balloons()
                                st.session_state["show_txn_complete_dialog"] = True
                                st.session_state["txn_complete_item"] = item_name

                            st.rerun()
                        else:
                            st.error(f"Could not update: {result.get('error')}")

        st.markdown("---")