# c_transactions.py
import streamlit as st


def render_company_past_transactions(db, user_id):
    st.markdown("""
    <div class="page-header">
        <h1>📜 Transaction History</h1>
        <p>Your company's completed trading history on E-match</p>
    </div>""", unsafe_allow_html=True)

    res          = db.get_past_transactions(user_id)
    transactions = res.get("transactions", [])

    if not transactions:
        st.info("No completed transactions yet.")
        return

    # Split into sold vs bought — compare as int to be safe
    seller_tx = [t for t in transactions if str(t.get("seller_id")) == str(user_id)]
    buyer_tx  = [t for t in transactions if str(t.get("buyer_id"))  == str(user_id)]

    tab1, tab2 = st.tabs(["🏪 Sold", "🛒 Bought"])

    def render_card(t, role):
        price = t.get("price")
        price_disp = f"RM {float(price):.2f}" if price else "Free / Exchange"

        completed_at = t.get("completed_at")
        if isinstance(completed_at, str):
            date_str = completed_at
        elif completed_at:
            date_str = completed_at.strftime("%d %b %Y %H:%M")
        else:
            date_str = "—"

        listing_type = (t.get("listing_type") or "—").capitalize()

        # Show username if available, fall back to ID
        buyer_display  = t.get("buyer_username")  or f"ID {t.get('buyer_id',  '—')}"
        seller_display = t.get("seller_username") or f"ID {t.get('seller_id', '—')}"

        st.markdown(f"""
        <div style="
            background:white;
            padding:18px 20px;
            border-radius:12px;
            border:1px solid #d1fae5;
            margin-bottom:12px;
            box-shadow:0 1px 3px rgba(0,0,0,.06);
        ">
            <p style="font-family:'Fraunces',serif;font-size:1.05rem;
                      font-weight:600;color:#14532d;margin:0 0 10px 0;">
                🎉 {t.get('item_name','Unknown')}
            </p>
            <div style="font-size:.85rem;color:#404040;line-height:1.9;">
                👤 <strong>Role:</strong> {role}<br>
                🛒 <strong>Buyer:</strong> {buyer_display}<br>
                🏪 <strong>Seller:</strong> {seller_display}<br>
                💰 <strong>Amount:</strong> {price_disp}<br>
                🔖 <strong>Type:</strong> {listing_type}<br>
                🆔 <strong>Item ID:</strong> {t.get('item_id','—')}<br>
                🕒 <strong>Completed:</strong> {date_str}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with tab1:
        if not seller_tx:
            st.info("No sales yet.")
        else:
            st.caption(f"{len(seller_tx)} sale(s)")
            for t in seller_tx:
                render_card(t, "You sold this item")

    with tab2:
        if not buyer_tx:
            st.info("No purchases yet.")
        else:
            st.caption(f"{len(buyer_tx)} purchase(s)")
            for t in buyer_tx:
                render_card(t, "You bought this item")