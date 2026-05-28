# company_cart.py  ── drop-in replacement for render_company_cart()
# Mirrors the EXACT same structure as mycart.py (personal cart)

import streamlit as st
import re
import html as html_lib


def render_company_cart(db, user_id):
    st.markdown("""
    <div class="co-header">
        <h1>🛒 My Order Cart</h1>
        <p>Company items you have reserved from the marketplace</p>
    </div>""", unsafe_allow_html=True)

    db_result = db.get_company_cart_items(user_id)
    items = db_result.get("items", [])

    if not items:
        st.info("Your cart is empty. Browse the **Company Marketplace** to reserve items.")
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
                    "font-size:2.5rem'>🏭</div>",
                    unsafe_allow_html=True,
                )

        with col2:
            item_id      = item["item_id"]
            item_name    = str(item.get("item_name") or "")
            seller_name  = str(item.get("company_name") or item.get("seller_name") or "Unknown")
            region       = str(item.get("region") or "—")
            category     = str(item.get("category") or "—")
            raw_desc     = str(item.get("description") or "No description provided")
            listing_type = item.get("listing_type") or "sell"

            seller_shipped = item.get("seller_shipped", False)
            buyer_received = item.get("buyer_received", False)

            # sanitise description
            raw_desc = re.sub(r"<[^>]+>", "", raw_desc).strip()
            raw_desc = html_lib.unescape(raw_desc)

            price_display = (
                f"RM {float(item['price']):.2f}" if item.get("price") else "Free / Exchange"
            )

            st.markdown(f"### {item_name}")

            info_lines = [
                f"🏢 **Company:** {seller_name}",
                f"📍 **Region:** {region}",
                f"🏷️ **Category:** {category}",
                f"💰 **Price:** {price_display}",
            ]

            if item.get("phone_number"):
                info_lines.append(f"📞 **Contact:** {item['phone_number']}")

            if listing_type == "exchange":
                offer = item.get("exchange_offer") or "—"
                want  = item.get("exchange_want")  or "—"
                info_lines.append(f"🔄 **Offering:** {offer}")
                info_lines.append(f"🎯 **Wanted:** {want}")
            else:
                info_lines.append(f"💬 **Description:** {raw_desc}")

            st.markdown("  \n".join(info_lines))

            # ─────────────────────────────────────────────────────────────────
            # TRANSACTION STATUS  (identical logic to mycart.py)
            # ─────────────────────────────────────────────────────────────────

            completed_key = f"co_txn_completed_{item_id}"
            if completed_key not in st.session_state:
                st.session_state[completed_key] = False

            # CASE 3: both confirmed → COMPLETED
            if seller_shipped and buyer_received:
                st.success("🎉 Transaction completed!")
                if not st.session_state[completed_key]:
                    st.balloons()
                    st.toast(f"🎉 {item_name} transaction completed!", icon="✅")
                    st.session_state[completed_key] = True

            # CASE 1: seller shipped first → buyer needs to confirm
            elif seller_shipped and not buyer_received:
                st.success("📦 Seller has shipped your item! Please confirm receipt.")

            # CASE 2: buyer pressed received first → waiting for seller
            elif not seller_shipped and buyer_received:
                st.info("⏳ Waiting for seller to confirm shipment")

            # DEFAULT: nothing done yet
            else:
                pass

            # ─────────────────────────────────────────────────────────────────
            # ACTION BUTTONS  (identical structure to mycart.py)
            # ─────────────────────────────────────────────────────────────────

            received_key = f"co_received_clicked_{item_id}"
            if received_key not in st.session_state:
                st.session_state[received_key] = False

            if st.session_state[received_key]:
                st.info("✅ Receipt confirmed — transaction is being processed.")
            else:
                b1, b2 = st.columns(2)

                with b1:
                    if st.button("❌ Cancel Reservation", key=f"co_cancel_{item_id}"):
                        db.cancel_company_reservation(item_id)
                        st.warning("Reservation cancelled.")
                        st.rerun()

                with b2:
                    if st.button("✅ Received Item", key=f"co_received_{item_id}"):
                        result = db.mark_company_item_received(item_id)

                        if result.get("success"):
                            st.session_state[received_key] = True

                            # ONLY show completion popup when BOTH sides confirmed
                            # (mirrors mycart.py: checks seller_shipped before popping)
                            if seller_shipped:
                                st.balloons()
                                st.session_state["show_txn_complete_dialog"] = True
                                st.session_state["txn_complete_item"] = item_name

                            st.rerun()
                        else:
                            st.error(f"Could not update: {result.get('error')}")

        st.markdown("---")