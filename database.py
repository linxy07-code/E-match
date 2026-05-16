import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import streamlit as st


class EcoMatchDB:
    def __init__(self):
        self.db_url = st.secrets["DB_URL"]
        self._init_db()

    def _get_connection(self):
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)

    def _init_db(self):
        with self._get_connection() as conn:
            with conn.cursor() as cursor:

                # 1. Users
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id             SERIAL PRIMARY KEY,
                        username       TEXT NOT NULL UNIQUE,
                        password_hash  TEXT NOT NULL,
                        region         TEXT,
                        user_type      TEXT,
                        trust_score    REAL DEFAULT 10,
                        created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 2. Items
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS items (
                        id            SERIAL PRIMARY KEY,
                        user_id       INTEGER NOT NULL REFERENCES users(id),
                        item_name     TEXT NOT NULL,
                        category      TEXT,
                        region        TEXT,
                        condition     TEXT DEFAULT 'Good',
                        quantity      INTEGER DEFAULT 1,
                        description   TEXT,
                        expiry_date   TEXT,
                        image_path    TEXT,
                        listing_type  TEXT DEFAULT 'free',
                        price         NUMERIC(10, 2),
                        is_active     INTEGER DEFAULT 1,
                        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Migrate old items table: add listing_type / price if missing
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

                # 3. Claims
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

                # Migrate old claims table: add message if missing
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'claims' AND column_name = 'message'
                """)
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE claims ADD COLUMN message TEXT")

                # 4. Notifications  ← NEW
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

                conn.commit()

    # ── USER METHODS ──────────────────────────────────────────────────────────

    def add_user(self, username, password, region, user_type):
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """INSERT INTO users (username, password_hash, region, user_type)
                           VALUES (%s, %s, %s, %s) RETURNING id""",
                        (username, password_hash, region, user_type),
                    )
                    user_id = cursor.fetchone()["id"]
                    conn.commit()
                    return {"success": True, "user_id": user_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def verify_user(self, username, password):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """SELECT id, password_hash, user_type, region, trust_score
                           FROM users WHERE username = %s""",
                        (username,),
                    )
                    row = cursor.fetchone()
                    if row and bcrypt.checkpw(
                        password.encode("utf-8"),
                        row["password_hash"].encode("utf-8"),
                    ):
                        return {
                            "success":     True,
                            "user_id":     row["id"],
                            "user_type":   row["user_type"],
                            "region":      row["region"],
                            "trust_score": row["trust_score"],
                        }
                    return {"success": False, "error": "Invalid credentials"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_by_id(self, user_id):
        """Used by cookie auto-login in app.py."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, username, region, user_type, trust_score FROM users WHERE id = %s",
                        (int(user_id),),
                    )
                    row = cursor.fetchone()
                    return dict(row) if row else None
        except Exception:
            return None

    # ── ITEM METHODS ──────────────────────────────────────────────────────────

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
        """
        Returns ALL columns from items plus seller username and trust score.
        Explicitly lists every column so nothing is missed.
        """
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
        """
        Returns ALL columns for the logged-in user's own listings.
        """
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

    # ── CLAIM METHODS ─────────────────────────────────────────────────────────

    def add_claim(self, item_id, claimer_id, message=""):
        """
        Insert a claim and automatically send a notification to the item owner.
        Prevents duplicate pending claims from the same buyer.
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:

                    # Block duplicate pending claims
                    cursor.execute("""
                        SELECT id FROM claims
                        WHERE item_id = %s AND claimer_id = %s AND status = 'pending'
                    """, (item_id, claimer_id))
                    if cursor.fetchone():
                        return {"success": False, "error": "duplicate"}

                    # Insert claim
                    cursor.execute("""
                        INSERT INTO claims (item_id, claimer_id, message)
                        VALUES (%s, %s, %s) RETURNING id
                    """, (item_id, claimer_id, message))
                    claim_id = cursor.fetchone()["id"]

                    # Fetch item + claimer details for the notification
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
                        title = (
                            f"New {action} request on '{info['item_name']}'"
                        )
                        body = (
                            f"👤 {info['claimer_name']} wants to {action} "
                            f"your item '{info['item_name']}'."
                        )
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

    # ── TRUST & STATS ─────────────────────────────────────────────────────────

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
                    cursor.execute("SELECT COUNT(*) FROM users")
                    stats["total_users"] = cursor.fetchone()["count"]
                    cursor.execute("SELECT COUNT(*) FROM items WHERE is_active = 1")
                    stats["active_listings"] = cursor.fetchone()["count"]
                    cursor.execute("SELECT AVG(trust_score) FROM users")
                    stats["avg_trust_score"] = round(
                        float(cursor.fetchone()["avg"] or 0), 1
                    )
                    return {"success": True, **stats}
        except Exception as e:
            return {"success": False, "error": str(e)}