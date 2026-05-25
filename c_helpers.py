import streamlit as st
import cloudinary.uploader
from datetime import datetime, date

# ── IMAGE UPLOAD ─────────────────────────────────────────

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

def save_company_image(uploaded_file):
    if uploaded_file is None:
        return None

    ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        st.error(f"❌ Unsupported file type: .{ext}")
        return None

    try:
        result = cloudinary.uploader.upload(
            uploaded_file,
            folder="ecomatch_company",
            transformation=[{
                "width": 500,
                "height": 500,
                "crop": "pad",
                "background": "white",
                "gravity": "center"
            }]
        )
        return result.get("secure_url")

    except Exception as e:
        st.error(f"❌ Upload failed: {e}")
        return None


# ── HELPERS ─────────────────────────────────────────────

def _expiry_badge(expiry_str):
    if not expiry_str:
        return "expiry-ok", "No Expiry"

    try:
        expiry_dt = datetime.strptime(expiry_str, "%Y-%m-%d").date()
        days_left = (expiry_dt - date.today()).days

        if days_left < 0:
            return "expiry-urgent", "EXPIRED"
        if days_left <= 7:
            return "expiry-urgent", f"{days_left}d left"
        if days_left <= 14:
            return "expiry-warn", f"{days_left}d left"
        return "expiry-ok", f"{days_left}d left"

    except ValueError:
        return "expiry-ok", "No Expiry"


def _lt_badge(listing_type, price=None):
    if listing_type == "sell":
        return "lt-sell", f"RM {float(price):.2f}" if price else "Sell"
    if listing_type == "exchange":
        return "lt-exchange", "Exchange"
    return "lt-free", "Free"