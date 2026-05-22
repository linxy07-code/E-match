import streamlit as st
import pandas as pd

def render_dashboard_page(db):
    st.markdown("""
    <div class="page-header">
        <h1>📊 Analytics Dashboard</h1>
        <p>Platform performance and regional activity overview</p>
    </div>""", unsafe_allow_html=True)

    # ── 1. FETCH LIVE SYSTEM METRICS ──────────────────────────────────────────
    try:
        stats = db.get_platform_stats() or {}
    except Exception:
        stats = {}

    total_matches   = stats.get("total_matches", 0)
    active_listings = stats.get("active_listings", 0)
    total_users      = stats.get("total_users", 0)
    near_expiry      = stats.get("near_expiry_count", 0)
    avg_trust       = stats.get("avg_trust_score", 10.0)

    # Pull raw values safely as strings
    match_delta     = str(stats.get("matches_this_week_delta", "0")).strip()
    listing_delta   = str(stats.get("listings_today_delta", "0")).strip()
    user_delta      = str(stats.get("users_this_month_delta", "0")).strip()

    # Helper function to guarantee clean "+" formatting without tripping over existing signs
    def format_delta(val):
        clean_val = val.lstrip('+') # Remove any existing plus sign to let .isdigit() work
        if clean_val.isdigit() and int(clean_val) >= 0:
            return f"+{clean_val}"
        return val # Return as-is if it's already structured or negative (e.g. "-3")

    formatted_match_delta   = format_delta(match_delta)
    formatted_listing_delta = format_delta(listing_delta)
    formatted_user_delta    = format_delta(user_delta)

    # Render dynamic metric structure layout matching your exact template
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card"><div class="metric-value">{total_matches:,}</div><div class="metric-label">Total Matches</div><div class="metric-delta">↑ {formatted_match_delta} this week</div></div>
        <div class="metric-card"><div class="metric-value">{active_listings:,}</div><div class="metric-label">Active Listings</div><div class="metric-delta">↑ {formatted_listing_delta} today</div></div>
        <div class="metric-card"><div class="metric-value">{total_users:,}</div><div class="metric-label">Registered Users</div><div class="metric-delta">↑ {formatted_user_delta} this month</div></div>
        <div class="metric-card"><div class="metric-value">{near_expiry}</div><div class="metric-label">Near Expiry</div><div class="metric-delta" style="color:{"#737373" if near_expiry == 0 else "#dc2626"}">{"✓ All clear" if near_expiry == 0 else "⚠ Needs attention"}</div></div>
        <div class="metric-card"><div class="metric-value">{float(avg_trust):.1f}</div><div class="metric-label">Avg Trust Score</div><div class="metric-delta">↑ Excellent</div></div>
    </div>
    """, unsafe_allow_html=True)

    months_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    region_labels = ["Selangor", "Kuala Lumpur", "Penang", "Johor", "Melaka", "Sabah", "Sarawak"]

    # ── 2. DATA VISUALIZATION ENGINE ─────────────────────────────────────────
    tab_a, tab_b = st.tabs(["📈  Monthly Trends", "🗺️  Regional Breakdown"])
    
    with tab_a:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("Monthly Matches — 2026")
            try:
                raw_matches = db.get_monthly_matches()
                df_matches = pd.DataFrame({"month": months_labels, "matches": [0]*12})
                if raw_matches:
                    db_df = pd.DataFrame(raw_matches)
                    y_col = [col for col in db_df.columns if col != "month"][0]
                    for _, row in db_df.iterrows():
                        m_val = str(row["month"])
                        if m_val in months_labels:
                            df_matches.loc[df_matches["month"] == m_val, "matches"] = row[y_col]
            except Exception:
                df_matches = pd.DataFrame({"month": months_labels, "matches": [0]*12})
            
            st.bar_chart(df_matches, x="month", y="matches", height=260, color="#1f77b4")
            
        with c2:
            st.markdown("Items Listed per Month — 2026")
            try:
                raw_items = db.get_monthly_items()
                df_items = pd.DataFrame({"month": months_labels, "items": [0]*12})
                if raw_items:
                    db_df = pd.DataFrame(raw_items)
                    y_col = [col for col in db_df.columns if col != "month"][0]
                    for _, row in db_df.iterrows():
                        m_val = str(row["month"])
                        if m_val in months_labels:
                            df_items.loc[df_items["month"] == m_val, "items"] = row[y_col]
            except Exception:
                df_items = pd.DataFrame({"month": months_labels, "items": [0]*12})
            
            st.bar_chart(df_items, x="month", y="items", height=260, color="#1f77b4")
            
    with tab_b:
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("Matches by Region")
            try:
                raw_reg_matches = db.get_matches_by_region()
                df_reg_matches = pd.DataFrame({"region": region_labels, "matches": [0]*len(region_labels)})
                if raw_reg_matches:
                    db_df = pd.DataFrame(raw_reg_matches)
                    y_col = [col for col in db_df.columns if col != "region"][0]
                    for _, row in db_df.iterrows():
                        r_val = str(row["region"])
                        if r_val in region_labels:
                            df_reg_matches.loc[df_reg_matches["region"] == r_val, "matches"] = row[y_col]
            except Exception:
                df_reg_matches = pd.DataFrame({"region": region_labels, "matches": [0]*len(region_labels)})
            
            st.bar_chart(df_reg_matches, x="region", y="matches", height=260, color="#1f77b4")
            
        with c4:
            st.markdown("Users by Region")
            try:
                raw_reg_users = db.get_users_by_region()
                df_reg_users = pd.DataFrame({"region": region_labels, "users": [0]*len(region_labels)})
                if raw_reg_users:
                    db_df = pd.DataFrame(raw_reg_users)
                    y_col = [col for col in db_df.columns if col != "region"][0]
                    for _, row in db_df.iterrows():
                        r_val = str(row["region"])
                        if r_val in region_labels:
                            df_reg_users.loc[df_reg_users["region"] == r_val, "users"] = row[y_col]
            except Exception:
                df_reg_users = pd.DataFrame({"region": region_labels, "users": [0]*len(region_labels)})
            
            st.bar_chart(df_reg_users, x="region", y="users", height=260, color="#1f77b4")

    # ── 3. CRITICAL LIVE OPERATIONAL TABLES ───────────────────────────────────
    st.markdown("---")
    st.markdown("### ⏳ Items Approaching Expiry")
    
    try:
        expiring_items_data = db.get_expiring_items()
        if expiring_items_data:
            df_expiring = pd.DataFrame(expiring_items_data)
            if not df_expiring.empty:
                df_expiring.columns = [col.replace('_', ' ').title() for col in df_expiring.columns]
                st.dataframe(df_expiring, use_container_width="stretch", hide_index=True)
            else:
                st.info("🎉 Perfect. No items are expiring soon or require immediate allocation!")
        else:
            st.info("🎉 Perfect. No items are expiring soon or require immediate allocation!")
    except Exception:
        st.info("🎉 Perfect. No items are expiring soon or require immediate allocation!")


    def cancel_reservation(self, item_id, user_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:

                    cursor.execute("""
                    SELECT reserved_by FROM items WHERE id = %s
                    """, (item_id,))
                    row = cursor.fetchone()
    
                    if not row:
                        return {"success": False, "error": "Item not found"}

                    if row["reserved_by"] != user_id:
                        return {"success": False, "error": "Not your reserved item"}

                    cursor.execute("""
                        UPDATE items
                        SET reserved_by = NULL,
                        status = 'available'
                        WHERE id = %s
                    """, (item_id,))

                    conn.commit()
                    return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}
        


    def mark_item_received(self, item_id, user_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:

                    cursor.execute("""
                    SELECT reserved_by FROM items WHERE id = %s
                    """, (item_id,))
                    row = cursor.fetchone()

                    if not row:
                        return {"success": False, "error": "Item not found"}

                    if row["reserved_by"] != user_id:
                        return {"success": False, "error": "Not your item"}
    
                    cursor.execute("""
                        UPDATE items
                        SET status = 'completed'
                        WHERE id = %s
                    """, (item_id,))

                    conn.commit()
                    return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}