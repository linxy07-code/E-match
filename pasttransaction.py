# pasttransaction.py
import streamlit as st


def render_past_transaction_page(db, user_id):
    st.markdown("""
    <div class="page-header">
        <h1>📜 Past Transactions</h1>
        <p>Your completed trading history on E-match</p>
    </div>""", unsafe_allow_html=True)

    res          = db.get_past_transactions(user_id)
    transactions = res.get("transactions", [])

    if not transactions:
        st.info("No completed transactions yet. Complete a trade to see your history here!")
        return

    st.caption(f"{len(transactions)} completed transaction(s)")

    for t in transactions:
        seller_id = str(t.get("seller_id") or "")
        buyer_id  = str(t.get("buyer_id")  or "")
        me        = str(user_id)

        if seller_id == me and buyer_id == me:
            role = "👤 Both"
        elif seller_id == me:
            role = "🏪 You were the Seller"
        else:
            role = "🛒 You were the Buyer"

        price_disp = f"RM {t['price']}" if t.get("price") else "Free / Exchange"

        listing_badges = {
            "sell":     ('<span style="background:#fef9c3;color:#854d0e;padding:3px 10px;'
                         'border-radius:999px;font-size:.75rem;font-weight:700;">💵 Sell</span>'),
            "exchange": ('<span style="background:#ede9fe;color:#5b21b6;padding:3px 10px;'
                         'border-radius:999px;font-size:.75rem;font-weight:700;">🔄 Exchange</span>'),
            "free":     ('<span style="background:#dcfce7;color:#15803d;padding:3px 10px;'
                         'border-radius:999px;font-size:.75rem;font-weight:700;">🆓 Free</span>'),
        }
        lt_badge = listing_badges.get(str(t.get("listing_type") or "free"), "")

        completed_at = t.get("completed_at")
        date_str     = completed_at.strftime("%d %b %Y, %I:%M %p") if completed_at else "—"

        st.markdown(f"""
        <div style="
            background:white; padding:18px 20px; border-radius:14px;
            border:1px solid #bbf7d0; margin-bottom:12px;
            box-shadow:0 1px 3px rgba(0,0,0,.05);
        ">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                <span style="font-family:'Fraunces',serif;font-size:1.1rem;
                             font-weight:700;color:#14532d;">
                    🎉 {t.get('item_name','Unknown Item')}
                </span>
                {lt_badge}
            </div>
            <div style="font-size:.85rem;color:#374151;line-height:2;">
                {role}<br>
                💰 <strong>Amount:</strong> {price_disp}<br>
                🆔 <strong>Item ID:</strong> {t.get('item_id','—')}<br>
                🕒 <strong>Completed:</strong> {date_str}
            </div>
        </div>
        """, unsafe_allow_html=True)