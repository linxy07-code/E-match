import streamlit as st

from c_styles import COMPANY_CSS
from c_helpers import save_company_image


def render_company_upload(db, user_id):
    st.markdown(COMPANY_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="co-header">
        <h1>📋 Upload Inventory Item</h1>
        <p>Add stock to your company inventory</p>
    </div>""", unsafe_allow_html=True)

    item_name = st.text_input("Product Name *")
    stock_name = st.text_input("Stock Name")
    category = st.selectbox("Category", ["Food","Household","Electronics","Others"])
    region = st.selectbox("Region", ["Selangor","Johor","Penang"])
    quantity = st.number_input("Quantity", 1)

    uploaded = st.file_uploader("Image")

    if st.button("Publish"):
        if not item_name:
            st.error("Name required")
            return

        img = save_company_image(uploaded)

        if img:
            db.add_company_item(
                user_id=user_id,
                item_name=item_name,
                stock_name=stock_name,
                category=category,
                region=region,
                quantity=quantity,
                image_path=img
            )
            st.success("Uploaded!")
            st.rerun()