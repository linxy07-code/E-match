import streamlit as st
from datetime import date, timedelta


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def is_expiring_soon(expiry_date):
    """Check if expiry is within 14 days."""
    if not expiry_date:
        return False
    return date.today() + timedelta(days=14) >= expiry_date


# ─────────────────────────────────────────────
# MAIN PAGE FUNCTION (IMPORTANT)
# ─────────────────────────────────────────────

def render_inventory_page(db, user_id):

    st.markdown("""
    <div style="
        background: linear-gradient(135deg,#166534,#14b8a6);
        padding: 28px;
        border-radius: 14px;
        color: white;
        margin-bottom: 20px;
    ">
        <h2 style="margin:0;">📦 My Inventory</h2>
        <p style="margin:5px 0 0;">Track your stock, expiry dates, and usage</p>
    </div>
    """, unsafe_allow_html=True)

    # ─────────────────────────────────────────
    # ADD NEW ITEM
    # ─────────────────────────────────────────
    st.subheader("➕ Add New Inventory Item")

    with st.form("add_inventory_form"):
        item_name = st.text_input("Item Name")
        quantity = st.number_input("Quantity", min_value=0.0)
        unit = st.selectbox("Unit", ["kg", "g", "pcs", "litre"])
        expiry_date = st.date_input("Expiry Date (optional)")

        submitted = st.form_submit_button("Add Item")

        if submitted:
            if not item_name:
                st.error("Item name is required.")
            else:
                db.add_inventory_item(
                    company_id=user_id,
                    item_name=item_name,
                    quantity=quantity,
                    unit=unit,
                    expiry_date=expiry_date
                )
                st.success("✅ Inventory item added successfully!")
                st.rerun()

    st.divider()

    # ─────────────────────────────────────────
    # LOAD DATA
    # ─────────────────────────────────────────
    items = db.get_inventory_by_company(user_id)

    if not items:
        st.info("No inventory items yet. Start by adding one above.")
        return

    # ─────────────────────────────────────────
    # EXPIRY ALERTS
    # ─────────────────────────────────────────
    st.subheader("⚠️ Expiring Soon (within 14 days)")

    expiring_items = [
        i for i in items if is_expiring_soon(i.get("expiry_date"))
    ]

    if expiring_items:
        for item in expiring_items:
            st.warning(
                f"⚠️ {item['item_name']} | "
                f"{item['quantity']} {item['unit']} | "
                f"Expires: {item.get('expiry_date')}"
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"📉 Use Stock - {item['id']}"):
                    st.session_state[f"use_{item['id']}"] = True

            with col2:
                if st.button(f"🛒 Send to Marketplace - {item['id']}"):
                    try:
                        db.add_marketplace_item_from_inventory(user_id, item)
                        db.mark_inventory_as_listed(item["id"], user_id)
                        st.success("Moved to marketplace!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
    else:
        st.success("🎉 No items expiring soon!")

    # ─────────────────────────────────────────
    # USAGE INPUT (SEPARATE STEP)
    # ─────────────────────────────────────────
    for item in expiring_items:
        if st.session_state.get(f"use_{item['id']}"):

            st.info(f"Updating usage for: {item['item_name']}")

            used_qty = st.number_input(
                "Quantity used",
                min_value=0.0,
                key=f"used_qty_{item['id']}"
            )

            if st.button(f"Confirm usage - {item['id']}"):
                new_qty = max(0, item["quantity"] - used_qty)

                db.update_inventory_quantity(
                    item["id"],
                    user_id,
                    new_qty
                )

                st.success("Stock updated!")
                st.session_state[f"use_{item['id']}"] = False
                st.rerun()

    st.divider()

    # ─────────────────────────────────────────
    # FULL INVENTORY LIST
    # ─────────────────────────────────────────
    st.subheader("📋 All Inventory Items")

    for item in items:

        expiring = is_expiring_soon(item.get("expiry_date"))

        st.markdown(f"""
        <div style="
            border:1px solid #d1fae5;
            padding:14px;
            border-radius:10px;
            margin-bottom:10px;
            background:{'#fef2f2' if expiring else '#ffffff'};
        ">
            <b>{item['item_name']}</b><br>
            Quantity: {item['quantity']} {item['unit']}<br>
            Expiry: {item.get('expiry_date', 'N/A')}<br>
            Status: {"⚠️ Expiring Soon" if expiring else "✅ OK"}
        </div>
        """, unsafe_allow_html=True)