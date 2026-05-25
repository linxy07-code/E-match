import streamlit as st
import html

from c_styles import COMPANY_CSS
from c_helpers import _expiry_badge


def render_company_dashboard(db, user_id):
    st.markdown(COMPANY_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="co-header">
        <h1>🏢 Company Dashboard</h1>
        <p>Inventory overview and expiry alert centre</p>
    </div>""", unsafe_allow_html=True)

    stats = db.get_company_stats(user_id)

    st.markdown(f"""
    <div class="co-metric-row">
        <div class="co-metric-card">
            <div class="co-metric-value">{stats['total_listings']}</div>
            <div class="co-metric-label">Active Listings</div>
        </div>
        <div class="co-metric-card">
            <div class="co-metric-value">{stats['near_expiry']}</div>
            <div class="co-metric-label">Expiring ≤ 14 Days</div>
        </div>
        <div class="co-metric-card">
            <div class="co-metric-value">{stats['completed_sales']}</div>
            <div class="co-metric-label">Completed Sales</div>
        </div>
        <div class="co-metric-card">
            <div class="co-metric-value">RM {stats['total_revenue']:,.2f}</div>
            <div class="co-metric-label">Total Revenue</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### ⏰ Expiry Alerts (Next 14 Days)")
    near = db.get_near_expiry_company_items(user_id, days=14)

    if not near:
        st.success("All clear.")
        return

    for item in near:
        cls, label = _expiry_badge(item.get("expiry_date"))

        st.markdown(f"""
        <div class="co-alert-box">
            📦 {html.escape(str(item.get('item_name')))}
            <span class="mp-badge {cls}">{label}</span>
        </div>
        """, unsafe_allow_html=True)