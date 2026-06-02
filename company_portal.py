import streamlit as st

from c_marketplace import render_company_marketplace
from c_dashboard import render_company_dashboard
from c_myitems import render_company_items
from c_upload import render_company_upload
from c_cart import render_company_cart
from c_transactions import render_company_past_transactions
from c_my_inventory import render_company_inventory_page


def run_company_portal(db, user_id):

    if "c_page" not in st.session_state:
        st.session_state.c_page = "dashboard"

    st.sidebar.title("🏢 Company Portal")

    choice = st.sidebar.radio(
        "Navigate",
        ["Dashboard", "My Items", "Upload Item", "Marketplace", "Cart", "Transactions"]
    )

    mapping = {
        "Dashboard": "dashboard",
        "My Items": "items",
        "Upload Item": "upload",
        "Marketplace": "marketplace",
        "Cart": "cart",
        "Transactions": "transactions"
    }

    st.session_state.c_page = mapping[choice]

    if st.session_state.c_page == "dashboard":
        render_company_dashboard(db, user_id)

    elif st.session_state.c_page == "items":
        render_company_items(db, user_id)

    elif st.session_state.c_page == "upload":
        render_company_upload(db, user_id)

    elif st.session_state.c_page == "marketplace":
        render_company_marketplace(db, user_id)

    elif st.session_state.c_page == "cart":
        render_company_cart(db, user_id)

    elif st.session_state.c_page == "transactions":
        render_company_past_transactions(db, user_id)