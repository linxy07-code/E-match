# upload.py
import cloudinary
import cloudinary.uploader
import streamlit as st
from database import EcoMatchDB
from PIL import Image, ImageOps
import io

db = EcoMatchDB()

cloudinary.config(
    cloud_name = st.secrets["cloudinary"]["cloud_name"],
    api_key    = st.secrets["cloudinary"]["api_key"],
    api_secret = st.secrets["cloudinary"]["api_secret"],
    secure     = True
)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


# ── PILLOW IMAGE CONTAIN & PAD STANDARDIZATION HELPER ──────────────────

def _process_and_standardize_image(uploaded_file, target_size=(400, 300)):
    """
    Opens an uploaded image, fits the ENTIRE original image inside a 4:3 canvas
    without cropping edges, and pads any empty space with a white background.
    """
    try:
        # Reset the source stream pointer before reading
        if hasattr(uploaded_file, 'seek'):
            uploaded_file.seek(0)
            
        img = Image.open(uploaded_file)
        
        # Convert to RGB if it's PNG or WEBP with transparency profiles
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # Fix auto-rotation if uploaded from mobile phones via EXIF metadata
        img = ImageOps.exif_transpose(img)
        
        # Scale the image down proportionally so it completely fits inside target_size
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # Create a blank white 4:3 canvas container
        padded_img = Image.new("RGB", target_size, color="white")
        
        # Perfectly center the scaled original image onto our canvas container
        paste_x = (target_size[0] - img.size[0]) // 2
        paste_y = (target_size[1] - img.size[1]) // 2
        padded_img.paste(img, (paste_x, paste_y))
        
        # Save back into a Byte stream mimicking a native file object
        img_byte_arr = io.BytesIO()
        padded_img.save(img_byte_arr, format='JPEG', quality=90)
        img_byte_arr.seek(0)
        img_byte_arr.name = getattr(uploaded_file, 'name', 'uploaded_image.jpg')
        return img_byte_arr
        
    except Exception as e:
        # Fallback to the original file silently if an issue occurs
        if hasattr(uploaded_file, 'seek'):
            uploaded_file.seek(0)
        return uploaded_file


def save_uploaded_file(processed_file) -> str | None:
    """Accepts the processed image file stream and uploads it to Cloudinary."""
    if processed_file is None:
        return None
    ext = processed_file.name.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        st.error(f"❌ Unsupported file type '.{ext}'")
        return None
    try:
        upload_result = cloudinary.uploader.upload(
            processed_file,
            folder="ecomatch_uploads"
        )
        return upload_result.get("secure_url")
    except Exception as e:
        st.error(f"❌ Cloud upload failed: {e}")
        return None


def render_upload_page():
    if not st.session_state.get("logged_in"):
        st.warning("⚠️ Please sign in to list an item.")
        st.stop()

    if "upload_success_mode" not in st.session_state:
        st.session_state.upload_success_mode = False

    user_id = st.session_state["user_id"]

    # ── SUCCESS VIEW ──────────────────────────────────────────────────────────
    if st.session_state.upload_success_mode:
        st.balloons()
        st.markdown("""
        <div class="page-header">
            <h1>🎉 Item Successfully Listed!</h1>
            <p>Your item is now visible to the community</p>
        </div>""", unsafe_allow_html=True)
        st.success("Great job! Your item is now visible to the community.")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🛒 View Marketplace", use_container_width=True):
                st.session_state.upload_success_mode = False
                st.session_state.current_page = "Marketplace"
                st.rerun()
        with col2:
            if st.button("📦 View My Items", use_container_width=True):
                st.session_state.upload_success_mode = False
                st.session_state.current_page = "My Items"
                st.rerun()
        with col3:
            if st.button("➕ Upload Another Item", use_container_width=True):
                for key in [
                    "upload_item_name", "upload_category", "upload_region",
                    "upload_condition", "upload_quantity", "upload_description",
                    "upload_image_file", "upload_listing_type_label",
                    "upload_price", "upload_has_expiry", "upload_expiry_date",
                    "upload_phone_digits",
                ]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.session_state.upload_success_mode = False
                st.rerun()
        return

    # ── UPLOAD FORM ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="page-header">
        <h1>📦 List a New Resource</h1>
        <p>Share your item with the E-match community</p>
    </div>""", unsafe_allow_html=True)

    col_main, col_side = st.columns([2, 1])

    with col_main:
        st.markdown("#### 📋 Item Details")

        item_name = st.text_input("Item Name *", key="upload_item_name")

        category = st.selectbox("Category *", [
            "Groceries & Food", "Household", "Electronics",
            "Fashion & Apparel", "Lifestyle & Hobbies", "Others"
        ], key="upload_category")

        region = st.selectbox("Pickup Region *", [
            "Johor","Kedah","Kelantan","Melaka","Negeri Sembilan",
            "Pahang","Perak","Perlis","Pulau Pinang",
            "Selangor","Terengganu","Sabah","Sarawak"
        ], key="upload_region")

        condition = st.selectbox("Item Condition *", [
            "Brand New", "Good", "Second Hand"
        ], key="upload_condition")

        quantity = st.number_input("Quantity *", min_value=1, value=1, step=1,
                                   key="upload_quantity")

        # ── FIXED: HIDE THE +/- INCREMENT BUTTONS FOR PHONE WIDGET ────────────
        st.markdown("""
            <style>
            /* Hides the complete custom +/- step button interface row */
            div[data-testid="stNumberInput"] div[role="group"] {
                display: none !important;
            }
            /* Removes standard webkit native input spinner styling arrows */
            input[type=number]::-webkit-inner-spin-button, 
            input[type=number]::-webkit-outer-spin-button { 
                -webkit-appearance: none; 
                margin: 0; 
            }
            input[type=number] {
                -moz-appearance: textfield;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("<label style='font-size: 14px;'>Contact Phone Number</label>", unsafe_allow_html=True)
        
        phone_col_prefix, phone_col_input = st.columns([1, 6])
        
        with phone_col_prefix:
            st.markdown("""
                <div style='padding-top: 6px; font-weight: bold; font-size: 16px; color: #555;'>
                    +60
                </div>
            """, unsafe_allow_html=True)
            
        with phone_col_input:
            phone_digits = st.number_input(
                "Contact Phone Number Label Hidden", 
                min_value=0, 
                value=0, 
                step=1,
                label_visibility="collapsed",
                key="upload_phone_digits",
                help="Optional: Let buyers contact you directly for pickup arrangements."
            )

        has_expiry  = st.checkbox("This item has an expiry date", key="upload_has_expiry")
        expiry_date = (
            st.date_input("Expiry Date", key="upload_expiry_date")
            if has_expiry else None
        )
        
        st.markdown("---")
        st.markdown("#### 💰 Listing Type")

        LISTING_TYPE_OPTIONS = {
            "🆓 Free of Charge": "free",
            "🔄 Exchange / Swap": "exchange",
            "💵 Sell":            "sell",
        }
        listing_type_label = st.radio(
            "How would you like to offer this item? *",
            options=list(LISTING_TYPE_OPTIONS.keys()),
            horizontal=True,
            key="upload_listing_type_label"
        )
        listing_type = LISTING_TYPE_OPTIONS[listing_type_label]
        
        exchange_offer = None
        exchange_want = None
        description = ""

        if listing_type == "exchange":
            st.markdown("#### 🔄 Exchange Details")

            exchange_offer = st.text_area(
                "Item I'm offering *",
                key="upload_exchange_offer",
                placeholder="What are you giving away?"
            )

            exchange_want = st.text_area(
                "Item I want in return *",
                key="upload_exchange_want",
                placeholder="What do you want in exchange?"
            )

            description = f"OFFER: {exchange_offer}\nWANT: {exchange_want}"

        else:
            description = st.text_area(
                "Description",
                key="upload_description"
            )

        price = None
        if listing_type == "sell":
            price = st.number_input(
                "Your Price (RM) *",
                min_value=0.01, step=0.50, format="%.2f",
                key="upload_price",
                help="Set the price in Malaysian Ringgit (RM)."
            )
        elif listing_type == "exchange":
            st.info("💡 Describe what you're looking to exchange for in the Description field above.")

    # ── IMAGE SIDE-BAR LAYOUT ─────────────────────────────────────────────────
    with col_side:
        st.markdown("#### 🖼️ Item Image")
        uploaded_file = st.file_uploader(
            "Upload", type=list(ALLOWED_EXTENSIONS), key="upload_image_file"
        )

        if uploaded_file:
            # Create a separate, isolated file stream layout just to build the UI preview card
            preview_stream = _process_and_standardize_image(uploaded_file)
            preview_image = Image.open(preview_stream)
            st.image(preview_image, caption="Preview", use_container_width=True)

    # ── POST BUTTON & DATA MERGE ──────────────────────────────────────────────
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

        with st.spinner("Uploading item…"):
            # Fresh generation pass right here ensures the binary data is perfectly loaded
            final_processed_file = _process_and_standardize_image(uploaded_file)
            
            # Reset internal file reader indexes to 0 to completely clean up pointer states
            if hasattr(final_processed_file, 'seek'):
                final_processed_file.seek(0)
                
            image_url = save_uploaded_file(final_processed_file)

        if image_url:
            expiry_str = expiry_date.strftime("%Y-%m-%d") if expiry_date else None
            
            # Safely concatenate the fixed Country Prefix string with the digits entered
            final_phone_string = f"+60{phone_digits}" if phone_digits > 0 else None

            result = db.add_item(
                user_id      = user_id,
                item_name    = item_name,
                category     = category,
                region       = region,
                condition    = condition,
                quantity     = quantity,
                expiry_date  = expiry_str,
                image_path   = image_url,
                description  = description,
                listing_type = listing_type,
                price        = price if listing_type == "sell" else None,
                phone_number = final_phone_string,
                exchange_offer = exchange_offer,
                exchange_want  = exchange_want
            )
            if result.get("success"):
                st.session_state.upload_success_mode = True
                st.rerun()
            else:
                st.error(f"Could not save listing: {result.get('error')}")