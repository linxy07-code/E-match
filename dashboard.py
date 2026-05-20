import streamlit as st
import pandas as pd

def render_dashboard_page(db):
    st.markdown("""
    <div class="page-header">
        <h1>📊 Analytics Dashboard</h1>
        <p>Platform performance and regional activity overview</p>
    </div>""", unsafe_allow_html=True)

    # 1. Pull dynamic platform numbers
    stats = db.get_platform_stats()

    total_matches   = stats.get("total_matches", 0)
    active_listings = stats.get("active_listings", 0)
    total_users     = stats.get("total_users", 0)
    near_expiry     = stats.get("near_expiry_count", 0)
    avg_trust       = stats.get("avg_trust_score", 0.0)

    match_delta     = stats.get("matches_this_week_delta", "+0")
    listing_delta   = stats.get("listings_today_delta", "+0")
    user_delta      = stats.get("users_this_month_delta", "+0")

    # 2. Inject numbers into the metrics component
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card"><div class="metric-value">{total_matches:,}</div><div class="metric-label">Total Matches</div><div class="metric-delta">↑ {match_delta} this week</div></div>
        <div class="metric-card"><div class="metric-value">{active_listings:,}</div><div class="metric-label">Active Listings</div><div class="metric-delta">↑ {listing_delta} today</div></div>
        <div class="metric-card"><div class="metric-value">{total_users:,}</div><div class="metric-label">Registered Users</div><div class="metric-delta">↑ {user_delta} this month</div></div>
        <div class="metric-card"><div class="metric-value">{near_expiry}</div><div class="metric-label">Near Expiry</div><div class="metric-delta" style="color:#dc2626">{"⚠ Needs attention" if near_expiry > 0 else "✓ All clear"}</div></div>
        <div class="metric-card"><div class="metric-value">{float(avg_trust):.1f}</div><div class="metric-label">Avg Trust Score</div><div class="metric-delta">↑ Excellent</div></div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Dynamic Charts 
    tab_a, tab_b = st.tabs(["📈  Monthly Trends", "🗺️  Regional Breakdown"])
    with tab_a:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("Monthly Matches — 2026")
            monthly_matches = db.get_monthly_matches()
            if not monthly_matches:
                monthly_matches = {"Matches": [0]*12}
            st.bar_chart(monthly_matches, height=260)
        with c2:
            st.markdown("Items Listed per Month — 2026")
            monthly_items = db.get_monthly_items()
            if not monthly_items:
                monthly_items = {"Items Listed": [0]*12}
            st.bar_chart(monthly_items, height=260)
            
    with tab_b:
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("Matches by Region")
            region_matches = db.get_matches_by_region()
            if not region_matches:
                region_matches = {"Matches": [0, 0, 0, 0, 0]}
            st.bar_chart(region_matches, height=260)
            st.caption("Selangor · KL · Penang · Johor · Others")
        with c4:
            st.markdown("Users by Region")
            users_region = db.get_users_by_region()
            if not users_region:
                users_region = {"Users": [0, 0, 0, 0, 0]}
            st.bar_chart(users_region, height=260)
            st.caption("Selangor · KL · Penang · Johor · Others")

    # 4. Critical Live Table 
    st.markdown("---")
    st.markdown("### ⏳ Items Approaching Expiry")
    
    expiring_items_data = db.get_expiring_items()
    if expiring_items_data:
        st.dataframe(pd.DataFrame(expiring_items_data), use_container_width=True, hide_index=True)
    else:
        st.info("🎉 Perfect. No items are expiring soon or require immediate allocation!")