import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import streamlit as st
import datetime

class EcoMatchDB:
    def __init__(self):
        # Initializes database configuration using Streamlit secrets
        self.db_url = st.secrets["database"]["connection_string"]
        self._init_db()

    def _get_connection(self):
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)

    def _init_db(self):
        with self._get_connection() as conn:
            with conn.cursor() as cursor:

                # 1. Users Table Structure
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id             SERIAL PRIMARY KEY,
                        username       TEXT NOT NULL UNIQUE,
                        password_hash  TEXT NOT NULL,
                        region         TEXT,
                        user_type      TEXT,
                        trust_score    REAL DEFAULT 10,
                        status         TEXT DEFAULT 'Active',
                        created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Automated Schema Migration for older User variants
                for col, definition in [
                    ("email", "TEXT"),
                    ("is_verified", "BOOLEAN DEFAULT FALSE"),
                    ("status", "TEXT DEFAULT 'Active'"),
                ]:
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name = 'users' AND column_name = %s
                    """, (col,))
                    if not cursor.fetchone():
                        cursor.execute(
                            f"ALTER TABLE users ADD COLUMN {col} {definition}"
                        )

                # Email Verification Tracking Matrix
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS email_verification (
                        user_id     INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                        otp_code    TEXT NOT NULL,
                        expires_at  TIMESTAMP NOT NULL
                    )
                """)

                # 2. Marketplace Items Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS items (
                        id             SERIAL PRIMARY KEY,
                        user_id        INTEGER NOT NULL REFERENCES users(id),
                        item_name      TEXT NOT NULL,
                        category       TEXT,
                        region         TEXT,
                        condition      TEXT DEFAULT 'Good',
                        quantity       INTEGER DEFAULT 1,
                        description    TEXT,
                        expiry_date    TEXT,
                        image_path     TEXT,
                        listing_type   TEXT DEFAULT 'free',
                        price          NUMERIC(10, 2),
                        is_active      INTEGER DEFAULT 1,
                        created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Automated Schema Migration for older Item variants
                for col, definition in [
                    ("listing_type", "TEXT DEFAULT 'free'"),
                    ("price",        "NUMERIC(10, 2)"),
                ]:
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name = 'items' AND column_name = %s
                    """, (col,))
                    if not cursor.fetchone():
                        cursor.execute(
                            f"ALTER TABLE items ADD COLUMN {col} {definition}"
                        )

                # 3. Transaction Claims Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS claims (
                        id          SERIAL PRIMARY KEY,
                        item_id     INTEGER NOT NULL REFERENCES items(id),
                        claimer_id  INTEGER NOT NULL REFERENCES users(id),
                        status      TEXT DEFAULT 'pending',
                        message     TEXT,
                        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Automated Schema Migration for old claims matrix
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'claims' AND column_name = 'message'
                """)
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE claims ADD COLUMN message TEXT")

                # 4. User System Notifications Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notifications (
                        id          SERIAL PRIMARY KEY,
                        user_id     INTEGER NOT NULL REFERENCES users(id),
                        title       TEXT NOT NULL,
                        body        TEXT NOT NULL,
                        is_read     BOOLEAN DEFAULT FALSE,
                        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 5. Misconduct Engine Reports Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reports (
                        id           SERIAL PRIMARY KEY,
                        reporter_id  INTEGER NOT NULL REFERENCES users(id),
                        reported_id  INTEGER NOT NULL REFERENCES users(id),
                        reason       TEXT NOT NULL,
                        details      TEXT,
                        is_reviewed  INTEGER DEFAULT 0,
                        trust_score  REAL DEFAULT 10.0,
                        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Automated Migration marking trust score evaluations
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'reports' AND column_name = 'trust_score'
                """)
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE reports ADD COLUMN trust_score REAL DEFAULT 10.0")

                conn.commit()

    # ── USER IDENTITY MANAGEMENT METHODS ───────────────────────────────────────

    def add_user(self, username, password, region, user_type, email):
        """Creates a new user record setting verification state to pending."""
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """INSERT INTO users (username, password_hash, region, user_type, email, is_verified, status)
                           VALUES (%s, %s, %s, %s, %s, FALSE, 'Active') RETURNING id""",
                        (username, password_hash, region, user_type, email.strip()),
                    )
                    user_id = cursor.fetchone()["id"]
                    conn.commit()
                    return {"success": True, "user_id": user_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def verify_user(self, username, password):
        """Validates login credentials, ensures verification passed, and fetches system parameters."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """SELECT id, password_hash, user_type, region, trust_score, status, is_verified
                           FROM users WHERE username = %s""",
                        (username,),
                    )
                    row = cursor.fetchone()
                    if row and bcrypt.checkpw(
                        password.encode("utf-8"),
                        row["password_hash"].encode("utf-8"),
                    ):
                        # Block access if account email verification is incomplete
                        if not row["is_verified"]:
                            return {"success": False, "error": "unverified", "user_id": row["id"]}
                        
                        return {
                            "success":     True,
                            "user_id":     row["id"],
                            "user_type":   row["user_type"],
                            "region":      row["region"],
                            "trust_score": row["trust_score"],
                            "status":      row["status"],
                        }
                    return {"success": False, "error": "Invalid credentials"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_by_id(self, user_id):
        """Used by safety engines and cookie auto-login parameters to pull live system metrics."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, username, region, user_type, trust_score, status, is_verified FROM users WHERE id = %s",
                        (int(user_id),),
                    )
                    row = cursor.fetchone()
                    return dict(row) if row else None
        except Exception:
            return None

    def get_user_by_username(self, username):
        """Fetches profile mapping parameters using a unique text string handle."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, username, region, user_type, trust_score, status FROM users WHERE username = %s",
                        (username.strip(),),
                    )
                    row = cursor.fetchone()
                    return dict(row) if row else None
        except Exception:
            return None

    # ── EMAIL VERIFICATION ENGINE METHODS ────────────────────────────────────

    def save_verification_code(self, user_id, otp_code, expiry_minutes=15):
        """Saves or updates a rolling verification code tied to a user account profile."""
        expires_at = datetime.datetime.now() + datetime.timedelta(minutes=expiry_minutes)
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # PostgreSQL UPSERT handling duplicate registration attempts cleanly
                    cursor.execute("""
                        INSERT INTO email_verification (user_id, otp_code, expires_at)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (user_id) 
                        DO UPDATE SET otp_code = EXCLUDED.otp_code, expires_at = EXCLUDED.expires_at
                    """, (user_id, otp_code, expires_at))
                    conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_verification_code(self, user_id, user_entered_code):
        """Validates temporary verification credentials and elevates user profile registration parameters."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT otp_code, expires_at FROM email_verification WHERE user_id = %s
                    """, (user_id,))
                    row = cursor.fetchone()
                    
                    if not row:
                        return {"success": False, "error": "No validation session found for this profile."}
                    
                    if row["otp_code"] != user_entered_code.strip():
                        return {"success": False, "error": "Invalid verification token."}
                        
                    if datetime.datetime.now() > row["expires_at"]:
                        return {"success": False, "error": "Code timeout expired. Please request a new token."}
                    
                    # Core Atomic Status Escalation Workflow
                    cursor.execute("UPDATE users SET is_verified = TRUE WHERE id = %s", (user_id,))
                    cursor.execute("DELETE FROM email_verification WHERE user_id = %s", (user_id,))
                    conn.commit()
                    
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── MARKETPLACE PRODUCT METRICS METHODS ───────────────────────────────────

    def add_item(
        self,
        user_id,
        item_name,
        category,
        region,
        expiry_date=None,
        image_path=None,
        condition="Good",
        quantity=1,
        description="",
        listing_type="free",
        price=None,
    ):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO items
                            (user_id, item_name, category, region, condition, quantity,
                             description, expiry_date, image_path, listing_type, price)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        user_id, item_name, category, region, condition, quantity,
                        description, expiry_date, image_path, listing_type,
                        float(price) if price is not None else None,
                    ))
                    conn.commit()
                    return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_all_items(self, category=None, search=None):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                        SELECT
                            i.id            AS item_id,
                            i.user_id,
                            i.item_name,
                            i.category,
                            i.region,
                            i.condition,
                            i.quantity,
                            i.description,
                            i.expiry_date,
                            i.image_path,
                            i.listing_type,
                            i.price,
                            i.is_active,
                            i.created_at,
                            u.username      AS seller_name,
                            u.trust_score   AS seller_trust
                        FROM items i
                        JOIN users u ON i.user_id = u.id
                        WHERE i.is_active = 1
                    """
                    params = []
                    if category:
                        query += " AND i.category = %s"
                        params.append(category)
                    if search:
                        query += " AND i.item_name ILIKE %s"
                        params.append(f"%{search}%")
                    query += " ORDER BY i.id DESC"
                    cursor.execute(query, params)
                    return {"success": True, "items": cursor.fetchall()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_items(self, user_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT
                            id          AS item_id,
                            item_name,
                            category,
                            region,
                            condition,
                            quantity,
                            description,
                            expiry_date,
                            image_path,
                            listing_type,
                            price,
                            created_at
                        FROM items
                        WHERE user_id = %s AND is_active = 1
                        ORDER BY id DESC
                    """, (user_id,))
                    return {"success": True, "items": cursor.fetchall()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_item(self, item_id, user_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT user_id FROM items WHERE id = %s", (item_id,)
                    )
                    row = cursor.fetchone()
                    if not row or row["user_id"] != user_id:
                        return {"success": False, "error": "Unauthorized"}
                    cursor.execute("DELETE FROM items WHERE id = %s", (item_id,))
                    conn.commit()
                    return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── TRANSACTION CLAIM MATRICES METHODS ────────────────────────────────────

    def add_claim(self, item_id, claimer_id, message=""):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:

                    # Block duplicate active pending claims
                    cursor.execute("""
                        SELECT id FROM claims
                        WHERE item_id = %s AND claimer_id = %s AND status = 'pending'
                    """, (item_id, claimer_id))
                    if cursor.fetchone():
                        return {"success": False, "error": "duplicate"}

                    # Save system claim record
                    cursor.execute("""
                        INSERT INTO claims (item_id, claimer_id, message)
                        VALUES (%s, %s, %s) RETURNING id
                    """, (item_id, claimer_id, message))
                    claim_id = cursor.fetchone()["id"]

                    # Fetch product details alongside applicant information context
                    cursor.execute("""
                        SELECT
                            i.item_name,
                            i.listing_type,
                            i.price,
                            i.user_id   AS owner_id,
                            u.username  AS claimer_name
                        FROM items i
                        JOIN users u ON u.id = %s
                        WHERE i.id = %s
                    """, (claimer_id, item_id))
                    info = cursor.fetchone()

                    if info:
                        lt = info["listing_type"] or "free"
                        action = (
                            "buy"      if lt == "sell"     else
                            "exchange" if lt == "exchange" else
                            "claim"
                        )
                        title = f"New {action} request on '{info['item_name']}'"
                        body = f"👤 {info['claimer_name']} wants to {action} your item '{info['item_name']}'."
                        if message:
                            body += f'\n💬 "{message}"'

                        cursor.execute("""
                            INSERT INTO notifications (user_id, title, body)
                            VALUES (%s, %s, %s)
                        """, (info["owner_id"], title, body))

                    conn.commit()
                    return {"success": True, "claim_id": claim_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_claims_for_item(self, item_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT c.*, u.username AS claimer_name
                        FROM claims c
                        JOIN users u ON c.claimer_id = u.id
                        WHERE c.item_id = %s
                        ORDER BY c.created_at DESC
                    """, (item_id,))
                    return {"success": True, "claims": cursor.fetchall()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_claim_status(self, claim_id, status):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE claims SET status = %s WHERE id = %s",
                        (status, claim_id)
                    )
                    conn.commit()
                    return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── NOTIFICATION METHODS ──────────────────────────────────────────────────

    def get_notifications(self, user_id, unread_only=False):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    query = (
                        "SELECT * FROM notifications WHERE user_id = %s"
                        + (" AND is_read = FALSE" if unread_only else "")
                        + " ORDER BY created_at DESC LIMIT 50"
                    )
                    cursor.execute(query, (user_id,))
                    return {"success": True, "notifications": cursor.fetchall()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def mark_notifications_read(self, user_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE notifications SET is_read = TRUE WHERE user_id = %s",
                        (user_id,),
                    )
                    conn.commit()
                    return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def count_unread_notifications(self, user_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """SELECT COUNT(*) FROM notifications
                           WHERE user_id = %s AND is_read = FALSE""",
                        (user_id,),
                    )
                    return int(cursor.fetchone()["count"])
        except Exception:
            return 0

    # ── TRUST MATRIX & ANALYTICS METHODS ──────────────────────────────────────

    def update_trust_score(self, user_id, delta):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE users
                        SET trust_score = LEAST(10, GREATEST(0, trust_score + %s))
                        WHERE id = %s RETURNING trust_score
                    """, (delta, user_id))
                    row = cursor.fetchone()
                    conn.commit()
                    return {"success": True, "new_score": row["trust_score"]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_platform_stats(self):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    stats = {}
                    
                    # 1. Total Users
                    cursor.execute("SELECT COUNT(*) FROM users")
                    stats["total_users"] = cursor.fetchone()["count"] or 0
                    
                    # 2. Active Listings
                    cursor.execute("SELECT COUNT(*) FROM items WHERE is_active = 1")
                    stats["active_listings"] = cursor.fetchone()["count"] or 0
                    
                    # 3. Average Trust Score
                    cursor.execute("SELECT AVG(trust_score) FROM users")
                    stats["avg_trust_score"] = round(float(cursor.fetchone()["avg"] or 0), 1)
                    
                    # 4. Total Matches (Total historical entries inside claims matrix)
                    cursor.execute("SELECT COUNT(*) FROM claims")
                    stats["total_matches"] = cursor.fetchone()["count"] or 0
                    
                    # 5. Near Expiry Count (Items expiring within the next rolling 7 days)
                    cursor.execute("""
                        SELECT COUNT(*) FROM items 
                        WHERE is_active = 1 
                        AND expiry_date IS NOT NULL 
                        AND expiry_date <> ''
                        AND TO_DATE(expiry_date, 'YYYY-MM-DD') <= CURRENT_DATE + INTERVAL '7 days'
                        AND TO_DATE(expiry_date, 'YYYY-MM-DD') >= CURRENT_DATE
                    """)
                    stats["near_expiry_count"] = cursor.fetchone()["count"] or 0

                    # 6. Deltas: Items added today
                    cursor.execute("""
                        SELECT COUNT(*) FROM items 
                        WHERE created_at >= CURRENT_DATE
                    """)
                    stats["listings_today_delta"] = cursor.fetchone()["count"] or 0

                    # 7. Deltas: Matches requested this rolling week (Last 7 Days)
                    cursor.execute("""
                        SELECT COUNT(*) FROM claims 
                        WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                    """)
                    stats["matches_this_week_delta"] = cursor.fetchone()["count"] or 0

                    # 8. Deltas: Registered accounts created this calendar month
                    cursor.execute("""
                        SELECT COUNT(*) FROM users 
                        WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
                    """)
                    stats["users_this_month_delta"] = cursor.fetchone()["count"] or 0

                    return stats
        except Exception:
            return {
                "total_users": 0, "active_listings": 0, "avg_trust_score": 10.0,
                "total_matches": 0, "near_expiry_count": 0,
                "listings_today_delta": 0, "matches_this_week_delta": 0, "users_this_month_delta": 0
            }

    # ── MISCONDUCT LOGGING METHOD ─────────────────────────────────────────────

    def create_misconduct_report(self, report_payload):
        """Inserts user misconduct report payloads straight into PostgreSQL 'reports' table."""
        try:
            reported_user = self.get_user_by_username(report_payload["reported_username"])
            if not reported_user:
                return {"success": False, "error": f"User '{report_payload['reported_username']}' does not exist."}
                
            reported_id = reported_user["id"]
            reported_trust = float(reported_user.get("trust_score", 10.0))

            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO reports (reporter_id, reported_id, reason, details, is_reviewed, trust_score, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        report_payload["reporter_id"],
                        reported_id,
                        report_payload["reason"],
                        report_payload["details"],
                        0,  # Default unreviewed snapshot parameter
                        reported_trust,
                        report_payload["created_at"]
                    ))
                    conn.commit()
                    return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        
     # ── DASHBOARD ANALYTICS METHODS ───────────────────────────────

    def get_monthly_matches(self):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT
                            TO_CHAR(created_at, 'YYYY-MM') AS month,
                            COUNT(*) AS matches
                        FROM claims
                        GROUP BY month
                        ORDER BY month
                    """)
                    return cursor.fetchall()
        except Exception:
            return []

    def get_monthly_items(self):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT
                            TO_CHAR(created_at, 'YYYY-MM') AS month,
                            COUNT(*) AS items
                        FROM items
                        GROUP BY month
                        ORDER BY month
                    """)
                    return cursor.fetchall()
        except Exception:
            return []

    def get_matches_by_region(self):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT
                            region,
                            COUNT(*) AS matches
                        FROM items
                        GROUP BY region
                        ORDER BY matches DESC
                    """)
                    return cursor.fetchall()
        except Exception:
            return []

    def get_users_by_region(self):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT
                            region,
                            COUNT(*) AS users
                        FROM users
                        GROUP BY region
                        ORDER BY users DESC
                    """)
                    return cursor.fetchall()
        except Exception:
            return []      

    def get_expiring_items(self):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT
                            item_name,
                            category,
                            region,
                            expiry_date
                        FROM items
                        WHERE expiry_date IS NOT NULL
                        ORDER BY expiry_date ASC
                        LIMIT 10
                    """)
                    return cursor.fetchall()
        except Exception:
            return []