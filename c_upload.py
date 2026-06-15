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
                st.session_state.current_page = "Company Marketplace"
                st.rerun()

        with col2:
            if st.button("📦 My Items", use_container_width=True):
                st.session_state.co_upload_success = False
                st.session_state.current_page = "My Items"
                st.rerun()

        with col3:
            if st.button("➕ Add Another", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if key.startswith("co_"):
                        del st.session_state[key]

                st.session_state.co_upload_success = False
                st.rerun()

        return

    # ── PRE-FILL from near-expiry notification ────────────────────
    # If the user arrived here via a near-expiry action button,
    # pick up the pre-filled values and then clear them so they
    # don't persist across subsequent visits.
    prefill_listing_label = st.session_state.pop("ne_prefill_listing_label", None)
    prefill_item_name     = st.session_state.pop("ne_prefill_item_name", None)
    # Clear the raw value too; the form uses the matching display label.
    st.session_state.pop("ne_prefill_listing_type", None)

    if prefill_item_name:
        st.session_state.co_item_name = prefill_item_name
    if prefill_listing_label:
        st.session_state.co_listing_type_label = prefill_listing_label

    # ── HEADER ─────────────────────────────────────────────────────
    if prefill_listing_label:
        # Show a contextual banner when arriving from a near-expiry alert
        action_map = {
            "💵 Sell":            ("💵", "Sell Near-Expiry Item", "#854d0e", "#fef9c3", "#fde68a"),
            "🆓 Free of Charge":  ("🆓", "Give Away Near-Expiry Item", "#15803d", "#dcfce7", "#bbf7d0"),
            "🔄 Exchange / Swap": ("🔄", "Barter Near-Expiry Item", "#5b21b6", "#ede9fe", "#c4b5fd"),
        }
        icon, action_title, txt_color, bg_color, border_color = action_map.get(
            prefill_listing_label,
            ("📋", "Upload Inventory Item", "#1e3a5f", "#eff6ff", "#bfdbfe"),
        )
        st.markdown(f"""
        <div style="background:{bg_color};border:1px solid {border_color};
        border-left:4px solid {txt_color};border-radius:12px;
        padding:18px 22px;margin-bottom:20px;">
            <p style="margin:0;font-weight:700;font-size:1.05rem;color:{txt_color};">
                {icon} {action_title}
            </p>
            <p style="margin:4px 0 0;font-size:.85rem;color:#475569;">
                The listing type has been pre-selected based on your near-expiry alert.
                Fill in the remaining details and post the item.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="co-header">
        <h1>📋 Upload Inventory Item</h1>
        <p>Add stock to your company inventory</p>
    </div>
    """, unsafe_allow_html=True)

    # ── FORM (same structure as personal page) ─────────────────────
    col_main, col_side = st.columns([2, 1])

    with col_main:
        st.markdown("#### 📋 Item Details")

        # Pre-fill item name if we have one from the alert
        item_name = st.text_input(
            "Item Name *",
            key="co_item_name",
        )

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

        st.markdown("#### 📞 Contact Phone Number")

        phone_col_prefix, phone_col_input = st.columns([1, 6])

        with phone_col_prefix:
            st.markdown("""
                <div style='padding-top: 6px; font-weight: bold; font-size: 16px; color: #555;'>
            +60
                </div>
            """, unsafe_allow_html=True)

        with phone_col_input:
            phone_digits = st.number_input(
                "Contact Phone Number Hidden",
                min_value=0,
                value=0,
                step=1,
                label_visibility="collapsed",
                key="co_phone_digits",
                help="Optional: Let buyers contact your company directly."
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
            "💵 Sell":            "sell",
        }

        option_labels = list(LISTING_TYPE_OPTIONS.keys())

        # Determine default index: use pre-fill if available, else 0
        if prefill_listing_label and prefill_listing_label in option_labels:
            default_lt_index = option_labels.index(prefill_listing_label)
        else:
            default_lt_index = 0

        listing_label = st.radio(
            "How would you like to offer this item? *",
            option_labels,
            index=default_lt_index,
            horizontal=True,
            key="co_listing_type_label",
        )

        listing_type = LISTING_TYPE_OPTIONS[listing_label]

        exchange_offer = None
        exchange_want  = None
        description    = ""

        if listing_type == "exchange":
            st.markdown("#### 🔄 Exchange Details")

            exchange_offer = st.text_area(
                "Item I'm offering *",
                key="co_exchange_offer"
            )

            exchange_want = st.text_area(
                "Item I want *",
                key="co_exchange_want"
            )

            description = f"OFFER: {exchange_offer}\nWANT: {exchange_want}"

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

    # ── SUBMIT ─────────────────────────────────────────────────────
    st.markdown("---")

    if st.button("📤 Post Item", use_container_width=True):

        if not item_name:
            st.error("Please enter an item name.")
            return

        if not uploaded_file:
            st.error("Please upload an image.")
            return

        if listing_type == "sell" and (price is None or price <= 0):
            st.error("Please enter a valid price.")
            return
        
        if phone_digits is None or phone_digits <= 0:
            st.error("Please enter a contact phone number.")
            return

        with st.spinner("Uploading item…"):
            image_url = save_company_image(uploaded_file)
            

        if image_url:
            expiry_str = expiry_date.strftime("%Y-%m-%d") if expiry_date else None
            phone_number = f"+60{phone_digits}"

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
                phone_number=phone_number,
                exchange_offer=exchange_offer,
                exchange_want=exchange_want
            )

            if result.get("success"):
                st.session_state.co_upload_success = True
                st.rerun()
            else:
                st.error(f"Could not save: {result.get('error')}")
