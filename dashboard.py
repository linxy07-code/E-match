# ── DASHBOARD FUNCTIONS ─────────────────────────────────────────────

def get_total_users(self):

    cursor = self.conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
    """)

    return cursor.fetchone()[0]


def get_total_items(self):

    cursor = self.conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM items
    """)

    return cursor.fetchone()[0]


def get_total_matches(self):

    cursor = self.conn.cursor()

    # Replace table name if different
    cursor.execute("""
        SELECT COUNT(*)
        FROM matches
    """)

    return cursor.fetchone()[0]


def get_near_expiry_count(self):

    cursor = self.conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM items
        WHERE expiry_date IS NOT NULL
        AND expiry_date <= DATE('now', '+7 day')
    """)

    return cursor.fetchone()[0]


def get_average_trust_score(self):

    cursor = self.conn.cursor()

    cursor.execute("""
        SELECT ROUND(AVG(trust_score), 1)
        FROM users
    """)

    result = cursor.fetchone()[0]

    return result if result else 0


def get_monthly_matches(self):

    # Demo live chart data
    data = {
        "Matches": [12, 20, 18, 25, 40, 55]
    }

    return pd.DataFrame(data)


def get_monthly_items(self):

    data = {
        "Items": [10, 22, 30, 45, 60, 72]
    }

    return pd.DataFrame(data)


def get_matches_by_region(self):

    data = {
        "Matches": [120, 95, 70, 50]
    }

    return pd.DataFrame(
        data,
        index=[
            "Selangor",
            "Kuala Lumpur",
            "Penang",
            "Johor"
        ]
    )


def get_users_by_region(self):

    data = {
        "Users": [420, 380, 210, 150]
    }

    return pd.DataFrame(
        data,
        index=[
            "Selangor",
            "Kuala Lumpur",
            "Penang",
            "Johor"
        ]
    )


def get_expiring_items(self):

    cursor = self.conn.cursor()

    cursor.execute("""
        SELECT
            item_name,
            region,
            expiry_date
        FROM items
        WHERE expiry_date IS NOT NULL
        ORDER BY expiry_date ASC
        LIMIT 10
    """)

    rows = cursor.fetchall()

    return pd.DataFrame(
        rows,
        columns=[
            "Item",
            "Region",
            "Expiry Date"
        ]
    )