import streamlit as st

def render_past_transaction_page(db, user_id):

    st.markdown("## 📜 Past Transactions")

    res = db.get_past_transactions(user_id)
    transactions = res.get("transactions", [])

    if not transactions:
        st.info("No past transactions yet.")
        return

    for t in transactions:
        st.markdown(f"""
        <div style="
            background:white;
            padding:14px;
            border-radius:10px;
            border:1px solid #ddd;
            margin-bottom:10px;
        ">
            <b>{t['item_name']}</b><br>
            💰 Transaction Price: {t['price'] if t['price'] is not None else "Free / Exchange"}<br>
            🧾 Type: {t['listing_type']}<br>
            🆔 Item ID: {t['item_id']}<br>
            👤 Buyer ID: {t['buyer_id']}<br>
            🏪 Seller ID: {t['seller_id']}<br>
            🕒 Completed: {t['completed_at']}
        </div>
        """, unsafe_allow_html=True)