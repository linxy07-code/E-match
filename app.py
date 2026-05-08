import streamlit as st
from datetime import datetime
from database import EcoMatchDB
from upload import render_upload_page
from marketplace import render_marketplace_page
import os
import time
from streamlit_cookies_controller import CookieController

# ── INITIALIZATION ───────────────────────────────────────────────────────────
db = EcoMatchDB()
controller = CookieController()

st.set_page_config(
    page_title="E-match | Resource Sharing Platform",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 1. Initialize Session State
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "🛒  Marketplace"
if "username" not in st.session_state:
    st.session_state.username = ""
if "auth_tab" not in st.session_state:
    st.session_state.auth_tab = "login"

# 2. Auto-Login Logic (Cookies)
if not st.session_state.logged_in:
    cookies = controller.getAll() 
    if not cookies:
        time.sleep(0.1)
        cookies = controller.getAll()

    remembered_user_id = cookies.get('ematch_user')
    if remembered_user_id:
        user_data = db.get_user_by_id(remembered_user_id) 
        if user_data:
            st.session_state.logged_in = True
            st.session_state.user_id = remembered_user_id
            st.session_state.username = user_data.get('username', 'User')
            st.session_state.region = user_data.get('region', 'Unknown')
            st.session_state.trust_score = user_data.get('trust_score', 10)
            st.rerun()

# ── Global CSS (Original Colors Kept) ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Fraunces:opsz,wght@9..144,300;9..144,500;9..144,600&display=swap');

:root {
    --green-50:  #f0fdf4; --green-100: #dcfce7; --green-200: #bbf7d0;
    --green-300: #86efac; --green-500: #22c55e; --green-600: #16a34a;
    --green-700: #15803d; --green-800: #166534; --green-900: #14532d;
    --teal-400:  #2dd4bf; --teal-500:  #14b8a6; --teal-600:  #0d9488;
    --neutral-50:  #fafafa; --neutral-100: #f5f5f5; --neutral-200: #e5e5e5;
    --neutral-500: #737373; --neutral-700: #404040; --neutral-900: #171717;
    --shadow-sm: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
    --shadow-md: 0 4px 12px rgba(0,0,0,.08), 0 2px 4px rgba(0,0,0,.04);
    --shadow-lg: 0 10px 30px rgba(0,0,0,.10), 0 4px 8px rgba(0,0,0,.05);
    --radius: 14px;
}

html, body, .stApp {
    font-family: 'DM Sans', sans-serif;
    background-color: #edfaf2;
    background-image:
        radial-gradient(ellipse 80% 60% at 10% 0%, rgba(34,197,94,.12) 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 90% 100%, rgba(20,184,166,.10) 0%, transparent 60%);
    color: var(--neutral-900);
}

[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #166534 0%, #14532d 100%) !important;
}
[data-testid="stSidebar"] * { color: #d1fae5 !important; }

.sidebar-brand {
    background: rgba(255,255,255,.08); border-radius: 12px; padding: 18px 20px; margin-bottom: 24px; border: 1px solid rgba(255,255,255,.12);
}
.sidebar-brand h2 { font-family: 'Fraunces', serif !important; font-size: 1.5rem !important; color: #ffffff !important; margin: 0 !important; }

.page-header {
    background: linear-gradient(135deg, var(--green-700) 0%, var(--teal-600) 100%);
    border-radius: var(--radius); padding: 32px 36px; margin-bottom: 28px; box-shadow: var(--shadow-lg);
}
.page-header h1 { font-family: 'Fraunces', serif !important; font-size: 2rem !important; color: #ffffff !important; margin: 0 0 6px !important; }
.page-header p { color: rgba(255,255,255,.75) !important; font-size:.95rem; margin:0; }

.card { background: #ffffff; border-radius: var(--radius); border: 1px solid var(--green-200); box-shadow: var(--shadow-sm); padding: 22px 24px; margin-bottom: 15px; }

/* Customizing the Sidebar Toggle Button */
button[data-testid="stSidebarCollapseButton"] {
    visibility: visible !important; color: #15803d !important; background-color: #ffffff !important; border: 1px solid #bbf7d0 !important;
}

div.stButton > button {
    background: linear-gradient(135deg, var(--green-600), var(--teal-600)) !important; color: white !important;
    border-radius: 9px !important; border: none !important;
}
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR SECTION ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""<div class="sidebar-brand"><h2>🌿 E-match</h2><p>Resource Organisation Management</p></div>""", unsafe_allow_html=True)

    if st.session_state.logged_in:
        st.markdown(f"""
        <div style="padding:10px 4px">
            <p style="font-size:.78rem;line-height:1.8;color:#86efac!important">
            🌍 Region: <strong style="color:#d1fae5!important">{st.session_state.get('region', '—')}</strong><br>
            👤 User: <strong style="color:#d1fae5!important">{st.session_state.username}</strong><br>
            ⭐ Trust Score: <strong style="color:#d1fae5!important">{st.session_state.get('trust_score', 10)} / 10</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

        NAV_OPTIONS = ["🛒  Marketplace", "📦  Upload Item", "🧾  My Items", "🛡️  Trust & Safety", "📊  Dashboard"]
        selection = st.radio("Navigation", NAV_OPTIONS, index=NAV_OPTIONS.index(st.session_state.current_page), label_visibility="collapsed")
        
        if selection != st.session_state.current_page:
            st.session_state.current_page = selection
            st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            controller.remove('ematch_user') 
            st.session_state.clear()
            st.rerun()

# ── MAIN ROUTER ───────────────────────────────────────────────────────────────
page_key = st.session_state.current_page.strip().split("  ", 1)[-1]

if not st.session_state.logged_in:
    # ── AUTHENTICATION SECTION (Only shows when logged out) ──
    st.markdown("""<div class="page-header"><h1>Welcome to E-match</h1><p>Malaysia's trusted platform for community resource sharing</p></div>""", unsafe_allow_html=True)

    _, center, _ = st.columns([1, 2, 1])
    with center:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔑  Sign In", use_container_width=True, key="tab_login"):
                st.session_state.auth_tab = "login"
                st.rerun()
        with c2:
            if st.button("📝  Create Account", use_container_width=True, key="tab_reg"):
                st.session_state.auth_tab = "register"
                st.rerun()

        if st.session_state.auth_tab == "login":
            st.markdown('<div class="card"><h3>Sign In</h3><p style="color:#737373; font-size:0.85rem;">Access your account to continue.</p></div>', unsafe_allow_html=True)
            l_user = st.text_input("Username", key="l_user")
            l_pass = st.text_input("Password", type="password", key="l_pass")
            remember = st.checkbox("Remember me on this device")
            
            if st.button("Sign In →", use_container_width=True, key="do_login"):
                res = db.verify_user(l_user.strip(), l_pass)
                if res["success"]:
                    st.session_state.logged_in = True
                    st.session_state.user_id = res["user_id"]
                    st.session_state.username = l_user.strip()
                    st.session_state.region = res["region"]
                    st.session_state.trust_score = res.get("trust_score", 10)
                    if remember: controller.set('ematch_user', res["user_id"])
                    st.rerun()
                else:
                    st.error(f"❌ {res['error']}")
        else:
            st.markdown('<div class="card"><h3>Create Account</h3><p style="color:#737373; font-size:0.85rem;">Join the E-match community.</p></div>', unsafe_allow_html=True)
            r_user = st.text_input("Username", key="r_user")
            r_email = st.text_input("Email", key="r_email")
            r_pass = st.text_input("Password", type="password", key="r_pass")
            r_reg = st.selectbox("Region", ["Selangor", "Kuala Lumpur", "Penang", "Johor", "Melaka", "Sabah", "Sarawak"])
            if st.button("Create My Account →", use_container_width=True):
                db.add_user(r_user, r_pass, r_reg, "Personal")
                st.success("Account created! Please Sign In.")
                st.session_state.auth_tab = "login"
                st.rerun()
else:
    # ── LOGGED IN PAGES ──
    if page_key == "Marketplace":
        render_marketplace_page()

    elif page_key == "Upload Item":
        # Check if the user just successfully uploaded something
        if st.session_state.get("upload_success", False):
            st.balloons()  # 🎈 The balloons trigger here
            
            st.markdown('<div class="page-header"><h1>✅ Item Posted!</h1><p>Your resource is now live on the marketplace.</p></div>', unsafe_allow_html=True)
            
            st.success("Listing successful!")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📦 Post Another Item", use_container_width=True):
                    st.session_state.upload_success = False
                    st.rerun()
            with col2:
                if st.button("🛒 View Marketplace", use_container_width=True):
                    st.session_state.upload_success = False
                    st.session_state.current_page = "🛒  Marketplace"
                    st.rerun()
        else:
            # If they haven't uploaded yet, show the form
            render_upload_page()

    elif page_key == "My Items":
        st.markdown("""<div class="page-header"><h1>🧾 My Listings</h1><p>Manage the items you have posted</p></div>""", unsafe_allow_html=True)
        items_res = db.get_user_items(st.session_state.user_id)
        if not items_res["items"]:
            st.info("No items posted yet.")
        else:
            for item in items_res["items"]:
                with st.container():
                    t_col, i_col = st.columns([2, 1])
                    with t_col:
                        st.markdown(f"### {item['item_name']}")
                        st.write(f"Category: {item['category']} | Region: {item['region']}")
                        if st.button(f"🗑️ Delete {item['item_name']}", key=f"del_{item['item_id']}"):
                            db.delete_item(item['item_id'], st.session_state.user_id)
                            st.rerun()
                    with i_col:
                        if item.get('image_path'): st.image(item['image_path'], use_container_width=True)
                st.divider()

    elif page_key == "Trust & Safety":
        st.markdown("""<div class="page-header"><h1>🛡️ Trust & Safety</h1><p>Your reputation and community standing</p></div>""", unsafe_allow_html=True)
        st.metric("Trust Score", f"{st.session_state.trust_score} / 10")
        st.success("✅ Follow the community guidelines to keep your score high.")

    elif page_key == "Dashboard":
        st.markdown("""<div class="page-header"><h1>📊 Analytics</h1><p>Platform performance overview</p></div>""", unsafe_allow_html=True)
        st.write("Statistics and visual charts will be displayed here.")