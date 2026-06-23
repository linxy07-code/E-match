import streamlit as st
import pandas as pd
import altair as alt

MONTH_ORDER = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def _bar(df, x_col, y_col, order=None):
    """Render an Altair bar chart that respects explicit category order."""
    x_enc = (
        alt.X(f"{x_col}:N", sort=order, axis=alt.Axis(labelAngle=-90))
        if order
        else alt.X(f"{x_col}:N", axis=alt.Axis(labelAngle=-90))
    )
    return (
        alt.Chart(df)
        .mark_bar(color="#1d4ed8")
        .encode(x=x_enc, y=alt.Y(f"{y_col}:Q"))
        .properties(height=260)
        .configure_axis(grid=False)
    )

def _make_month_df(raw_rows, value_col):
    df = pd.DataFrame({"month": MONTH_ORDER, value_col: [0] * 12})
    if raw_rows:
        db_df = pd.DataFrame(raw_rows)
        src_cols = [c for c in db_df.columns if c != "month"]
        if src_cols:
            src_col = src_cols[0]
            for _, row in db_df.iterrows():
                m = str(row["month"]).strip()
                if m in MONTH_ORDER:
                    df.loc[df["month"] == m, value_col] = row[src_col]
    return df


def render_company_dashboard(db, user_id):
    st.markdown("""
    <div style="background:#1d4ed8; padding:16px; border-radius:12px; color:white;">
        <h1>📊 Analytics Dashboard</h1>
        <p>Company performance and regional activity overview</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:25px'></div>", unsafe_allow_html=True)

    stats = db.get_company_stats(user_id)

    total_listings  = stats.get("total_listings", 0)
    near_expiry     = stats.get("near_expiry", 0)
    completed_sales = stats.get("completed_sales", 0)
    total_revenue   = stats.get("total_revenue", 0)
    listing_delta   = stats.get("listings_delta", 0)
    sales_delta     = stats.get("sales_delta", 0)

    def fmt(v):
        try:
            v = int(v)
            return f"+{v}" if v >= 0 else str(v)
        except Exception:
            return str(v)

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card"><div class="metric-value">{total_listings}</div><div class="metric-label">Active Listings</div><div class="metric-delta">↑ {fmt(listing_delta)} this week</div></div>
        <div class="metric-card"><div class="metric-value">{near_expiry}</div><div class="metric-label">Near Expiry</div><div class="metric-delta">{"✓ All clear" if near_expiry == 0 else "⚠ Needs attention"}</div></div>
        <div class="metric-card"><div class="metric-value">{completed_sales}</div><div class="metric-label">Completed Sales</div><div class="metric-delta">↑ {fmt(sales_delta)} this month</div></div>
        <div class="metric-card"><div class="metric-value">RM {float(total_revenue):,.2f}</div><div class="metric-label">Total Trading Revenue</div><div class="metric-delta">Revenue tracked</div></div>
    </div>
    """, unsafe_allow_html=True)

    region_labels = [
        "Johor", "Kelantan", "Terengganu", "Negeri Sembilan",
        "Sabah", "Selangor", "Perlis", "Perak",
        "Pahang", "Kedah", "Sarawak", "Melaka",
        "Pulau Pinang", "Kuala Lumpur"
    ]

    tab_a, tab_b = st.tabs(["📈  Monthly Trends", "🗺️  Regional Breakdown"])

    with tab_a:
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("Monthly Company Listings")
            try:
                raw = db.get_company_monthly_listings()
            except Exception:
                raw = []
            df = _make_month_df(raw, "listings")
            st.altair_chart(_bar(df, "month", "listings", MONTH_ORDER), use_container_width=True)

        with c2:
            st.markdown("Monthly Sales")
            try:
                raw = db.get_company_monthly_sales()
            except Exception:
                raw = []
            df = _make_month_df(raw, "sales")
            st.altair_chart(_bar(df, "month", "sales", MONTH_ORDER), use_container_width=True)

    with tab_b:
        c3, c4 = st.columns(2)

        with c3:
            st.markdown("Sales by Region")
            df = pd.DataFrame({"region": region_labels, "sales": [0]*len(region_labels)})
            try:
                raw = db.get_company_sales_by_region()
                if raw:
                    db_df = pd.DataFrame(raw)
                    for _, row in db_df.iterrows():
                        r = str(row["region"]).strip()
                        if r in region_labels:
                            df.loc[df["region"] == r, "sales"] = row["sales"]
            except Exception:
                pass
            st.altair_chart(_bar(df, "region", "sales", region_labels), use_container_width=True)

        with c4:
            st.markdown("Users by Region")
            df = pd.DataFrame({"region": region_labels, "users": [0]*len(region_labels)})
            try:
                raw = db.get_company_users_by_region()
                if raw:
                    db_df = pd.DataFrame(raw)
                    for _, row in db_df.iterrows():
                        r = str(row["region"]).strip()
                        if r in region_labels:
                            df.loc[df["region"] == r, "users"] = row["users"]
            except Exception:
                pass
            st.altair_chart(_bar(df, "region", "users", region_labels), use_container_width=True)

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
    except Exception:
        st.info("🎉 No items expiring soon!")