import os
import streamlit as st
from datetime import datetime, date
from database import EcoMatchDB

db = EcoMatchDB()

def expiry_badge(expiry_str):
    if not expiry_str: return "expiry-ok", "✅ No Expiry"
    expiry_dt = datetime.strptime(expiry_str, "%Y-%m-%d").date()
    days_left = (expiry_dt - date.today()).days
    if days_left < 0: return "expiry-urgent", "❌ EXPIRED"
    if days_left <= 3: return "expiry-urgent", f"🚨 {days_left}d left"
    return "expiry-ok", f"✅ {days_left}d left"

def render_marketplace_page():
    st.markdown("""<div class="page-header"><h1>🛒 Marketplace</h1></div>""", unsafe_allow_html=True)
    
    f1, f2 = st.columns([3, 1])
    search_q = f1.text_input("", placeholder="🔍 Search...", key="mp_search")
    filt_region = f2.selectbox("Region", ["All Regions", "Selangor", "Kuala Lumpur"], key="mp_region")

    db_result = db.get_all_items(search=search_q if search_q else None)
    if db_result["success"]:
        items = db_result["items"]
        cols = st.columns(3)
        for idx, item in enumerate(items):
            exp_cls, exp_label = expiry_badge(item.get("expiry_date"))
            with cols[idx % 3]:
                st.markdown(f"""<div class="mp-card">
                    <p class="mp-card-title">{item['item_name']}</p>
                    <span class="mp-card-expiry {exp_cls}">{exp_label}</span>
                </div>""", unsafe_allow_html=True)
                # 1. Get the image link from the database
                img_url = item.get("image_path")

                # 2. Show the image if it exists. 
                # We use 'use_container_width=True' to keep it at that standard size you like!
                if img_url:
                    st.image(img_url, use_container_width=True)
                else:
                    # Optional: show a small text if there's no image
                    st.caption("No image available")
                if st.button("Claim", key=f"cl_{item['item_id']}"):
                    st.success("Requested!")