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
        .mark_bar(color="#1f77b4")
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

def render_dashboard_page(db):
    st.markdown("""
    <div class="page-header">
        <h1>📊 Analytics Dashboard</h1>
        <p>Platform performance and regional activity overview</p>
    </div>""", unsafe_allow_html=True)

    try:
        stats = db.get_platform_stats() or {}
    except Exception:
        stats = {}

    total_matches   = stats.get("total_matches", 0)
    active_listings = stats.get("active_listings", 0)
    total_users     = stats.get("total_users", 0)
    near_expiry     = stats.get("near_expiry_count", 0)
    avg_trust       = stats.get("avg_trust_score", 10.0)

    def format_delta(val):
        clean_val = str(val).strip().lstrip('+')
        if clean_val.isdigit() and int(clean_val) >= 0:
            return f"+{clean_val}"
        return str(val)

    formatted_match_delta   = format_delta(stats.get("matches_this_week_delta", "0"))
    formatted_listing_delta = format_delta(stats.get("listings_today_delta", "0"))
    formatted_user_delta    = format_delta(stats.get("users_this_month_delta", "0"))

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card"><div class="metric-value">{total_matches:,}</div><div class="metric-label">Total Matches</div><div class="metric-delta">↑ {formatted_match_delta} this week</div></div>
        <div class="metric-card"><div class="metric-value">{active_listings:,}</div><div class="metric-label">Active Listings</div><div class="metric-delta">↑ {formatted_listing_delta} today</div></div>
        <div class="metric-card"><div class="metric-value">{total_users:,}</div><div class="metric-label">Registered Users</div><div class="metric-delta">↑ {formatted_user_delta} this month</div></div>
        <div class="metric-card"><div class="metric-value">{near_expiry}</div><div class="metric-label">Near Expiry</div><div class="metric-delta" style="color:{"#737373" if near_expiry == 0 else "#dc2626"}">{"✓ All clear" if near_expiry == 0 else "⚠ Needs attention"}</div></div>
        <div class="metric-card"><div class="metric-value">{float(avg_trust):.1f}</div><div class="metric-label">Avg Trust Score</div><div class="metric-delta">↑ Excellent</div></div>
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
            st.markdown("Monthly Matches — 2026")
            try:
                raw = db.get_monthly_matches()
            except Exception:
                raw = []
            df = _make_month_df(raw, "matches")
            st.altair_chart(_bar(df, "month", "matches", MONTH_ORDER), use_container_width=True)

        with c2:
            st.markdown("Items Listed per Month — 2026")
            try:
                raw = db.get_monthly_items()
            except Exception:
                raw = []
            df = _make_month_df(raw, "items")
            st.altair_chart(_bar(df, "month", "items", MONTH_ORDER), use_container_width=True)

    with tab_b:
        c3, c4 = st.columns(2)

        with c3:
            st.markdown("Matches by Region")
            df = pd.DataFrame({"region": region_labels, "matches": [0]*len(region_labels)})
            try:
                raw = db.get_matches_by_region()
                if raw:
                    db_df = pd.DataFrame(raw)
                    y_col = [col for col in db_df.columns if col != "region"][0]
                    for _, row in db_df.iterrows():
                        r = str(row["region"])
                        if r in region_labels:
                            df.loc[df["region"] == r, "matches"] = row[y_col]
            except Exception:
                pass
            st.altair_chart(_bar(df, "region", "matches", region_labels), use_container_width=True)

        with c4:
            st.markdown("Users by Region")
            df = pd.DataFrame({"region": region_labels, "users": [0]*len(region_labels)})
            try:
                raw = db.get_users_by_region()
                if raw:
                    db_df = pd.DataFrame(raw)
                    y_col = [col for col in db_df.columns if col != "region"][0]
                    for _, row in db_df.iterrows():
                        r = str(row["region"])
                        if r in region_labels:
                            df.loc[df["region"] == r, "users"] = row[y_col]
            except Exception:
                pass
            st.altair_chart(_bar(df, "region", "users", region_labels), use_container_width=True)

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