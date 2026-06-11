import streamlit as st
from c_styles import COMPANY_CSS
from c_helpers import save_company_image


def render_company_upload(db, user_id):
    st.markdown(COMPANY_CSS, unsafe_allow_html=True)

    if "co_upload_success" not in st.session_state:
        st.session_state.co_upload_success = False

    # ── SUCCESS VIEW ─────────────────────────────────────────────
    if st.session_state.co_upload_success:
        st.balloons()
        st.markdown("""
        <div class="co-header">
            <h1>🎉 Item Listed Successfully!</h1>
            <p>Your item is now visible on the Company Marketplace</p>
        </div>
        """, unsafe_allow_html=True)

        st.success("Item successfully published.")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🏭 Marketplace", use_container_width=True):
                st.session_state.co_upload_success = False
                st.session_state.c_page = "marketplace"
                st.rerun()

        with col2:
            if st.button("📦 My Items", use_container_width=True):
                st.session_state.co_upload_success = False
                st.session_state.c_page = "items"
                st.rerun()

        with col3:
            if st.button("➕ Add Another", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if key.startswith("co_"):
                        del st.session_state[key]

                st.session_state.co_upload_success = False
                st.rerun()

        return

    # ── HEADER ─────────────────────────────────────────────
    st.markdown("""
    <div class="co-header">
        <h1>📋 Upload Inventory Item</h1>
        <p>Add stock to your company inventory</p>
    </div>
    """, unsafe_allow_html=True)

    # ── FORM (same structure as personal page) ─────────────
    col_main, col_side = st.columns([2, 1])

    with col_main:
        st.markdown("#### 📋 Item Details")

        item_name = st.text_input("Item Name *", key="co_item_name")

        stock_name = st.text_input("Stock Name", key="co_stock_name")

        category = st.selectbox(
            "Category *",
            ["Groceries & Food", "Household", "Electronics",
             "Fashion & Apparel", "Lifestyle & Hobbies", "Others"],
            key="co_category"
        )

        region = st.selectbox(
            "Region *",
            ["Johor","Kedah","Kelantan","Melaka","Negeri Sembilan",
             "Pahang","Perak","Perlis","Pulau Pinang",
             "Selangor","Terengganu","Sabah","Sarawak"],
            key="co_region"
        )

        quantity = st.number_input(
            "Quantity *",
            min_value=1,
            value=1,
            step=1,
            key="co_quantity"
        )

        # ── Phone Number (MANDATORY) ──────────────────────────────────────────
        phone_number = st.text_input(
            "Contact Phone Number *",
            placeholder="+60 12-345 6789",
            key="co_phone",
            help="Required: Buyers will use this number to arrange pickup or delivery."
        )

        has_expiry = st.checkbox("This item has an expiry date", key="co_has_expiry")
        expiry_date = (
            st.date_input("Expiry Date", key="co_expiry")
            if has_expiry else None
        )

        st.markdown("---")
        st.markdown("#### 💰 Listing Type")

        LISTING_TYPE_OPTIONS = {
            "🆓 Free of Charge": "free",
            "🔄 Exchange / Swap": "exchange",
            "💵 Sell": "sell",
        }

        listing_label = st.radio(
            "How would you like to offer this item? *",
            list(LISTING_TYPE_OPTIONS.keys()),
            horizontal=True,
            key="co_listing_type_label"
        )

        listing_type = LISTING_TYPE_OPTIONS[listing_label]

        exchange_offer = None
        exchange_want = None
        description = ""

        if listing_type == "exchange":
            st.markdown("#### 🔄 Exchange Details")

            exchange_offer = st.text_area(
                "Item I'm offering * (required for Exchange)",
                key="co_exchange_offer",
                placeholder="What are you giving away?"
            )

            exchange_want = st.text_area(
                "Item I want * (required for Exchange)",
                key="co_exchange_want",
                placeholder="What do you want in exchange?"
            )

            description = f"OFFER: {exchange_offer}\nWANT: {exchange_want}"

            st.info("💡 Both exchange fields must be completed before you can submit.")

        else:
            description = st.text_area("Description", key="co_description")

        price = None
        if listing_type == "sell":
            price = st.number_input(
                "Price (RM) *",
                min_value=0.01,
                step=0.50,
                format="%.2f",
                key="co_price"
            )

    with col_side:
        st.markdown("#### 🖼️ Item Image")

        uploaded_file = st.file_uploader(
            "Upload image",
            type=["jpg", "jpeg", "png", "webp"],
            key="co_image"
        )

        if uploaded_file:
            st.image(uploaded_file, use_container_width=True)

    # ── SUBMIT ─────────────────────────────────────────────
    st.markdown("---")

    if st.button("📤 Post Item", use_container_width=True):
        # ── VALIDATION ────────────────────────────────────────────────────────
        errors = []

        if not item_name.strip():
            errors.append("Item name is required.")

        if not uploaded_file:
            errors.append("Please upload an image.")

        if not phone_number.strip():
            errors.append("Contact phone number is required.")

        if listing_type == "sell" and (price is None or price <= 0):
            errors.append("Please enter a valid price.")

        if listing_type == "exchange":
            if not exchange_offer or not exchange_offer.strip():
                errors.append("'Item I'm offering' is required for Exchange listings.")
            if not exchange_want or not exchange_want.strip():
                errors.append("'Item I want in return' is required for Exchange listings.")

        if errors:
            for err in errors:
                st.error(f"❌ {err}")
            return

        with st.spinner("Uploading item…"):
            image_url = save_company_image(uploaded_file)

        if image_url:
            expiry_str = expiry_date.strftime("%Y-%m-%d") if expiry_date else None

            result = db.add_company_item(
                user_id=user_id,
                item_name=item_name,
                stock_name=stock_name,
                category=category,
                region=region,
                quantity=quantity,
                expiry_date=expiry_str,
                image_path=image_url,
                description=description,
                listing_type=listing_type,
                price=price if listing_type == "sell" else None,
                phone_number=phone_number.strip() if phone_number else None,
                exchange_offer=exchange_offer,
                exchange_want=exchange_want
            )

            if result.get("success"):
                st.session_state.co_upload_success = True
                st.rerun()
            else:
                st.error(f"Could not save: {result.get('error')}")