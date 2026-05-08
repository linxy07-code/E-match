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
        # ── CLOUD UPLOAD WITH AUTOMATIC RESIZING ──
        # This tells Cloudinary: "Take the image and force it into a 500x500 square"
        # This ensures all images in your marketplace look exactly the same size.
        upload_result = cloudinary.uploader.upload(
            uploaded_file,
            folder="ecomatch_uploads",
            transformation=[
                {
                    "width": 500, 
                    "height": 500, 
                    "crop": "pad",      # Changed 'fill' to 'pad'
                    "background": "white", # Adds white bars to the sides if image is skinny
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
        # --- THE BALLOONS ARE HERE ---
        st.balloons() 
        
        st.markdown("""<div class="page-header"><h1>🎉 Item Successfully Listed!</h1></div>""", unsafe_allow_html=True)
        
        st.success("Great job! Your item is now visible to the community.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🛒 View in Marketplace", use_container_width=True):
                # Reset the success mode
                st.session_state.upload_success_mode = False 
                # Set the target page
                st.session_state.current_page = "🛒  Marketplace"
                st.rerun()
        with col2:
            if st.button("➕ Upload Another Item", use_container_width=True):
                # Clear the old form data so it's fresh
                for key in ["upload_item_name", "upload_description", "upload_image_file"]:
                    if key in st.session_state: del st.session_state[key]
                
                st.session_state.upload_success_mode = False # Back to the form
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
        category = st.selectbox("Category *", ["Food", "Household", "Electronics", "Others"], key="upload_category")
        region = st.selectbox("Pickup Region *", ["Selangor", "Kuala Lumpur", "Penang", "Johor"], key="upload_region")
        description = st.text_area("Description", key="upload_description")
        
        has_expiry = st.checkbox("This item has an expiry date", key="upload_has_expiry")
        expiry_date = st.date_input("Expiry Date", key="upload_expiry_date") if has_expiry else None
        st.markdown("</div>", unsafe_allow_html=True)

    with col_side:
        st.markdown("<div class='form-section'><p class='form-section-title'>🖼️ Item Image</p>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload", type=list(ALLOWED_EXTENSIONS), key="upload_image_file")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("📤 Post Item", use_container_width=True):
        if not item_name or not uploaded_file:
            st.error("Please provide both a name and an image.")
            return

        with st.spinner("Uploading..."):
            image_url = save_uploaded_file(uploaded_file)
    
        if image_url:
            expiry_str = expiry_date.strftime("%Y-%m-%d") if expiry_date else None
            result = db.add_item(
                user_id=user_id, item_name=item_name, category=category,
                region=region, expiry_date=expiry_str, image_path=image_url, 
                description=description
            )
        
            if result["success"]:
                # Set the switch to True and rerun to trigger the balloons at the top
                st.session_state.upload_success_mode = True
                st.rerun()