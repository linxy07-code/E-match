import cloudinary
import cloudinary.uploader
import streamlit as st
from database import EcoMatchDB
from PIL import Image # Keeping this just in case you want local edits
import io

# 1. Initialize Database
db = EcoMatchDB()

# 2. Configure Cloudinary
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key    = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"],
    secure = True
)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

def save_uploaded_file(uploaded_file) -> str | None:
    if uploaded_file is None:
        return None

    ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        st.error(f"❌ Unsupported file type '.{ext}'")
        return None

    try:
        upload_result = cloudinary.uploader.upload(
            uploaded_file,
            folder="ecomatch_uploads",
            transformation=[
                {
                    "width": 500,
                    "height": 500,
                    "crop": "pad",
                    "background": "white",
                    "gravity": "center"
                }
            ]
        )
        return upload_result.get("secure_url")

    except Exception as e:
        st.error(f"❌ Cloud upload failed: {e}")
        return None

    
def render_upload_page():
    if not st.session_state.get("logged_in"):
        st.warning("⚠️ Please sign in to list an item.")
        st.stop()

    # 1. Initialize our "toggle switch"
    if "upload_success_mode" not in st.session_state:
        st.session_state.upload_success_mode = False

    user_id = st.session_state["user_id"]

    # ══════════════════════════════════════════════════════════════════════════
    # MODE A: SUCCESS CHOICE (Only shows after a successful post)
    # ══════════════════════════════════════════════════════════════════════════
    if st.session_state.upload_success_mode:
        st.balloons()
        
        st.markdown("""<div class="page-header"><h1>🎉 Item Successfully Listed!</h1></div>""", unsafe_allow_html=True)
        
        st.success("Great job! Your item is now visible to the community.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🛒 View in Marketplace", use_container_width=True):
                st.session_state.upload_success_mode = False 
                st.session_state.current_page = "🛒  Marketplace"
                st.rerun()
        with col2:
            if st.button("➕ Upload Another Item", use_container_width=True):
                for key in ["upload_item_name", "upload_description", "upload_image_file",
                            "upload_listing_type", "upload_price"]:
                    if key in st.session_state:
                        del st.session_state[key]
                
                st.session_state.upload_success_mode = False
                st.rerun()
        
        return # STOP HERE

    # ══════════════════════════════════════════════════════════════════════════
    # MODE B: THE ORIGINAL FORM (Shows by default)
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("""<div class="page-header"><h1>📦 List a New Resource</h1></div>""", unsafe_allow_html=True)
    
    col_main, col_side = st.columns([2, 1])
    with col_main:
        st.markdown("<div class='form-section'><p class='form-section-title'>📋 Item Details</p>", unsafe_allow_html=True)
        item_name = st.text_input("Item Name *", key="upload_item_name")
        category = st.selectbox("Category *", ["Groceries & Food", "Household", "Electronics", "Fashion & Apparel", "Lifestyle & Hobbies", "Others"], key="upload_category")
        region = st.selectbox("Pickup Region *", ["Johor", "Kedah", "Kelantan", "Melaka", "Negeri Sembilan", "Pahang", "Perak", "Perlis", "Pulau Pinang", "Selangor", "Terengganu", "Sabah", "Sarawak"], key="upload_region")
        description = st.text_area("Description", key="upload_description")
        has_expiry = st.checkbox("This item has an expiry date", key="upload_has_expiry")
        expiry_date = st.date_input("Expiry Date", key="upload_expiry_date") if has_expiry else None

        # ── LISTING TYPE ──────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("<p class='form-section-title'>💰 Listing Type</p>", unsafe_allow_html=True)

        LISTING_TYPE_OPTIONS = {
            "🆓 Free of Charge": "free",
            "🔄 Exchange / Swap": "exchange",
            "💵 Sell": "sell",
        }

        listing_type_label = st.radio(
            "How would you like to offer this item? *",
            options=list(LISTING_TYPE_OPTIONS.keys()),
            key="upload_listing_type_label",
            horizontal=True,
        )
        listing_type = LISTING_TYPE_OPTIONS[listing_type_label]

        # Show price field only when "Sell" is selected
        price = None
        if listing_type == "sell":
            price = st.number_input(
                "Your Price (RM) *",
                min_value=0.01,
                step=0.50,
                format="%.2f",
                key="upload_price",
                help="Set the price in Malaysian Ringgit (RM).",
            )
        elif listing_type == "exchange":
            st.info("💡 Describe what you're looking to exchange for in the Description field above.")

        st.markdown("</div>", unsafe_allow_html=True)

    with col_side:
        st.markdown("<div class='form-section'><p class='form-section-title'>🖼️ Item Image</p>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload", type=list(ALLOWED_EXTENSIONS), key="upload_image_file")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("📤 Post Item", use_container_width=True):
        if not item_name or not uploaded_file:
            st.error("Please provide both a name and an image.")
            return

        # Validate price when listing type is "sell"
        if listing_type == "sell" and (price is None or price <= 0):
            st.error("Please enter a valid price for your item.")
            return

        with st.spinner("Uploading..."):
            image_url = save_uploaded_file(uploaded_file)
    
        if image_url:
            expiry_str = expiry_date.strftime("%Y-%m-%d") if expiry_date else None
            result = db.add_item(
                user_id=user_id,
                item_name=item_name,
                category=category,
                region=region,
                expiry_date=expiry_str,
                image_path=image_url,
                description=description,
                listing_type=listing_type,       # "free" | "exchange" | "sell"
                price=price if listing_type == "sell" else None,
            )
        
            if result["success"]:
                st.session_state.upload_success_mode = True
                st.rerun()