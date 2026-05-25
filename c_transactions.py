import streamlit as st


def render_company_past_transactions(db, user_id):
    st.markdown("""
    <div class="co-header">
        <h1>📜 Transaction History</h1>
    </div>
    """, unsafe_allow_html=True)

    transactions = db.get_past_transactions(user_id).get("transactions", [])

    if not transactions:
        st.info("No transactions yet")
        return

    for t in transactions:
        role = "Seller" if str(t.get("seller_id")) == str(user_id) else "Buyer"

        st.markdown(f"""
        🎉 {t.get('item_name')}  
        Role: {role}  
        Amount: RM {t.get('price','0')}
        """)