# database.py
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import streamlit as st
import datetime

class EcoMatchDB:
    def __init__(self):
        self.db_url = st.secrets["database"]["connection_string"]
        self._init_db()

    def _get_connection(self):
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)

    def _init_db(self):
        with self._get_connection() as conn:
            with conn.cursor() as cursor:

                # ── 1. USERS TABLE ────────────────────────────────────────────
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id            SERIAL PRIMARY KEY,
                        username      TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        region        TEXT,
                        user_type     TEXT DEFAULT 'Personal',
                        email         TEXT,
                        is_verified   BOOLEAN DEFAULT FALSE,
                        trust_score   REAL DEFAULT 10.0,
                        status        TEXT DEFAULT 'Active',
                        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                for col, definition in [
                    ("phone_number",    "TEXT"),
                    ("company_name",    "TEXT"),
                    ("supervisor_name", "TEXT"),
                    ("address",         "TEXT"),
                ]:
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name = 'users' AND column_name = %s
                    """, (col,))
                    if not cursor.fetchone():
                        cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")

                # ── 2. PERSONAL ITEMS TABLE ───────────────────────────────────
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
                        phone_number   TEXT,
                        is_active      INTEGER DEFAULT 1,
                        reserved_by    INTEGER REFERENCES users(id),
                        buyer_id       INTEGER REFERENCES users(id),
                        seller_shipped BOOLEAN DEFAULT FALSE,
                        buyer_received BOOLEAN DEFAULT FALSE,
                        status         TEXT DEFAULT 'active',
                        created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                for col, definition in [
                    ("reserved_by",    "INTEGER REFERENCES users(id)"),
                    ("buyer_id",       "INTEGER REFERENCES users(id)"),
                    ("seller_shipped", "BOOLEAN DEFAULT FALSE"),
                    ("buyer_received", "BOOLEAN DEFAULT FALSE"),
                    ("status",         "TEXT DEFAULT 'active'"),
                    ("listing_type",   "TEXT DEFAULT 'free'"),
                    ("price",          "NUMERIC(10, 2)"),
                    ("phone_number",   "TEXT"),
                    ("quantity",       "INTEGER DEFAULT 1"),
                    ("exchange_offer", "TEXT"),
                    ("exchange_want",  "TEXT"),
                ]:
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name = 'items' AND column_name = %s
                    """, (col,))
                    if not cursor.fetchone():
                        cursor.execute(f"ALTER TABLE items ADD COLUMN {col} {definition}")

                # ── 3. COMPANY INVENTORY TABLE (separate, never mixed with personal items) ──
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS company_items (
                        id             SERIAL PRIMARY KEY,
                        user_id        INTEGER NOT NULL REFERENCES users(id),
                        item_name      TEXT NOT NULL,
                        category       TEXT,
                        region         TEXT,
                        stock_name     TEXT,
                        quantity       INTEGER DEFAULT 1,
                        description    TEXT,
                        expiry_date    TEXT,
                        image_path     TEXT,
                        listing_type   TEXT DEFAULT 'sell',
                        price          NUMERIC(10, 2),
                        phone_number   TEXT,
                        exchange_offer TEXT,
                        exchange_want  TEXT,
                        is_active      INTEGER DEFAULT 1,
                        reserved_by    INTEGER REFERENCES users(id),
                        buyer_id       INTEGER REFERENCES users(id),
                        seller_shipped BOOLEAN DEFAULT FALSE,
                        buyer_received BOOLEAN DEFAULT FALSE,
                        status         TEXT DEFAULT 'active',
                        alert_sent     BOOLEAN DEFAULT FALSE,
                        created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                for col, definition in [
                    ("exchange_offer", "TEXT"),
                    ("exchange_want",  "TEXT"),
                    ("phone_number",   "TEXT"),
                    ("stock_name",     "TEXT"),
                    ("alert_sent",     "BOOLEAN DEFAULT FALSE"),
                    ("buyer_id",       "INTEGER REFERENCES users(id)"),
                    ("seller_shipped", "BOOLEAN DEFAULT FALSE"),
                    ("buyer_received", "BOOLEAN DEFAULT FALSE"),
                ]:
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name = 'company_items' AND column_name = %s
                    """, (col,))
                    if not cursor.fetchone():
                        cursor.execute(f"ALTER TABLE company_items ADD COLUMN {col} {definition}")

                # ── 4. EMAIL VERIFICATION TABLE ───────────────────────────────
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS email_verification (
                        user_id    INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                        otp_code   TEXT NOT NULL,
                        expires_at TIMESTAMP NOT NULL
                    )
                """)

                # ── 5. CLAIMS TABLE ───────────────────────────────────────────
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS claims (
                        id         SERIAL PRIMARY KEY,
                        item_id    INTEGER NOT NULL REFERENCES items(id),
                        claimer_id INTEGER NOT NULL REFERENCES users(id),
                        status     TEXT DEFAULT 'pending',
                        message    TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'claims' AND column_name = 'message'
                """)
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE claims ADD COLUMN message TEXT")

                # ── 6. NOTIFICATIONS TABLE ────────────────────────────────────
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notifications (
                        id         SERIAL PRIMARY KEY,
                        user_id    INTEGER NOT NULL REFERENCES users(id),
                        title      TEXT NOT NULL,
                        body       TEXT NOT NULL,
                        is_read    BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # ── 7. REPORTS TABLE ──────────────────────────────────────────
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reports (
                        id          SERIAL PRIMARY KEY,
                        reporter_id INTEGER NOT NULL REFERENCES users(id),
                        reported_id INTEGER NOT NULL REFERENCES users(id),
                        reason      TEXT NOT NULL,
                        details     TEXT,
                        is_reviewed INTEGER DEFAULT 0,
                        trust_score REAL DEFAULT 10.0,
                        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'reports' AND column_name = 'trust_score'
                """)
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE reports ADD COLUMN trust_score REAL DEFAULT 10.0")

                # ── 8. PAST TRANSACTIONS TABLE ────────────────────────────────
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS past_transactions (
                        id              SERIAL PRIMARY KEY,
                        item_id         INTEGER,
                        buyer_id        INTEGER REFERENCES users(id),
                        seller_id       INTEGER REFERENCES users(id),
                        buyer_username  TEXT,
                        seller_username TEXT,
                        item_name       TEXT,
                        price           NUMERIC(10,2),
                        listing_type    TEXT,
                        source_table    TEXT DEFAULT 'items',
                        completed_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                for col, definition in [
                    ("source_table",    "TEXT DEFAULT 'items'"),
                    ("buyer_username",  "TEXT"),
                    ("seller_username", "TEXT"),
                ]:
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name = 'past_transactions' AND column_name = %s
                    """, (col,))
                    if not cursor.fetchone():
                        cursor.execute(f"ALTER TABLE past_transactions ADD COLUMN {col} {definition}")

                # Index common read paths so page loads and filters avoid table scans.
                for index_sql in [
                    "CREATE INDEX IF NOT EXISTS idx_items_marketplace ON items (is_active, reserved_by, user_id, id DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_items_filters ON items (region, listing_type, condition)",
                    "CREATE INDEX IF NOT EXISTS idx_company_items_marketplace ON company_items (is_active, reserved_by, user_id, id DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_company_items_filters ON company_items (region, listing_type, category)",
                    "CREATE INDEX IF NOT EXISTS idx_notifications_user_read_created ON notifications (user_id, is_read, created_at DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_past_transactions_buyer ON past_transactions (buyer_id, completed_at DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_past_transactions_seller ON past_transactions (seller_id, completed_at DESC)",
                ]:
                    cursor.execute(index_sql)

                conn.commit()

    # ── TRANSACTION NOTIFICATIONS HELPER ─────────────────────────────────────

    def _create_transaction_notifications(self, item):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    buyer_id  = item["buyer_id"]
                    seller_id = item["user_id"]
                    item_name = item["item_name"]

                    cursor.execute("""
                        INSERT INTO notifications (user_id, title, body)
                        VALUES (%s, %s, %s)
                    """, (
                        seller_id,
                        "⏳ Transaction Update",
                        f"Waiting for buyer to confirm transaction for '{item_name}'"
                    ))

                    cursor.execute("""
                        INSERT INTO notifications (user_id, title, body)
                        VALUES (%s, %s, %s)
                    """, (
                        buyer_id,
                        "⏳ Transaction Update",
                        f"Waiting for seller to confirm transaction for '{item_name}'"
                    ))

                    conn.commit()
        except Exception:
            pass

    # ── USER IDENTITY MANAGEMENT ──────────────────────────────────────────────

    def add_user(self, username, password, region, user_type, email,
                 phone_number=None, company_name=None, supervisor_name=None, address=None):
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """INSERT INTO users
                               (username, password_hash, region, user_type, email,
                                is_verified, status, phone_number,
                                company_name, supervisor_name, address)
                           VALUES (%s,%s,%s,%s,%s, FALSE,'Active',%s,%s,%s,%s)
                           RETURNING id""",
                        (username, password_hash, region, user_type,
                         email.strip(), phone_number,
                         company_name, supervisor_name, address),
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
                        """SELECT id, password_hash, user_type, region,
                                  trust_score, status, is_verified
                           FROM users WHERE username = %s""",
                        (username,),
                    )
                    row = cursor.fetchone()
                    if row and bcrypt.checkpw(
                        password.encode("utf-8"),
                        row["password_hash"].encode("utf-8"),
                    ):
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
                    return {"success": False, "error": "Invalid username or password. Please try again."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_by_id(self, user_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """SELECT id, username, region, user_type, trust_score,
                                  status, is_verified, phone_number,
                                  company_name, supervisor_name, address
                           FROM users WHERE id = %s""",
                        (int(user_id),),
                    )
                    row = cursor.fetchone()
                    return dict(row) if row else None
        except Exception:
            return None

    def get_user_by_username(self, username):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """SELECT id, username, region, user_type, trust_score, status
                           FROM users WHERE username = %s""",
                        (username.strip(),),
                    )
                    row = cursor.fetchone()
                    return dict(row) if row else None
        except Exception:
            return None

    # ── EMAIL VERIFICATION ────────────────────────────────────────────────────

    def save_verification_code(self, user_id, otp_code, expiry_minutes=15):
        expires_at = datetime.datetime.now() + datetime.timedelta(minutes=expiry_minutes)
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO email_verification (user_id, otp_code, expires_at)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (user_id)
                        DO UPDATE SET otp_code = EXCLUDED.otp_code,
                                      expires_at = EXCLUDED.expires_at
                    """, (user_id, otp_code, expires_at))
                    conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_verification_code(self, user_id, user_entered_code):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT otp_code, expires_at FROM email_verification
                        WHERE user_id = %s
                    """, (user_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {"success": False, "error": "No validation session found."}
                    if row["otp_code"] != user_entered_code.strip():
                        return {"success": False, "error": "Invalid verification token."}
                    if datetime.datetime.now() > row["expires_at"]:
                        return {"success": False, "error": "Code expired. Please request a new token."}
                    cursor.execute("UPDATE users SET is_verified = TRUE WHERE id = %s", (user_id,))
                    cursor.execute("DELETE FROM email_verification WHERE user_id = %s", (user_id,))
                    conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    def delete_unverified_user(self, user_id):
        """
        Permanently delete an unverified account and its OTP record.
        Called when the user cancels the OTP verification flow.
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Safety check — only delete truly unverified accounts
                    cursor.execute(
                        "SELECT is_verified FROM users WHERE id = %s", (user_id,)
                    )
                    row = cursor.fetchone()
                    if not row:
                        return {"success": False, "error": "User not found"}
                    if row["is_verified"]:
                        return {"success": False, "error": "Cannot delete a verified account"}
                    # Remove OTP record first (FK constraint)
                    cursor.execute(
                        "DELETE FROM email_verification WHERE user_id = %s", (user_id,)
                    )
                    # Remove the user
                    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                    conn.commit()
                    return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── PERSONAL MARKETPLACE ITEMS ────────────────────────────────────────────

    def add_item(self, user_id, item_name, category, region,
                 condition, quantity, expiry_date,
                 image_path, description,
                 listing_type, price, phone_number,
                 exchange_offer=None, exchange_want=None):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:

                    region = (region or "").strip().title()
                    
                    cursor.execute("""
                        INSERT INTO items
                            (user_id, item_name, category, region, condition, quantity,
                             description, expiry_date, image_path, listing_type, price,
                             phone_number, exchange_offer, exchange_want)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        user_id, item_name, category, region, condition, quantity,
                        description, expiry_date, image_path, listing_type,
                        float(price) if price is not None else None,
                        phone_number, exchange_offer, exchange_want,
                    ))
                    conn.commit()
                    return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_all_items(
        self,
        category=None,
        search=None,
        region=None,
        listing_type=None,
        condition=None,
        exclude_user_id=None,
    ):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                        SELECT
                            i.id          AS item_id,
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
                            i.phone_number,
                            i.exchange_offer,
                            i.exchange_want,
                            i.is_active,
                            i.created_at,
                            u.username    AS seller_name,
                            u.trust_score AS seller_trust
                        FROM items i
                        JOIN users u ON i.user_id = u.id
                        WHERE i.is_active = 1
                          AND i.reserved_by IS NULL
                          AND u.user_type = 'Personal'
                    """
                    params = []
                    if exclude_user_id is not None:
                        query += " AND i.user_id <> %s"
                        params.append(exclude_user_id)
                    if category:
                        query += " AND i.category = %s"
                        params.append(category)
                    if search:
                        query += " AND i.item_name ILIKE %s"
                        params.append(f"%{search}%")
                    if region:
                        if region in ("Pulau Pinang", "Penang"):
                            query += " AND i.region IN ('Pulau Pinang', 'Penang')"
                        else:
                            query += " AND i.region = %s"
                            params.append(region)
                    if listing_type:
                        query += " AND i.listing_type = %s"
                        params.append(listing_type)
                    if condition:
                        query += " AND i.condition = %s"
                        params.append(condition)
                    query += " ORDER BY i.id DESC"
                    cursor.execute(query, params)
                    return {"success": True, "items": [dict(row) for row in cursor.fetchall()]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_items(self, user_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id AS item_id, item_name, category, region,
                               condition, quantity, description, expiry_date,
                               image_path, listing_type, price, phone_number,
                               exchange_offer, exchange_want,
                               seller_shipped, buyer_received, status, created_at
                        FROM items
                        WHERE user_id = %s AND is_active = 1
                        ORDER BY id DESC
                    """, (user_id,))
                    return {"success": True, "items": [dict(row) for row in cursor.fetchall()]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def reserve_item(self, item_id, user_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT reserved_by FROM items WHERE id = %s", (item_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {"success": False, "error": "Item not found"}
                    if row["reserved_by"] is not None:
                        return {"success": False, "error": "Already reserved"}
                    cursor.execute("""
                        UPDATE items SET reserved_by = %s, buyer_id = %s WHERE id = %s
                    """, (user_id, user_id, item_id))
                    conn.commit()
                    return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_item(self, item_id, user_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT user_id FROM items WHERE id = %s", (item_id,))
                    row = cursor.fetchone()
                    if not row or row["user_id"] != user_id:
                        return {"success": False, "error": "Unauthorized"}
                    cursor.execute("DELETE FROM items WHERE id = %s", (item_id,))
                    conn.commit()
                    return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_cart_items(self, user_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT i.id AS item_id, i.item_name, i.category, i.region,
                               i.condition, i.quantity, i.description, i.image_path,
                               i.listing_type, i.price, i.phone_number,
                               i.buyer_received, i.seller_shipped, i.created_at,
                               u.username AS seller_name
                        FROM items i
                        JOIN users u ON i.user_id = u.id
                        WHERE i.reserved_by = %s
                        ORDER BY i.created_at DESC
                    """, (user_id,))
                    return {"success": True, "items": [dict(row) for row in cursor.fetchall()]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def cancel_reservation(self, item_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE items
                        SET reserved_by = NULL, buyer_id = NULL, status = 'active'
                        WHERE id = %s
                    """, (item_id,))
                    cursor.execute("""
                        DELETE FROM claims
                        WHERE item_id = %s AND status = 'pending'
                    """, (item_id,))
                    conn.commit()
                    return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def mark_item_shipped(self, item_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE items
                        SET seller_shipped = TRUE
                        WHERE id = %s
                    """, (item_id,))
                    conn.commit()
            self._check_transaction_complete(item_id)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def mark_item_received(self, item_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE items
                        SET buyer_received = TRUE
                        WHERE id = %s
                    """, (item_id,))
                    cursor.execute("""
                        SELECT user_id, item_name
                        FROM items
                        WHERE id = %s
                    """, (item_id,))
                    item = cursor.fetchone()
                    cursor.execute("""
                        INSERT INTO notifications (user_id, title, body)
                        VALUES (%s, %s, %s)
                    """, (
                        item["user_id"],
                        "📦 Buyer Confirmed Receipt",
                        f"Buyer has received '{item['item_name']}'. Please ship to complete transaction."
                    ))
                    conn.commit()
                self._check_transaction_complete(item_id)
                return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _check_transaction_complete(self, item_id, source_table="items"):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    table = "company_items" if source_table == "company_items" else "items"

                    cursor.execute(f"""
                        SELECT
                            id,
                            user_id,
                            buyer_id,
                            reserved_by,
                            seller_shipped,
                            buyer_received,
                            item_name,
                            price,
                            listing_type
                        FROM {table}
                        WHERE id = %s
                    """, (item_id,))
                    item = cursor.fetchone()

                    if not item:
                        return

                    if not (item["seller_shipped"] and item["buyer_received"]):
                        return

                    effective_buyer_id = item["buyer_id"] or item["reserved_by"]

                    cursor.execute("""
                        SELECT 1 FROM past_transactions
                        WHERE item_id = %s AND source_table = %s
                        LIMIT 1
                    """, (item_id, source_table))

                    if cursor.fetchone():
                        return

                    buyer_username = None
                    if effective_buyer_id:
                        cursor.execute("SELECT username FROM users WHERE id = %s", (effective_buyer_id,))
                        buyer_row = cursor.fetchone()
                        buyer_username = buyer_row["username"] if buyer_row else None

                    cursor.execute("SELECT username FROM users WHERE id = %s", (item["user_id"],))
                    seller_row = cursor.fetchone()
                    seller_username = seller_row["username"] if seller_row else None

                    cursor.execute("""
                        INSERT INTO past_transactions
                            (item_id, buyer_id, seller_id, buyer_username, seller_username,
                             item_name, price, listing_type, source_table, completed_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """, (
                        item_id,
                        effective_buyer_id,
                        item["user_id"],
                        buyer_username,
                        seller_username,
                        item["item_name"],
                        item["price"],
                        item["listing_type"],
                        source_table,
                    ))

                    if item["buyer_id"] is None and effective_buyer_id is not None:
                        cursor.execute(f"""
                            UPDATE {table}
                            SET buyer_id = %s
                            WHERE id = %s
                        """, (effective_buyer_id, item_id))

                    cursor.execute(f"""
                        UPDATE {table}
                        SET status = 'completed',
                            is_active = 0,
                            reserved_by = NULL
                        WHERE id = %s
                    """, (item_id,))

                    if effective_buyer_id:
                        cursor.execute("""
                            INSERT INTO notifications (user_id, title, body)
                            VALUES (%s, %s, %s)
                        """, (
                            effective_buyer_id,
                            "🎉 Transaction Completed",
                            f"Your purchase '{item['item_name']}' is completed!"
                        ))

                    cursor.execute("""
                        INSERT INTO notifications (user_id, title, body)
                        VALUES (%s, %s, %s)
                    """, (
                        item["user_id"],
                        "🎉 Transaction Completed",
                        f"Your item '{item['item_name']}' has been sold successfully!"
                    ))

                    conn.commit()

        except Exception as e:
            try:
                import traceback
                st.error("Transaction completion failed")
                st.code(traceback.format_exc())
            except Exception:
                pass

    # ── CLAIMS ────────────────────────────────────────────────────────────────

    def add_claim(self, item_id, claimer_id, message=""):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id FROM claims
                        WHERE item_id = %s AND claimer_id = %s AND status = 'pending'
                    """, (item_id, claimer_id))
                    if cursor.fetchone():
                        return {"success": False, "error": "duplicate"}
                    cursor.execute("""
                        INSERT INTO claims (item_id, claimer_id, message)
                        VALUES (%s, %s, %s) RETURNING id
                    """, (item_id, claimer_id, message))
                    claim_id = cursor.fetchone()["id"]
                    cursor.execute("""
                        SELECT i.item_name, i.listing_type, i.price,
                               i.user_id AS owner_id, u.username AS claimer_name
                        FROM items i JOIN users u ON u.id = %s
                        WHERE i.id = %s
                    """, (claimer_id, item_id))
                    info = cursor.fetchone()
                    if info:
                        lt = info["listing_type"] or "free"
                        action = ("buy" if lt == "sell" else
                                  "exchange" if lt == "exchange" else "claim")
                        title = f"New {action} request on '{info['item_name']}'"
                        body  = f"👤 {info['claimer_name']} wants to {action} your item '{info['item_name']}'."
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
                        FROM claims c JOIN users u ON c.claimer_id = u.id
                        WHERE c.item_id = %s ORDER BY c.created_at DESC
                    """, (item_id,))
                    return {"success": True, "claims": [dict(row) for row in cursor.fetchall()]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_claim_status(self, item_id, status):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE claims SET status = %s
                        WHERE item_id = %s
                    """, (status, item_id))
                    conn.commit()
                    return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── NOTIFICATIONS ─────────────────────────────────────────────────────────

    def get_notifications(self, user_id, unread_only=False):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                        SELECT id, user_id, title, body, is_read, created_at
                        FROM notifications WHERE user_id = %s
                    """
                    if unread_only:
                        query += " AND is_read = FALSE"
                    query += " ORDER BY created_at DESC LIMIT 50"
                    cursor.execute(query, (user_id,))
                    return {"success": True, "notifications": [dict(row) for row in cursor.fetchall()]}
        except Exception as e:
            return {"success": False, "error": str(e), "notifications": []}

    def get_notifications_with_unread_count(self, user_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, user_id, title, body, is_read, created_at
                        FROM notifications
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT 50
                    """, (user_id,))
                    notifications = [dict(row) for row in cursor.fetchall()]

                    cursor.execute(
                        "SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE",
                        (user_id,),
                    )
                    row = cursor.fetchone()
                    return {
                        "success": True,
                        "notifications": notifications,
                        "unread_count": int(row["count"]) if row else 0,
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "notifications": [],
                "unread_count": 0,
            }

    def mark_notifications_read(self, user_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE notifications SET is_read = TRUE WHERE user_id = %s", (user_id,)
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
                        "SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE",
                        (user_id,),
                    )
                    row = cursor.fetchone()
                    return int(row["count"]) if row else 0
        except Exception:
            return 0

    # ── TRUST SYSTEM ──────────────────────────────────────────────────────────

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

    def create_misconduct_report(self, report_payload):
        try:
            reported_user = self.get_user_by_username(report_payload["reported_username"])
            if not reported_user:
                return {"success": False, "error": f"User '{report_payload['reported_username']}' does not exist."}
            reported_id    = reported_user["id"]
            reported_trust = float(reported_user.get("trust_score", 10.0))
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO reports
                            (reporter_id, reported_id, reason, details,
                             is_reviewed, trust_score, created_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        report_payload["reporter_id"], reported_id,
                        report_payload["reason"], report_payload["details"],
                        0, reported_trust, report_payload["created_at"]
                    ))
                    conn.commit()
                    return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── DASHBOARD ANALYTICS ───────────────────────────────────────────────────

    def get_platform_stats(self):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    stats = {}
                    cursor.execute("SELECT COUNT(*) FROM users")
                    stats["total_users"] = cursor.fetchone()["count"] or 0
                    cursor.execute("SELECT COUNT(*) FROM items WHERE is_active = 1")
                    stats["active_listings"] = cursor.fetchone()["count"] or 0
                    cursor.execute("SELECT AVG(trust_score) FROM users")
                    res = cursor.fetchone()
                    stats["avg_trust_score"] = round(float(res["avg"]), 1) if res and res["avg"] else 10.0
                    cursor.execute("SELECT COUNT(*) FROM claims")
                    stats["total_matches"] = cursor.fetchone()["count"] or 0
                    cursor.execute("""
                        SELECT COUNT(*) FROM items
                        WHERE is_active = 1 AND expiry_date IS NOT NULL AND expiry_date <> ''
                          AND TO_DATE(expiry_date,'YYYY-MM-DD') <= CURRENT_DATE + INTERVAL '7 days'
                          AND TO_DATE(expiry_date,'YYYY-MM-DD') >= CURRENT_DATE
                    """)
                    stats["near_expiry_count"] = cursor.fetchone()["count"] or 0
                    cursor.execute("SELECT COUNT(*) FROM items WHERE created_at >= CURRENT_DATE")
                    stats["listings_today_delta"] = cursor.fetchone()["count"] or 0
                    cursor.execute("SELECT COUNT(*) FROM claims WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'")
                    stats["matches_this_week_delta"] = cursor.fetchone()["count"] or 0
                    cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)")
                    stats["users_this_month_delta"] = cursor.fetchone()["count"] or 0
                    return stats
        except Exception:
            return {
                "total_users": 0, "active_listings": 0, "avg_trust_score": 10.0,
                "total_matches": 0, "near_expiry_count": 0,
                "listings_today_delta": 0, "matches_this_week_delta": 0,
                "users_this_month_delta": 0,
            }

    def get_monthly_matches(self):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT TO_CHAR(created_at,'YYYY-MM') AS month, COUNT(*) AS matches
                        FROM claims GROUP BY month ORDER BY month
                    """)
                    return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []

    def get_monthly_items(self):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT TO_CHAR(created_at,'Mon') AS month,
                               COUNT(*) AS matches
                        FROM claims
                        GROUP BY month
                        ORDER BY MIN(created_at)
                    """)
                    return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []

    def get_matches_by_region(self):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT region, COUNT(*) AS matches
                        FROM items GROUP BY region ORDER BY matches DESC
                    """)
                    return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []

    def get_users_by_region(self):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT region, COUNT(*) AS users
                        FROM users GROUP BY region ORDER BY users DESC
                    """)
                    return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []

    def get_expiring_items(self):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT item_name, category, region, expiry_date
                        FROM items WHERE expiry_date IS NOT NULL
                        ORDER BY expiry_date ASC LIMIT 10
                    """)
                    return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []

    def get_past_transactions(self, user_id):
        try:
            user_id = str(user_id)
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM past_transactions
                        WHERE buyer_id = %s OR seller_id = %s
                        ORDER BY completed_at DESC
                    """, (user_id, user_id))
                    rows = cursor.fetchall()
                    return {"transactions": [dict(r) for r in rows]}
        except Exception as e:
            import traceback
            st.error("DB ERROR in get_past_transactions")
            st.code(traceback.format_exc())
            return {"transactions": []}

    def is_item_reserved(self, item_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT reserved_by, status
                        FROM items
                        WHERE id = %s
                    """, (item_id,))
                    row = cursor.fetchone()
                    if not row:
                        return False
                    if row["reserved_by"] is not None:
                        return True
                    if row["status"] in ["reserved", "waiting_seller", "waiting_buyer"]:
                        return True
            return False
        except Exception:
            return False

    # ── COMPANY INVENTORY (separate table — never mixed with personal items) ──

    def add_company_item(self, user_id, item_name, stock_name, category, region,
                         quantity=1, description="", expiry_date=None,
                         image_path=None, listing_type="sell",
                         price=None, phone_number=None, exchange_offer=None,
                         exchange_want=None):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:

                    region = (region or "").strip().title()

                    cursor.execute("""
                        INSERT INTO company_items
                            (user_id, item_name, stock_name, category, region,
                             quantity, description, expiry_date, image_path,
                             listing_type, price, phone_number,
                             exchange_offer, exchange_want)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        user_id, item_name, stock_name, category, region,
                        quantity, description, expiry_date, image_path,
                        listing_type,
                        float(price) if price is not None else None,
                        phone_number, exchange_offer, exchange_want,
                    ))
                    conn.commit()
                    return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_company_items(self, user_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id AS item_id, item_name, stock_name, category,
                               region, quantity, description, expiry_date,
                               image_path, listing_type, price, phone_number,
                               exchange_offer, exchange_want,
                               seller_shipped, buyer_received, status, alert_sent,
                               created_at
                        FROM company_items
                        WHERE user_id = %s AND is_active = 1
                        ORDER BY
                            CASE
                                WHEN expiry_date IS NOT NULL AND expiry_date <> ''
                                THEN TO_DATE(expiry_date,'YYYY-MM-DD')
                                ELSE '9999-12-31'::DATE
                            END ASC,
                            id DESC
                    """, (user_id,))
                    return {"success": True, "items": [dict(row) for row in cursor.fetchall()]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_all_company_items(
        self,
        search=None,
        category=None,
        region=None,
        listing_type=None,
        exclude_user_id=None,
    ):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                        SELECT ci.id AS item_id, ci.user_id, ci.item_name, ci.stock_name,
                               ci.category, ci.region, ci.quantity, ci.description,
                               ci.expiry_date, ci.image_path, ci.listing_type, ci.price,
                               ci.phone_number,
                               ci.exchange_offer, ci.exchange_want,
                               ci.created_at,
                               u.username AS seller_name, u.company_name
                        FROM company_items ci
                        JOIN users u ON ci.user_id = u.id
                        WHERE ci.is_active = 1 AND ci.reserved_by IS NULL
                    """
                    params = []
                    if exclude_user_id is not None:
                        query += " AND ci.user_id <> %s"
                        params.append(exclude_user_id)
                    if category:
                        query += " AND ci.category = %s"
                        params.append(category)
                    if search:
                        query += " AND ci.item_name ILIKE %s"
                        params.append(f"%{search}%")
                    if region:
                        target = region.strip().lower()
                        if target in ("pulau pinang", "penang"):
                            query += " AND LOWER(TRIM(ci.region)) IN ('pulau pinang', 'penang')"
                        else:
                            query += " AND LOWER(TRIM(ci.region)) = %s"
                            params.append(target)
                    if listing_type:
                        query += " AND ci.listing_type = %s"
                        params.append(listing_type)
                    query += " ORDER BY ci.id DESC"
                    cursor.execute(query, params)
                    return {"success": True, "items": [dict(row) for row in cursor.fetchall()]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_company_item(self, item_id, user_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT user_id FROM company_items WHERE id = %s", (item_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {"success": False, "error": "Item not found"}
                    if row["user_id"] != user_id:
                        return {"success": False, "error": "Unauthorized"}
                    cursor.execute("DELETE FROM company_items WHERE id = %s", (item_id,))
                    conn.commit()
                    return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_near_expiry_company_items(self, user_id, days=14):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id AS item_id, item_name, stock_name, quantity,
                               expiry_date, alert_sent
                        FROM company_items
                        WHERE user_id = %s AND is_active = 1
                          AND expiry_date IS NOT NULL AND expiry_date <> ''
                          AND TO_DATE(expiry_date,'YYYY-MM-DD') <= CURRENT_DATE + INTERVAL '{days} days'
                          AND TO_DATE(expiry_date,'YYYY-MM-DD') >= CURRENT_DATE
                        ORDER BY expiry_date ASC
                    """.format(days=days), (user_id,))
                    return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []

    def mark_company_item_shipped(self, item_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE company_items SET seller_shipped = TRUE WHERE id = %s", (item_id,)
                    )
                    conn.commit()
            self._check_transaction_complete(item_id, source_table="company_items")
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def mark_company_item_received(self, item_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE company_items SET buyer_received = TRUE WHERE id = %s", (item_id,)
                    )
                    cursor.execute("""
                        SELECT user_id, item_name
                        FROM company_items
                        WHERE id = %s
                    """, (item_id,))
                    item = cursor.fetchone()
                    if item:
                        cursor.execute("""
                            INSERT INTO notifications (user_id, title, body)
                            VALUES (%s, %s, %s)
                        """, (
                            item["user_id"],
                            "📦 Buyer Confirmed Receipt",
                            f"Buyer has received '{item['item_name']}'. "
                            f"Please confirm shipment to complete the transaction."
                        ))
                    conn.commit()
            self._check_transaction_complete(item_id, source_table="company_items")
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def reserve_company_item(self, item_id, user_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT reserved_by FROM company_items WHERE id = %s", (item_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {"success": False, "error": "Item not found"}
                    if row["reserved_by"] is not None:
                        return {"success": False, "error": "Already reserved"}
                    cursor.execute("""
                        UPDATE company_items SET reserved_by = %s, buyer_id = %s WHERE id = %s
                    """, (user_id, user_id, item_id))
                    conn.commit()
                    return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def cancel_company_reservation(self, item_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE company_items
                        SET reserved_by = NULL, buyer_id = NULL, status = 'active'
                        WHERE id = %s
                    """, (item_id,))
                    conn.commit()
                    return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_company_cart_items(self, user_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT ci.id AS item_id, ci.item_name, ci.category, ci.region,
                               ci.quantity, ci.description, ci.image_path,
                               ci.listing_type, ci.price, ci.phone_number,
                               ci.exchange_offer, ci.exchange_want,
                               ci.buyer_received, ci.seller_shipped, ci.created_at,
                               u.username AS seller_name, u.company_name
                        FROM company_items ci
                        JOIN users u ON ci.user_id = u.id
                        WHERE ci.reserved_by = %s
                        ORDER BY ci.created_at DESC
                    """, (user_id,))
                    return {"success": True, "items": [dict(row) for row in cursor.fetchall()]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_company_stats(self, user_id):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    stats = {}

                    cursor.execute("""
                        SELECT COUNT(*) AS count
                        FROM company_items
                        WHERE user_id = %s AND is_active = 1
                    """, (user_id,))
                    stats["total_listings"] = cursor.fetchone()["count"] or 0

                    cursor.execute("""
                        SELECT COUNT(*) AS count
                        FROM company_items
                        WHERE user_id = %s
                          AND is_active = 1
                          AND expiry_date IS NOT NULL
                          AND expiry_date <> ''
                          AND TO_DATE(expiry_date, 'YYYY-MM-DD')
                              BETWEEN CURRENT_DATE
                              AND CURRENT_DATE + INTERVAL '14 days'
                    """, (user_id,))
                    stats["near_expiry"] = cursor.fetchone()["count"] or 0

                    cursor.execute("""
                        SELECT COUNT(*) AS count
                        FROM past_transactions
                        WHERE seller_id = %s
                          AND source_table = 'company_items'
                    """, (user_id,))
                    stats["completed_sales"] = cursor.fetchone()["count"] or 0

                    cursor.execute("""
                        SELECT COALESCE(SUM(price), 0) AS total
                        FROM past_transactions
                        WHERE seller_id = %s
                          AND source_table = 'company_items'
                    """, (user_id,))
                    stats["total_revenue"] = float(cursor.fetchone()["total"] or 0)

                    return stats

        except Exception as e:
            return {
                "total_listings": 0,
                "near_expiry": 0,
                "completed_sales": 0,
                "total_revenue": 0.0,
                "error": str(e)
            }
        

    #----------------COMPANY INVENTORY-------------------
    def get_inventory_by_company(self, company_id):
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT *
            FROM inventory
            WHERE company_id = %s
            ORDER BY item_name ASC
        """, (company_id,))

        items = cur.fetchall()

        cur.close()
        conn.close()

        return items
    
    def add_inventory_item(
        self,
        company_id,
        item_name,
        category,
        quantity,
        unit,
        supplier=None,
        expiry_date=None,
        notes=None
    ):
        try:
            conn = self._get_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO inventory (
                    company_id,
                    item_name,
                    category,
                    quantity,
                    unit,
                    supplier,
                    expiry_date,
                    notes
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                company_id,
                item_name,
                category,
                quantity,
                unit,
                supplier,
                expiry_date,
                notes
            ))

            conn.commit()

            cur.close()
            conn.close()

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}
        
    def update_inventory_quantity(
        self,
        item_id,
        user_id,
        new_quantity,
        note=None
    ):
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT *
                FROM inventory
                WHERE id = %s
            """, (item_id,))

            item = cur.fetchone()

            if not item:
                return {"success": False, "error": "Inventory item not found"}

            old_quantity = float(item["quantity"])
            quantity_used = old_quantity - float(new_quantity)

            cur.execute("""
                UPDATE inventory
                SET quantity = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                new_quantity,
                item_id
            ))
    
            cur.execute("""
                INSERT INTO inventory_usage_log (
                    inventory_id,
                    company_id,
                    quantity_used,
                    note
                )
                VALUES (%s,%s,%s,%s)
            """, (
                item_id,
                item["company_id"],
                quantity_used,
                note
            ))

            conn.commit()

            cur.close()
            conn.close()

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}
        

    def update_inventory_item(
        self,
        item_id,
        user_id,
        item_name,
        category,
        quantity,
        unit,
        supplier=None,
        expiry_date=None,
        notes=None
    ):
        try:
            conn = self._get_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE inventory
                SET
                    item_name = %s,
                    category = %s,
                    quantity = %s,
                    unit = %s,
                    supplier = %s,
                    expiry_date = %s,
                    notes = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                item_name,
                category,
                quantity,
                unit,
                supplier,
                expiry_date,
                notes,
                item_id
            ))

            conn.commit()

            cur.close()
            conn.close()

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}
        

    def delete_inventory_item(self, item_id, user_id):
        try:
            conn = self._get_connection()
            cur = conn.cursor()

            cur.execute("""
                DELETE FROM inventory
                WHERE id = %s
            """, (item_id,))

            conn.commit()
    
            cur.close()
            conn.close()

            return {"success": True}
    
        except Exception as e:
            return {"success": False, "error": str(e)}


@st.cache_resource(show_spinner=False)
def get_shared_db():
    return EcoMatchDB()
