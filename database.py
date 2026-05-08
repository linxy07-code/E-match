import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import streamlit as st

class EcoMatchDB:
    def __init__(self):
        # This automatically grabs the URL from your secrets.toml
        self.db_url = st.secrets["DB_URL"]
        self._init_db()

    def _get_connection(self):
        """Connects to Supabase using psycopg2."""
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)

    def _init_db(self):
        """Creates tables using PostgreSQL syntax."""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                # 1. Users Table
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
                # 2. Items Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS items (
                        id           SERIAL PRIMARY KEY,
                        user_id      INTEGER NOT NULL REFERENCES users(id),
                        item_name    TEXT NOT NULL,
                        category     TEXT,
                        region       TEXT,
                        condition    TEXT DEFAULT 'Good',
                        quantity     INTEGER DEFAULT 1,
                        description  TEXT,
                        expiry_date  TEXT,
                        image_path   TEXT,
                        is_active    INTEGER DEFAULT 1,
                        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # 3. Claims Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS claims (
                        id          SERIAL PRIMARY KEY,
                        item_id     INTEGER NOT NULL REFERENCES items(id),
                        claimer_id  INTEGER NOT NULL REFERENCES users(id),
                        status      TEXT DEFAULT 'pending',
                        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()

    # ── USER METHODS ──
    def add_user(self, username, password, region, user_type):
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO users (username, password_hash, region, user_type) VALUES (%s, %s, %s, %s) RETURNING id",
                        (username, password_hash, region, user_type),
                    )
                    user_id = cursor.fetchone()['id']
                    conn.commit()
                    return {"success": True, "user_id": user_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def verify_user(self, username, password):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id, password_hash, user_type, region, trust_score FROM users WHERE username = %s", (username,))
                    row = cursor.fetchone()
                    if row and bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
                        return {
                            "success": True, "user_id": row["id"], "user_type": row["user_type"],
                            "region": row["region"], "trust_score": row["trust_score"]
                        }
                    return {"success": False, "error": "Invalid credentials"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── ITEM METHODS ──
    def add_item(self, user_id, item_name, category, region, expiry_date=None, image_path=None, condition="Good", quantity=1, description=""):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO items (user_id, item_name, category, region, condition, quantity, description, expiry_date, image_path)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (user_id, item_name, category, region, condition, quantity, description, expiry_date, image_path))
                    conn.commit()
                    return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_all_items(self, category=None, search=None):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                        SELECT i.*, i.id AS item_id, u.username, u.trust_score 
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
                    # We add 'id AS item_id' so your app.py finds the key it's looking for
                    cursor.execute("""
                        SELECT *, id AS item_id 
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
                    cursor.execute("SELECT user_id FROM items WHERE id = %s", (item_id,))
                    row = cursor.fetchone()
                    if not row or row['user_id'] != user_id:
                        return {"success": False, "error": "Unauthorized"}
                    
                    cursor.execute("DELETE FROM items WHERE id = %s", (item_id,))
                    conn.commit()
                    return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_trust_score(self, user_id, delta):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE users 
                        SET trust_score = LEAST(10, GREATEST(0, trust_score + %s)) 
                        WHERE id = %s 
                        RETURNING trust_score
                    """, (delta, user_id))
                    row = cursor.fetchone()
                    conn.commit()
                    return {"success": True, "new_score": row['trust_score']}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_platform_stats(self):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    stats = {}
                    cursor.execute("SELECT COUNT(*) FROM users")
                    stats["total_users"] = cursor.fetchone()['count']
                    cursor.execute("SELECT COUNT(*) FROM items WHERE is_active = 1")
                    stats["active_listings"] = cursor.fetchone()['count']
                    cursor.execute("SELECT AVG(trust_score) FROM users")
                    stats["avg_trust_score"] = round(float(cursor.fetchone()['avg'] or 0), 1)
                    return {"success": True, **stats}
        except Exception as e:
            return {"success": False, "error": str(e)}
        