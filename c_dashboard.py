import streamlit as st
import pandas as pd


def render_company_dashboard(db, user_id):

    st.markdown("""
    <div style="background:#1d4ed8; padding:16px; border-radius:12px; color:white;">
        <h1>📊 Analytics Dashboard</h1>
        <p>Company performance and regional activity overview</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:25px'></div>", unsafe_allow_html=True)

    # ─────────────────────────────
    # STATS
    # ─────────────────────────────
    stats = db.get_company_stats(user_id)

    total_listings  = stats.get("total_listings", 0)
    near_expiry     = stats.get("near_expiry", 0)
    completed_sales = stats.get("completed_sales", 0)
    total_revenue   = stats.get("total_revenue", 0)

    listing_delta = stats.get("listings_delta", 0)
    sales_delta   = stats.get("sales_delta", 0)

    def fmt(v):
        try:
            v = int(v)
            return f"+{v}" if v >= 0 else str(v)
        except:
            return str(v)

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card"><div class="metric-value">{total_listings}</div><div class="metric-label">Active Listings</div><div class="metric-delta">↑ {fmt(listing_delta)} this week</div></div>
        <div class="metric-card"><div class="metric-value">{near_expiry}</div><div class="metric-label">Near Expiry</div><div class="metric-delta">{"✓ All clear" if near_expiry == 0 else "⚠ Needs attention"}</div></div>
        <div class="metric-card"><div class="metric-value">{completed_sales}</div><div class="metric-label">Completed Sales</div><div class="metric-delta">↑ {fmt(sales_delta)} this month</div></div>
        <div class="metric-card"><div class="metric-value">RM {float(total_revenue):,.2f}</div><div class="metric-label">Total Trading Revenue</div><div class="metric-delta">Revenue tracked</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ─────────────────────────────
    # TABS
    # ─────────────────────────────
    tab_a, tab_b = st.tabs(["📈  Monthly Trends", "🗺️  Regional Breakdown"])

    months_labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    region_labels = [
        "Johor", "Kelantan", "Terengganu", "Negeri Sembilan",
        "Sabah", "Selangor", "Perlis", "Perak",
        "Pahang", "Kedah", "Sarawak", "Melaka",
        "Pulau Pinang", "Kuala Lumpur"
    ]

    # ─────────────────────────────
    # MONTHLY LISTINGS
    # ─────────────────────────────
    with tab_a:
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("Monthly Company Listings")

            df = pd.DataFrame({"month": months_labels, "value": [0]*12})

            try:
                raw = db.get_company_monthly_listings()
                if raw:
                    db_df = pd.DataFrame(raw)
                    for _, row in db_df.iterrows():
                        month = str(row["month"]).strip()
                        if month in months_labels:
                            df.loc[df["month"] == month, "value"] = row["listings"]
            except:
                pass

            st.bar_chart(df, x="month", y="value", height=260)

        with c2:
            st.markdown("Monthly Sales")

            df = pd.DataFrame({"month": months_labels, "value": [0]*12})

            try:
                raw = db.get_company_monthly_sales()
                if raw:
                    db_df = pd.DataFrame(raw)
                    for _, row in db_df.iterrows():
                        month = str(row["month"]).strip()
                        if month in months_labels:
                            df.loc[df["month"] == month, "value"] = row["sales"]
            except:
                pass

            st.bar_chart(df, x="month", y="value", height=260)

    # ─────────────────────────────
    # REGIONS
    # ─────────────────────────────
    with tab_b:
        c3, c4 = st.columns(2)

        with c3:
            st.markdown("Sales by Region")

            df = pd.DataFrame({"region": region_labels, "value": [0]*len(region_labels)})

            try:
                raw = db.get_company_sales_by_region()
                if raw:
                    db_df = pd.DataFrame(raw)
                    for _, row in db_df.iterrows():
                        region = str(row["region"]).strip()
                        if region in region_labels:
                            df.loc[df["region"] == region, "value"] = row["sales"]
            except:
                pass

            st.bar_chart(df, x="region", y="value", height=260)

        with c4:
            st.markdown("Users by Region")

            df = pd.DataFrame({"region": region_labels, "value": [0]*len(region_labels)})

            try:
                raw = db.get_company_users_by_region()
                if raw:
                    db_df = pd.DataFrame(raw)
                    for _, row in db_df.iterrows():
                        region = str(row["region"]).strip()
                        if region in region_labels:
                            df.loc[df["region"] == region, "value"] = row["users"]
            except:
                pass

            st.bar_chart(df, x="region", y="value", height=260)

    # ─────────────────────────────
    # EXPIRY TABLE
    # ─────────────────────────────
    st.markdown("---")
    st.markdown("### ⏳ Items Approaching Expiry")

    try:
        data = db.get_company_expiring_items()

        if data:
            df = pd.DataFrame(data)
            if not df.empty:
                df.columns = [c.replace("_", " ").title() for c in df.columns]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("🎉 No items expiring soon!")
        else:
            st.info("🎉 No items expiring soon!")

    except:
        st.info("🎉 No items expiring soon!")