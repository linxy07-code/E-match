import streamlit as st
import html
from datetime import datetime, date

from c_styles import COMPANY_CSS
from c_helpers import _expiry_badge, _lt_badge


def render_company_inventory(db, user_id):
    st.markdown(COMPANY_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="co-header">
        <h1>🗂️ My Uploads / Items</h1>
        <p>All items your company has listed — sorted by expiry date</p>
    </div>""", unsafe_allow_html=True)

    items = db.get_company_inventory(user_id).get("items", [])

    if not items:
        st.info("No inventory listed yet.")
        return

    for item in items:
        lt = item.get("listing_type") or "sell"
        price = item.get("price")

        exp_cls, exp_label = _expiry_badge(item.get("expiry_date"))
        badge = _lt_badge(lt, price)

        expiry_raw = item.get("expiry_date")

        if expiry_raw:
            try:
                days_left = (datetime.strptime(expiry_raw, "%Y-%m-%d").date() - date.today()).days
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
            except:
                row_css = ""
                expiry_display = expiry_raw
        else:
            row_css = ""
            expiry_display = "No expiry"

        col1, col2 = st.columns([1, 2])

        with col1:
            if item.get("image_path"):
                st.image(item["image_path"], use_container_width=True)
            else:
                st.markdown("🏭 No Image")

        with col2:
            st.markdown(f"""
            <div class="co-item-card">
                <p class="co-item-title">
                    {html.escape(item.get('item_name',''))} {badge}
                    <span class="mp-badge {exp_cls}">{exp_label}</span>
                </p>

                <div class="co-item-row">📦 Qty: {item.get('quantity',1)}</div>
                <div class="co-item-row {row_css}">📅 {expiry_display}</div>
            </div>
            """, unsafe_allow_html=True)