import streamlit as st
import streamlit.components.v1 as components
from c_styles import COMPANY_CSS
from c_helpers import save_company_image
from PIL import Image, ImageOps
import io
import re


# ── PILLOW IMAGE STANDARDIZATION HELPER ───────────────────────────────────────

def _process_and_standardize_image(uploaded_file, target_size=(400, 300)):
    """
    Opens an uploaded image, fits the ENTIRE original image inside a 4:3 canvas
    without cropping edges, and pads any empty space with a white background.
    """
    try:
        # Open image via Pillow
        img = Image.open(uploaded_file)
        
        # Convert to RGB mode if it's PNG or WEBP with transparency
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # Automatically rotate if the image metadata contains EXIF rotation info
        img = ImageOps.exif_transpose(img)
        
        # Scale the image down proportionally so it completely fits inside target_size
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # Create a blank white 4:3 canvas background
        padded_img = Image.new("RGB", target_size, color="white")
        
        # Perfectly center the scaled original image onto our canvas container
        paste_x = (target_size[0] - img.size[0]) // 2
        paste_y = (target_size[1] - img.size[1]) // 2
        padded_img.paste(img, (paste_x, paste_y))
        
        # Save back into a Byte stream mimicking a native file upload object
        img_byte_arr = io.BytesIO()
        padded_img.save(img_byte_arr, format='JPEG', quality=90)
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

    # ── FORM ───────────────────────────────────────────────
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

        # ── FIXED: PHONE NUMBER PART (REMOVED + - AND BLOCKED ALPHABETS) ──────
        st.markdown("<label style='font-size: 14px;'>Contact Phone Number</label>", unsafe_allow_html=True)
        
        # Create tight side-by-side components for the prefix and the input field
        phone_col_prefix, phone_col_input = st.columns([1, 6])
        
        with phone_col_prefix:
            # Displays the locked static prefix vertically aligned with the input box
            st.markdown("""
                <div style='padding-top: 6px; font-weight: bold; font-size: 16px; color: #555;'>
                    +60
                </div>
            """, unsafe_allow_html=True)
            
        with phone_col_input:
            # Switched to st.text_input to drop increment/decrement buttons entirely
            phone_input_raw = st.text_input(
                "Company Contact Phone Number Label Hidden", 
                value="", 
                placeholder="123456789",
                label_visibility="collapsed",
                key="co_phone_digits",
                help="Optional: Let other companies contact you directly for inventory pickup arrangements."
            )
            
            # Browser UI Javascript verification: dynamically restricts entry to real numbers on key press
            components.html(
                """
                <script>
                const parentDoc = window.parent.document;
                const inputs = parentDoc.querySelectorAll('input[aria-label="Company Contact Phone Number Label Hidden"]');
                inputs.forEach(input => {
                    if (!input.dataset.numericBound) {
                        input.dataset.numericBound = "true";
                        
                        // Drop characters that are not digits right at typing time
                        input.addEventListener('keypress', function(e) {
                            if (!/[0-9]/.test(e.key)) {
                                e.preventDefault();
                            }
                        });
                        
                        // Sanitize pasted elements completely
                        input.addEventListener('input', function(e) {
                            this.value = this.value.replace(/[^0-9]/g, '');
                        });
                    }
                });
                </script>
                """,
                height=0,
                width=0
            )
            
            # Strip non-digits cleanly for background processing
            phone_digits = re.sub(r"\D", "", phone_input_raw)

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
            # 1. Process image to contain full dimensions and pad out empty space
            processed_file_preview = _process_and_standardize_image(uploaded_file)
            
            # 2. Open byte stream with PIL to force Streamlit to read custom canvas layout dimensions
            preview_image = Image.open(processed_file_preview)
            
            # 3. Clean layout rendering
            st.image(preview_image, use_container_width=True, caption="Preview")

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
            # Format and pad picture container perfectly on the fly before cloud storage triggers
            standard_image_bytes = _process_and_standardize_image(uploaded_file)
            image_url = save_company_image(standard_image_bytes)

        if image_url:
            expiry_str = expiry_date.strftime("%Y-%m-%d") if expiry_date else None
            
            # Parse and merge the +60 prefix safely for database submission
            final_phone_string = f"+60{phone_digits}" if len(phone_digits) > 0 else None

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
                phone_number=final_phone_string,
                exchange_offer=exchange_offer,
                exchange_want=exchange_want
            )

            if result.get("success"):
                st.session_state.co_upload_success = True
                st.rerun()
            else:
                st.error(f"Could not save: {result.get('error')}")