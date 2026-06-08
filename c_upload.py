import streamlit as st
from c_styles import COMPANY_CSS
from c_helpers import save_company_image
from PIL import Image, ImageOps
import io


# ── PILLOW IMAGE STANDARDIZATION HELPER ───────────────────────────────────────

def _process_and_standardize_image(uploaded_file, target_size=(400, 300)):
    """
    Opens an uploaded image, fixes orientation, center-crops and resizes it 
    to target_size, and returns a BytesIO object ready for your save function.
    """
    try:
        # Open image via Pillow
        img = Image.open(uploaded_file)
        
        # Convert to RGB mode if it's PNG or WEBP with transparency
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # Automatically rotate if the image metadata contains EXIF rotation info
        img = ImageOps.exif_transpose(img)
        
        # Crop and resize to exactly fill target dimensions (Center Crop method)
        standardized_img = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)
        
        # Save back into a Byte stream mimicking a native file upload object
        img_byte_arr = io.BytesIO()
        standardized_img.save(img_byte_arr, format='JPEG', quality=90)
        img_byte_arr.seek(0)
        
        # Keep name metadata intact for backend compatibility
        img_byte_arr.name = getattr(uploaded_file, 'name', 'uploaded_image.jpg')
        return img_byte_arr
        
    except Exception as e:
        # Fallback to original file if processing encounters an error
        st.warning(f"Image formatting optimized with a warning: {e}")
        return uploaded_file


# ── MAIN COMPONENT PAGE ───────────────────────────────────────────────────────

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

        phone_number = st.text_input(
            "Contact Phone Number",
            placeholder="+60 12-345 6789",
            key="co_phone"
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
            # Process and display the same uniform size layout on the screen live!
            processed_file_preview = _process_and_standardize_image(uploaded_file)
            st.image(processed_file_preview, use_container_width=True, caption="Standardized Preview (4:3)")

    # ── SUBMIT ─────────────────────────────────────────────
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

        with st.spinner("Processing image and uploading item…"):
            # Format and resize picture dynamically on the fly before cloud upload triggers
            standard_image_bytes = _process_and_standardize_image(uploaded_file)
            image_url = save_company_image(standard_image_bytes)

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