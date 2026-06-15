import streamlit as st
import pandas as pd


def _query_rows(db, sql, params=None):
    try:
        with db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params or ())
                return [dict(row) for row in cursor.fetchall()]
    except Exception:
        return []


def _call_or_query(db, method_name, sql, params=None):
    try:
        method = getattr(db, method_name, None)
        if method:
            rows = method()
            if rows:
                return rows
    except Exception:
        pass

    return _query_rows(db, sql, params)


def _get_company_stats(db, user_id):
    rows = _query_rows(db, """
        SELECT
            COUNT(*) FILTER (
                WHERE ci.user_id = %s AND ci.is_active = 1
            ) AS total_listings,
            COUNT(*) FILTER (
                WHERE ci.user_id = %s
                  AND ci.is_active = 1
                  AND ci.expiry_date IS NOT NULL
                  AND ci.expiry_date <> ''
                  AND TO_DATE(ci.expiry_date, 'YYYY-MM-DD')
                      BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '14 days'
            ) AS near_expiry,
            COUNT(*) FILTER (
                WHERE ci.user_id = %s
                  AND ci.is_active = 1
                  AND ci.created_at >= CURRENT_DATE
            ) AS listings_delta
        FROM company_items ci
    """, (user_id, user_id, user_id))

    stats = dict(rows[0]) if rows else {}

    tx_rows = _query_rows(db, """
        SELECT COUNT(*) AS completed_sales,
               COALESCE(SUM(price), 0) AS total_revenue,
               COUNT(*) FILTER (
                   WHERE completed_at >= DATE_TRUNC('month', CURRENT_DATE)
               ) AS sales_delta
        FROM past_transactions
        WHERE seller_id::text = %s
          AND source_table = 'company_items'
    """, (str(user_id),))

    if tx_rows:
        stats.update(tx_rows[0])

    return stats


def render_company_dashboard(db, user_id):

    # ─────────────────────────────────────────────
    # 🔵 ONLY CHANGE: BLUE HEADER (same structure)
    # ─────────────────────────────────────────────
    st.markdown("""
    <div style="background:#1d4ed8; padding:16px; border-radius:12px; color:white;">
        <h1>📊 Analytics Dashboard</h1>
        <p>Company performance and regional activity overview</p>
    </div>
    """, unsafe_allow_html=True)

    # ── 2. SPACING BEFORE GRAPHS
    st.markdown("<div style='height:25px'></div>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # 1. FETCH COMPANY STATS (same logic style)
    # ─────────────────────────────────────────────
    stats = _get_company_stats(db, user_id)

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

    # ─────────────────────────────────────────────
    # METRICS (SAME STRUCTURE AS YOUR PLATFORM)
    # ─────────────────────────────────────────────
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card"><div class="metric-value">{total_listings}</div><div class="metric-label">Active Listings</div><div class="metric-delta">↑ {fmt(listing_delta)} change</div></div>
        <div class="metric-card"><div class="metric-value">{near_expiry}</div><div class="metric-label">Near Expiry</div><div class="metric-delta">{"✓ All clear" if near_expiry == 0 else "⚠ Needs attention"}</div></div>
        <div class="metric-card"><div class="metric-value">{completed_sales}</div><div class="metric-label">Completed Sales</div><div class="metric-delta">↑ {fmt(sales_delta)} this period</div></div>
        <div class="metric-card"><div class="metric-value">RM {float(total_revenue):,.2f}</div><div class="metric-label">Total Revenue</div><div class="metric-delta">Revenue tracked</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # 2. TABS (UNCHANGED STRUCTURE)
    # ─────────────────────────────────────────────
    tab_a, tab_b = st.tabs(["📈  Monthly Trends", "🗺️  Regional Breakdown"])

    months_labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    region_labels = ["Selangor","Kuala Lumpur","Penang","Johor","Melaka","Sabah","Sarawak"]

    # ─────────────────────────────────────────────
    # MONTHLY TRENDS
    # ─────────────────────────────────────────────
    with tab_a:
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("Monthly Company Listings")

            try:
                raw = _call_or_query(db, "get_company_monthly_listings", """
                    SELECT TO_CHAR(created_at, 'Mon') AS month,
                           COUNT(*) AS listings
                    FROM company_items
                    GROUP BY month
                    ORDER BY MIN(created_at)
                """)
                df = pd.DataFrame({"month": months_labels, "value": [0]*12})

                if raw:
                    db_df = pd.DataFrame(raw)
                    y_col = [col for col in db_df.columns if col != "month"][0]

                    for _, row in db_df.iterrows():
                        month = str(row["month"]).strip()
                        if month in months_labels:
                            df.loc[df["month"] == month, "value"] = row[y_col]

            except Exception:
                df = pd.DataFrame({"month": months_labels, "value": [0]*12})

            st.bar_chart(df, x="month", y="value", height=260, color="#1f77b4")

        with c2:
            st.markdown("Monthly Sales")

            try:
                raw = _call_or_query(db, "get_company_monthly_sales", """
                    SELECT TO_CHAR(completed_at, 'Mon') AS month,
                           COUNT(*) AS sales
                    FROM past_transactions
                    WHERE source_table = 'company_items'
                    GROUP BY month
                    ORDER BY MIN(completed_at)
                """)
                df = pd.DataFrame({"month": months_labels, "value": [0]*12})

                if raw:
                    db_df = pd.DataFrame(raw)
                    y_col = [col for col in db_df.columns if col != "month"][0]

                    for _, row in db_df.iterrows():
                        month = str(row["month"]).strip()
                        if month in months_labels:
                            df.loc[df["month"] == month, "value"] = row[y_col]

            except Exception:
                df = pd.DataFrame({"month": months_labels, "value": [0]*12})

            st.bar_chart(df, x="month", y="value", height=260, color="#1f77b4")

    # ─────────────────────────────────────────────
    # REGIONAL BREAKDOWN
    # ─────────────────────────────────────────────
    with tab_b:
        c3, c4 = st.columns(2)

        with c3:
            st.markdown("Sales by Region")

            try:
                raw = _call_or_query(db, "get_company_sales_by_region", """
                    SELECT COALESCE(ci.region, u.region, 'Unknown') AS region,
                           COUNT(*) AS sales
                    FROM past_transactions pt
                    LEFT JOIN company_items ci ON ci.id = pt.item_id
                    LEFT JOIN users u ON u.id::text = pt.seller_id::text
                    WHERE pt.source_table = 'company_items'
                    GROUP BY COALESCE(ci.region, u.region, 'Unknown')
                    ORDER BY sales DESC
                """)
                df = pd.DataFrame({"region": region_labels, "value": [0]*len(region_labels)})

                if raw:
                    db_df = pd.DataFrame(raw)
                    y_col = [col for col in db_df.columns if col != "region"][0]

                    for _, row in db_df.iterrows():
                        region = str(row["region"]).strip()
                        if region in region_labels:
                            df.loc[df["region"] == region, "value"] = row[y_col]

            except Exception:
                df = pd.DataFrame({"region": region_labels, "value": [0]*len(region_labels)})

            st.bar_chart(df, x="region", y="value", height=260, color="#1f77b4")

        with c4:
            st.markdown("Users by Region")

            try:
                raw = _call_or_query(db, "get_company_users_by_region", """
                    SELECT region, COUNT(*) AS users
                    FROM users
                    WHERE user_type = 'Company'
                    GROUP BY region
                    ORDER BY users DESC
                """)
                df = pd.DataFrame({"region": region_labels, "value": [0]*len(region_labels)})

                if raw:
                    db_df = pd.DataFrame(raw)
                    y_col = [col for col in db_df.columns if col != "region"][0]

                    for _, row in db_df.iterrows():
                        region = str(row["region"]).strip()
                        if region in region_labels:
                            df.loc[df["region"] == region, "value"] = row[y_col]

            except Exception:
                df = pd.DataFrame({"region": region_labels, "value": [0]*len(region_labels)})

            st.bar_chart(df, x="region", y="value", height=260, color="#1f77b4")

    # ─────────────────────────────────────────────
    # 3. EXPIRY TABLE
    # ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ⏳ Items Approaching Expiry")

    try:
        data = _call_or_query(db, "get_company_expiring_items", """
            SELECT ci.item_name, ci.category, ci.region, ci.expiry_date,
                   COALESCE(u.company_name, u.username) AS company
            FROM company_items ci
            JOIN users u ON ci.user_id = u.id
            WHERE ci.is_active = 1
              AND ci.expiry_date IS NOT NULL
              AND ci.expiry_date <> ''
            ORDER BY TO_DATE(ci.expiry_date, 'YYYY-MM-DD') ASC
            LIMIT 10
        """)

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
