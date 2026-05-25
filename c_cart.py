import streamlit as st
import re
import html


def render_company_cart(db, user_id):
    st.markdown("""
    <div class="co-header">
        <h1>🛒 My Order Cart</h1>
    </div>
    """, unsafe_allow_html=True)

    items = db.get_company_cart_items(user_id).get("items", [])

    if not items:
        st.info("Cart empty")
        return

    for item in items:
        desc = re.sub(r"<[^>]+>", "", str(item.get("description","")))

        st.markdown(f"""
        ### {html.escape(item.get('item_name',''))}
        🏢 {item.get('company_name','—')}  
        💰 {item.get('price','Free')}
        💬 {desc}
        """)