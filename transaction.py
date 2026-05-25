# transaction.py
import streamlit as st


def render_past_transaction_page(db, user_id):
    st.markdown("""
    <div class="page-header">
        <h1>📜 Past Transactions</h1>
        <p>Your completed trading history on E-match</p>
    </div>""", unsafe_allow_html=True)


    res = db.get_past_transactions(user_id)
    transactions = res.get("transactions", [])

    if not transactions:
        st.info("No completed transactions yet.")
        return

    seller_tx = [
        t for t in transactions
        if int(t.get("seller_id")) == int(user_id)
    ]

    buyer_tx = [
        t for t in transactions
        if int(t.get("buyer_id")) == int(user_id)
    ]

    tab1, tab2 = st.tabs(["🏪 Sold", "🛒 Bought"])

    def render_card(t, role):
        price = t.get("price")
        price_disp = f"RM {price}" if price else "Free / Exchange"

        completed_at = t.get("completed_at")
        if isinstance(completed_at, str):
            date_str = completed_at
        elif completed_at:
            date_str = completed_at.strftime("%d %b %Y %H:%M")
        else:
            date_str = "—"

        st.markdown(f"""
        <div style="
            background:white;
            padding:16px;
            border-radius:12px;
            border:1px solid #d1fae5;
            margin-bottom:10px;
        ">
            <b>🎉 {t.get("item_name","Unknown")}</b><br>
            {role}<br>
            💰 {price_disp}<br>
            🆔 {t.get("item_id")}<br>
            🕒 {date_str}
        </div>
        """, unsafe_allow_html=True)

    with tab1:
        if not seller_tx:
            st.info("No sales yet.")
        else:
            for t in seller_tx:
                render_card(t, "You sold this item")

    with tab2:
        if not buyer_tx:
            st.info("No purchases yet.")
        else:
            for t in buyer_tx:
                render_card(t, "You bought this item")