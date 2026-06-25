# app.py
import sys
import os
import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mailer import send_verification_otp
from trust_safety import render_trust_safety_page   # shared for both user types
from upload import render_upload_page
from marketplace import render_marketplace_page
from dashboard import render_dashboard_page
from mycart import render_cart_page
from transaction import render_past_transaction_page
from my_items import render_my_items_page


from company_portal import (
    render_company_dashboard,
    render_company_items,
    render_company_upload,
    render_company_marketplace,
    render_company_cart,
    render_company_past_transactions,
    render_company_inventory_page
)

from datetime import datetime
from database import get_shared_db
import time
from streamlit_cookies_controller import CookieController

NOTIF_BASE = "🔔  Notifications"

st.set_page_config(
    page_title="E-match | Resource Sharing Platform",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── INITIALIZATION ────────────────────────────────────────────────────────────
db         = get_shared_db()
controller = CookieController()

# ── Session state defaults ────────────────────────────────────────────────────
for key, default in [
    ("logged_in",    False),
    ("current_page", "Marketplace"),
    ("username",     ""),
    ("auth_tab",     "login"),
    ("reg_type",     "Personal"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── FIX #5: Cookie auto-login (remember me) ───────────────────────────────────
if not st.session_state.logged_in:
    # Give cookies a moment to load
    cookies = controller.getAll()
    if not cookies and not st.session_state.get("cookies_checked_once"):
        time.sleep(0.3)
        cookies = controller.getAll()
    st.session_state.cookies_checked_once = True

    remembered_user_id = cookies.get("ematch_user")
    if remembered_user_id:
        user_data = db.get_user_by_id(int(remembered_user_id))
        if user_data and user_data.get("status") != "Banned":
            st.session_state.logged_in   = True
            st.session_state.user_id     = int(remembered_user_id)
            st.session_state.username    = user_data.get("username", "User")
            st.session_state.region      = user_data.get("region", "Unknown")
            st.session_state.trust_score = user_data.get("trust_score", 10)
            st.session_state.user_type   = user_data.get("user_type", "Personal")
            if st.session_state.user_type == "Company":
                st.session_state.current_page = "Company Marketplace"
            else:
                st.session_state.current_page = "Marketplace"
            st.rerun()

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Fraunces:opsz,wght@9..144,300;9..144,500;9..144,600&display=swap');

:root {
    --green-500:#22c55e; --green-600:#16a34a; --green-700:#15803d;
    --green-800:#166534; --green-900:#14532d;
    --teal-400:#2dd4bf;  --teal-500:#14b8a6;  --teal-600:#0d9488;
    --green-200:#bbf7d0;
    --neutral-500:#737373; --neutral-700:#404040; --neutral-900:#171717;
    --shadow-sm:0 1px 3px rgba(0,0,0,.06),0 1px 2px rgba(0,0,0,.04);
    --shadow-lg:0 10px 30px rgba(0,0,0,.10),0 4px 8px rgba(0,0,0,.05);
    --radius:14px;
}
html,body,.stApp {
    font-family:'DM Sans',sans-serif;
    background-color:#edfaf2;
    background-image:
        radial-gradient(ellipse 80% 60% at 10% 0%,rgba(34,197,94,.12) 0%,transparent 60%),
        radial-gradient(ellipse 60% 50% at 90% 100%,rgba(20,184,166,.10) 0%,transparent 60%);
    color:var(--neutral-900);
}
[data-testid="stSidebar"] { background:linear-gradient(160deg,#166534 0%,#14532d 100%) !important; }
[data-testid="stSidebar"] * { color:#d1fae5 !important; }

.sidebar-brand {
    background:rgba(255,255,255,.08); border-radius:12px; padding:18px 20px;
    margin-bottom:20px; border:1px solid rgba(255,255,255,.12);
}
.sidebar-brand h2 { font-family:'Fraunces',serif !important; font-size:1.5rem !important;
                    color:#fff !important; margin:0 !important; }

.page-header {
    background:linear-gradient(135deg,var(--green-700) 0%,var(--teal-600) 100%);
    border-radius:var(--radius); padding:32px 36px; margin-bottom:28px;
    box-shadow:var(--shadow-lg);
}
.page-header h1 { font-family:'Fraunces',serif !important; font-size:2rem !important;
                  color:#fff !important; margin:0 0 6px !important; }
.page-header p  { color:rgba(255,255,255,.75) !important; font-size:.95rem; margin:0; }

.card { background:#fff; border-radius:var(--radius); border:1px solid var(--green-200);
        box-shadow:var(--shadow-sm); padding:22px 24px; margin-bottom:15px; }

.my-item-card { background:#fff; border-radius:var(--radius); border:1px solid var(--green-200);
                box-shadow:var(--shadow-sm); padding:20px 24px; margin-bottom:8px; }
.my-item-title { font-family:'Fraunces',serif; font-size:1.2rem; font-weight:600;
                 color:var(--green-900); margin:0 0 10px 0; }
.my-item-row   { font-size:.85rem; color:var(--neutral-700); margin:3px 0; }
.my-item-row strong { color:var(--green-700); }
.my-item-desc  { font-size:.85rem; color:#525252; margin-top:10px; padding-top:10px;
                 border-top:1px solid #f0fdf4; line-height:1.5; }

.lt-badge { display:inline-block; font-size:.75rem; font-weight:700;
            padding:3px 10px; border-radius:999px; margin-left:6px; }
.lt-free     { background:#dcfce7; color:#15803d; border:1px solid #bbf7d0; }
.lt-exchange { background:#ede9fe; color:#5b21b6; border:1px solid #c4b5fd; }
.lt-sell     { background:#fef9c3; color:#854d0e; border:1px solid #fde68a; }

.notif-item { padding:12px 14px; border-radius:10px; margin-bottom:8px;
              border-left:3px solid var(--green-500); background:#f0fdf4; }
.notif-item.unread { background:#dcfce7; border-left-color:var(--teal-500); }
.notif-title  { font-weight:600; font-size:.875rem; color:var(--green-900); margin:0 0 4px 0; }
.notif-body   { font-size:.8rem; color:#404040; margin:0; }
.notif-time   { font-size:.72rem; color:#737373; margin-top:4px; }

.metric-row { display:flex; gap:16px; margin-bottom:24px; flex-wrap:wrap; }
.metric-card { flex:1; min-width:180px; background:white; border:1px solid var(--green-200);
               border-radius:var(--radius); padding:20px 22px; box-shadow:var(--shadow-sm);
               position:relative; overflow:hidden; }
.metric-card::before { content:''; position:absolute; top:0; left:0; right:0; height:3px;
                       background:linear-gradient(90deg,var(--green-500),var(--teal-400)); }
.metric-value { font-family:'Fraunces',serif; font-size:1.9rem; font-weight:600;
                color:var(--green-800); line-height:1; margin-bottom:4px; }
.metric-label { font-size:.78rem; color:var(--neutral-500); text-transform:uppercase; font-weight:600; }
.metric-delta { font-size:.75rem; margin-top:4px; }

.trust-ring-wrap { display:flex; flex-direction:column; align-items:center; padding:24px;
                   background:white; border-radius:14px; border:1px solid #bbf7d0; }
.trust-score-num { font-family:'Fraunces',serif; font-size:3.5rem; color:#15803d; font-weight:600; }
.trust-score-denom { font-size:1.2rem; color:#737373; }
.trust-label { font-weight:700; color:#16a34a; margin-top:5px; }
.trust-bar-bg { height:10px; border-radius:999px; background:#dcfce7; width:100%; overflow:hidden; }
.trust-bar-fill { height:100%; background:linear-gradient(90deg,#22c55e,#2dd4bf); }
.rule-row { display:flex; justify-content:space-between; padding:10px 0;
            border-bottom:1px solid #f0fdf4; }
.rule-impact-pos { color:#16a34a; font-weight:700; }
.rule-impact-neg { color:#dc2626; font-weight:700; }

div.stButton > button {
    background:linear-gradient(135deg,var(--green-600),var(--teal-600)) !important;
    color:white !important; border-radius:9px !important; border:none !important;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _lt_badge(listing_type, price=None):
    if listing_type == "sell":
        label = f"💵 RM {float(price):.2f}" if price else "💵 Sell"
        css   = "lt-sell"
    elif listing_type == "exchange":
        label, css = "🔄 Exchange", "lt-exchange"
    else:
        label, css = "🆓 Free", "lt-free"
    return f'<span class="lt-badge {css}">{label}</span>'


def get_transaction_status(item):
    seller = item.get("seller_shipped", False)
    buyer  = item.get("buyer_received", False)
    if seller and buyer:   return "completed"
    if seller:             return "waiting_buyer"
    if buyer:              return "waiting_seller"
    return "active"


def normalize_page(page):
    if "Notifications" in page:
        return "Notifications"
    parts = page.split("  ", 1)
    return parts[-1].strip() if len(parts) > 1 else page.strip()


page_key = normalize_page(st.session_state.current_page)

# ── DIALOGS ───────────────────────────────────────────────────────────────────

@st.dialog("🔔 New Item Requests!")
def show_login_notifications(notifs):
    for n in notifs[:3]:
        st.markdown(f"""
        <div style="margin-bottom:12px;padding:12px;border-left:4px solid #2e7d32;
        background:#f1f8e9;border-radius:6px;">
            <p style="margin:0;font-weight:bold;color:#2e7d32;">🟢 {n.get('title','Incoming Request')}</p>
            <p style="margin:4px 0 0;color:#333;font-size:.95rem;">{n.get('body','Someone wants to match with your item!')}</p>
        </div>""", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🔔 Go to Notifications", width="stretch", type="primary"):
        st.session_state.current_page = "Notifications"
        st.rerun()


@st.dialog("🎉 Transaction Complete!")
def show_transaction_complete_dialog(item_name="your item"):
    st.markdown(f"""
    <div style="text-align:center;padding:20px 0;">
        <div style="font-size:4rem;margin-bottom:12px;">🎉</div>
        <h2 style="font-family:'Fraunces',serif;color:#166534;margin:0 0 10px 0;">
            Congratulations!
        </h2>
        <p style="color:#374151;font-size:1rem;margin:0 0 16px 0;">
            Your transaction for <strong>"{item_name}"</strong> has been successfully completed!
        </p>
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:16px;">
            <p style="margin:0;color:#166534;font-weight:600;">
                ✅ Both parties confirmed. The listing has been archived in your Past Transactions.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    user_type = st.session_state.get("user_type", "Personal")
    dest = "Company Marketplace" if user_type == "Company" else "Marketplace"
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📜 View History", width="stretch"):
            st.session_state.current_page = "Company Transactions" if user_type == "Company" else "Past Transactions"
            st.rerun()
    with c2:
        if st.button("🛒 Continue Shopping", width="stretch", type="primary"):
            st.session_state.current_page = dest
            st.rerun()


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    user_type_session = st.session_state.get("user_type", "Personal")
    brand_icon = "🏢" if user_type_session == "Company" else "🌿"
    brand_sub  = "Company Resource Platform" if user_type_session == "Company" else "Resource Organisation Management"
    st.markdown(
        f'<div class="sidebar-brand"><h2>{brand_icon} E-match</h2><p>{brand_sub}</p></div>',
        unsafe_allow_html=True,
    )

    if st.session_state.logged_in:
        user_id = st.session_state.get("user_id")
        unread  = db.count_unread_notifications(user_id)

        type_color = "#60a5fa" if user_type_session == "Company" else "#86efac"
        
        # Display trust score for ALL user types
        trust_line = (
            f'⭐ Trust: <strong style="color:#d1fae5!important">'
            f'{st.session_state.get("trust_score",10)} / 10</strong><br>'
        )

        st.markdown(f"""
        <div style="padding:10px 4px">
            <p style="font-size:.78rem;line-height:1.8;color:#86efac!important">
                {'🏢' if user_type_session=='Company' else '👤'} Type:
                <strong style="color:{type_color}!important">{user_type_session}</strong><br>
                🌍 Region: <strong style="color:#d1fae5!important">{st.session_state.get('region','—')}</strong><br>
                👤 User: <strong style="color:#d1fae5!important">{st.session_state.username}</strong><br>
                {trust_line}
            </p>
        </div>
        """, unsafe_allow_html=True)

        notif_label = NOTIF_BASE + (f" ({unread})" if unread else "")

        if user_type_session == "Company":
            NAV_OPTIONS = [
                ("🏭  Company Marketplace",   "Company Marketplace"),
                ("🛒  My Order Cart",         "Company Cart"),
                ("📜  Transaction History",   "Company Transactions"),
                ("🗂️  My Inventory",          "Company Inventory"),
                ("📦  Upload Items",      "Upload Inventory"),
                ("🗂️  My Uploads / Items",    "My Items"),
                ("🛡️  Trust & Safety",        "Company Trust & Safety"),
                ("📊  Company Dashboard",     "Company Dashboard"),
                (notif_label,                 "Notifications"),
            ]
        else:
            NAV_OPTIONS = [
                ("🛒  Marketplace",           "Marketplace"),
                ("🧾  My Cart",               "My Cart"),
                ("📜  Past Transactions",     "Past Transactions"),
                ("📦  Upload Item",           "Upload Item"),
                ("🧾  My Uploads / Items",    "My Items"),
                ("🛡️  Trust & Safety",        "Trust & Safety"),
                ("📊  Dashboard",             "Dashboard"),
                (notif_label,                 "Notifications"),
            ]

        selection = st.radio(
            "Navigation",
            NAV_OPTIONS,
            index=next((i for i, (_, p) in enumerate(NAV_OPTIONS) if p == page_key), 0),
            format_func=lambda x: x[0],
            label_visibility="collapsed",
        )

        _, page = selection
        if st.session_state.current_page != page:
            st.session_state.current_page = page
            st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout", width="stretch"):
            # FIX #5: properly clear remember-me cookie on logout
            try:
                all_cookies = controller.getAll()
                if "ematch_user" in all_cookies:
                    controller.remove("ematch_user")
            except Exception:
                pass
            st.session_state.clear()
            st.rerun()


# ── AUTH FLOW ─────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:

    # ── OTP VERIFICATION ─────────────────────────────────────────────────────
    if "pending_verification_user_id" in st.session_state:
        st.markdown(
            '<div class="page-header"><h1>🌿 Complete Your Verification</h1>'
            "<p>Security verification for safe resource sharing in Malaysia</p></div>",
            unsafe_allow_html=True,
        )
        _, center, _ = st.columns([1, 2, 1])
        with center:
            st.markdown(f"""
            <div class="card">
                <h3>Enter OTP Code</h3>
                <p style="color:#737373;font-size:.85rem">
                    Hi <strong>{st.session_state['pending_username']}</strong>,
                    we dispatched a 6-digit security code to your email.<br>
                    <span style="color:#dc2626;font-size:.8rem">
                        ⚠️ Your account will remain inactive until you complete verification.
                        Cancelling will permanently delete this account.
                    </span>
                </p>
            </div>""", unsafe_allow_html=True)
 
            entered_code = st.text_input("6-Digit Code", max_chars=6, key="otp_input")
            c1, c2 = st.columns(2)
 
            with c1:
                if st.button("Verify Account →", width="stretch", type="primary"):
                    verify_res = db.check_verification_code(
                        st.session_state["pending_verification_user_id"], entered_code
                    )
                    if verify_res["success"]:
                        st.success("🎉 Account verified! You can now log in.")
                        del st.session_state["pending_verification_user_id"]
                        del st.session_state["pending_username"]
                        st.session_state.auth_tab = "login"
                        st.rerun()
                    else:
                        st.error(f"❌ {verify_res['error']}")
 
            with c2:
                # Cancel: delete the unverified account entirely
                if st.button("Cancel & Delete Account", width="stretch"):
                    pending_uid = st.session_state["pending_verification_user_id"]
                    db.delete_unverified_user(pending_uid)
                    del st.session_state["pending_verification_user_id"]
                    del st.session_state["pending_username"]
                    st.info("Account removed. You can register again at any time.")
                    st.rerun()
 
        st.stop()

    # ── AUTH LAYOUT ───────────────────────────────────────────────────────────
    st.markdown(
        '<div class="page-header"><h1>Welcome to E-match</h1>'
        "<p>Malaysia's trusted platform for community resource sharing</p></div>",
        unsafe_allow_html=True,
    )
    _, center, _ = st.columns([1, 2, 1])
    with center:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔑  Sign In", width="stretch", key="tab_login"):
                st.session_state.auth_tab = "login"; st.rerun()
        with c2:
            if st.button("📝  Create Account", width="stretch", key="tab_reg"):
                st.session_state.auth_tab = "register"; st.rerun()

        # ── SIGN IN ───────────────────────────────────────────────────────────
        if st.session_state.auth_tab == "login":
            st.markdown(
                '<div class="card"><h3>Sign In</h3>'
                '<p style="color:#737373;font-size:.85rem">Access your account to continue.</p></div>',
                unsafe_allow_html=True,
            )
            with st.form("login_engine_form", clear_on_submit=False):
                l_user   = st.text_input("Username", key="l_user")
                l_pass   = st.text_input("Password", type="password", key="l_pass")
                # FIX #5: remember me checkbox wired to cookie
                remember = st.checkbox("Remember me on this device", key="remember_me_chk")
                login_submitted = st.form_submit_button("Sign In →", width="stretch")

                if login_submitted:
                    res = db.verify_user(l_user.strip(), l_pass)
                    if res["success"]:
                        st.session_state.logged_in   = True
                        st.session_state.user_id     = res["user_id"]
                        st.session_state.username    = l_user.strip()
                        st.session_state.region      = res["region"]
                        st.session_state.trust_score = res.get("trust_score", 10)
                        st.session_state.user_type   = res.get("user_type", "Personal")

                        # FIX #5: set cookie as string ID when "remember me" ticked
                        if remember:
                            controller.set("ematch_user", str(res["user_id"]))

                        st.session_state.current_page = (
                            "Company Marketplace"
                            if st.session_state.user_type == "Company"
                            else "Marketplace"
                        )
                        st.rerun()
                    elif res.get("error") == "unverified":
                        st.session_state["pending_verification_user_id"] = res["user_id"]
                        st.session_state["pending_username"] = l_user.strip()
                        st.warning("⚠️ Your account email is unverified. Redirecting…")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        # FIX #8: friendly error message
                        st.error(f"❌ {res['error']}")

        # ── REGISTER ──────────────────────────────────────────────────────────
        else:
            st.markdown(
                '<div class="card"><h3>Create Account</h3>'
                '<p style="color:#737373;font-size:.85rem">Join the E-match community.</p></div>',
                unsafe_allow_html=True,
            )

            st.markdown("#### Choose Your Account Type")
            t1, t2 = st.columns(2)
            with t1:
                if st.button(
                    "👤 Personal User\n\nIndividuals sharing or trading items in the community.",
                    use_container_width=True,
                    type="primary" if st.session_state.reg_type == "Personal" else "secondary",
                    key="reg_type_personal",
                ):
                    st.session_state.reg_type = "Personal"; st.rerun()
            with t2:
                if st.button(
                    "🏢 Company User\n\nBusinesses managing near-expiry inventory and bulk listings.",
                    use_container_width=True,
                    type="primary" if st.session_state.reg_type == "Company" else "secondary",
                    key="reg_type_company",
                ):
                    st.session_state.reg_type = "Company"; st.rerun()

            st.markdown(
                f"**Selected:** {'👤 Personal Account' if st.session_state.reg_type=='Personal' else '🏢 Company Account'}"
            )
            st.markdown("---")

            r_user  = st.text_input("Username *",       key="r_user")
            r_email = st.text_input("Email *",          key="r_email")
            r_pass  = st.text_input("Password *",       type="password", key="r_pass")
            # ── CHANGED: phone is now mandatory (label has *)
            r_phone = st.text_input("Phone Number *",   placeholder="+60 12-345 6789", key="r_phone")
            r_reg   = st.selectbox("Region *", [
                "Selangor","Kuala Lumpur","Penang","Johor",
                "Melaka","Sabah","Sarawak","Kedah","Kelantan",
                "Negeri Sembilan","Pahang","Perak","Perlis","Terengganu"
            ])

            r_company_name = r_supervisor = r_address = None
            if st.session_state.reg_type == "Company":
                st.markdown("#### Company Details")
                r_company_name = st.text_input("Company Name *",   key="r_company_name")
                r_supervisor   = st.text_input("Supervisor Name",  key="r_supervisor")
                r_address      = st.text_area("Company Address",   key="r_address", height=80)

            if st.button("Create My Account →", width="stretch"):
                errors = []

                if not r_user or not r_email or not r_pass:
                    errors.append("Please fill in all required fields (username, email, password).")

                elif "@" not in r_email or "." not in r_email:
                    errors.append("Please enter a valid email address.")

                if not r_phone or not r_phone.strip():
                    errors.append("Phone number is required.")

                # NEW: Company name validation
                if (
                    st.session_state.reg_type == "Company"
                    and (not r_company_name or not r_company_name.strip())
                ):
                    errors.append("Company name is required.")
                if errors:
                    for e in errors:
                        st.error(f"❌ {e}")
                else:
                    res = db.add_user(
                        username=r_user.strip(), password=r_pass, region=r_reg,
                        user_type=st.session_state.reg_type, email=r_email.strip(),
                        phone_number=r_phone.strip() if r_phone else None,
                        company_name=r_company_name.strip() if r_company_name else None,
                        supervisor_name=r_supervisor.strip() if r_supervisor else None,
                        address=r_address.strip() if r_address else None,
                    )
                    if res["success"]:
                        with st.spinner("Dispatching authorization code to your email…"):
                            mail_res = send_verification_otp(r_email.strip())
                        if mail_res["success"]:
                            db.save_verification_code(res["user_id"], mail_res["otp"])
                            st.session_state["pending_verification_user_id"] = res["user_id"]
                            st.session_state["pending_username"] = r_user.strip()
                            st.success("📩 Account created! Check your email for the OTP.")
                            time.sleep(1.0)
                            st.rerun()
                        else:
                            st.error(f"❌ SMTP error: {mail_res['error']}")
                    else:
                        st.error(f"❌ {res.get('error')}")

# ── LOGGED-IN PAGES ───────────────────────────────────────────────────────────
else:
    user_id   = st.session_state.get("user_id")
    user_type = st.session_state.get("user_type", "Personal")

    # ── TRANSACTION COMPLETE DIALOG (#6 balloons triggered in mycart/company_cart) ──
    # AFTER (fixed)
    if st.session_state.get("show_txn_complete_dialog"):
        _item_name = st.session_state.get("txn_complete_item", "your item")
        st.session_state.show_txn_complete_dialog = False  # clear BEFORE showing
        st.session_state.txn_complete_item = None
        show_transaction_complete_dialog(_item_name)

    # ── CART POPUP ────────────────────────────────────────────────────────────
    # AFTER (fixed)
    if st.session_state.get("show_cart_popup"):
        item_name = st.session_state.get("cart_popup_item", "Item")
        st.session_state.show_cart_popup = False  # clear BEFORE showing
        st.session_state.cart_popup_item = None

        @st.dialog("🛒 Item Added to Cart!")
        def cart_popup():
            st.success(f"✅ '{item_name}' has been added to your cart!")
            st.markdown("""
            <div style="padding:14px;border-radius:12px;background:#f0fdf4;
            border:1px solid #bbf7d0;margin-top:10px;">
                <p style="margin:0;color:#166534;font-weight:600;">
                    You can review it in the Cart section.
                </p>
            </div>""", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                cart_page = "Company Cart" if user_type == "Company" else "My Cart"
                if st.button("🧾 Go to My Cart", width="stretch", type="primary"):
                    st.session_state.current_page = cart_page
                    st.rerun()
            with col2:
                if st.button("Close", width="stretch"):
                    st.rerun()

        cart_popup()

    # ── LOGIN POPUP (once per session) ────────────────────────────────────────
    if "has_shown_popup" not in st.session_state:
        st.session_state["has_shown_popup"] = True

        try:
            notif_res = db.get_notifications(user_id)
            notifs    = notif_res.get("notifications", []) if isinstance(notif_res, dict) else notif_res
            unread_n  = [n for n in notifs if not n.get("is_read", True)]

            if unread_n:
                show_login_notifications(unread_n)

        except Exception:
            pass

    # ── BAN CHECK ─────────────────────────────────────────────────────────────
    user_status_data = db.get_user_by_id(user_id)
    if user_status_data and user_status_data.get("status") == "Banned":
        st.markdown("""
        <div style="background:#fee2e2;border:1px solid #fca5a5;padding:30px;
        border-radius:14px;margin-top:50px;text-align:center;">
            <h1 style="color:#dc2626;margin:0 0 10px 0;">❌ Access Denied</h1>
            <p style="color:#991b1b;margin:0 0 20px 0;">
                Your account has been <strong>Banned</strong> by an administrator.
            </p>
        </div>""", unsafe_allow_html=True)
        if st.button("🚪 Leave Platform", width="stretch"):
            try: controller.remove("ematch_user")
            except Exception: pass
            st.session_state.clear()
            st.rerun()
        st.stop()

    # ── Refresh page_key each render ─────────────────────────────────────────
    page_key = normalize_page(st.session_state.current_page)

    # ── NOTIFICATIONS helper (shared) ─────────────────────────────────────────
    def _render_notifications():
        header_style = (
            '<div class="co-header" style="background:linear-gradient(135deg,#1e3a5f,#0d6efd); border-radius: 14px 14px 0 0; padding: 32px 36px;">'
            '<h1 style="font-family:Fraunces,serif;color:#fff;font-size:2rem;margin:0 0 6px">🔔 Notifications</h1>'
            '<p style="color:rgba(255,255,255,.75);margin:0">Updates for your account</p></div>'
        ) if user_type == "Company" else (
            '<div class="page-header"><h1>🔔 Notifications</h1>'
            '<p>Requests and updates from the community</p></div>'
        )
        st.markdown(header_style, unsafe_allow_html=True)
        notif_res = db.get_notifications_with_unread_count(user_id)
        notifs    = notif_res.get("notifications", [])
        unread_count = notif_res.get("unread_count", 0)
        if not notifs:
            st.info("No notifications yet.")
            return
        col_hdr, col_btn = st.columns([3, 1])
        
        col_hdr.caption(f"{unread_count} unread notification(s)")
        if col_btn.button("✅ Mark all as read", width="stretch"):
            db.mark_notifications_read(user_id); st.rerun()
        for n in notifs:
            is_unread  = not n.get("is_read", True)
            card_class = "notif-item unread" if is_unread else "notif-item"
            dot        = "🟢 " if is_unread else ""
            created    = n.get("created_at")
            ts = created.strftime("%d %b %Y, %I:%M %p") if created else ""
            st.markdown(f"""
            <div class="{card_class}">
                <p class="notif-title">{dot}{n['title']}</p>
                <p class="notif-body">{n['body']}</p>
                <p class="notif-time">🕐 {ts}</p>
            </div>""", unsafe_allow_html=True)

    # ── PERSONAL PAGES ────────────────────────────────────────────────────────
    if user_type == "Personal":
        if page_key == "Marketplace":
            render_marketplace_page(db)

        elif page_key == "My Cart":
            render_cart_page(db)

        elif page_key == "Upload Item":
            render_upload_page(db)

        elif page_key == "My Items":
            render_my_items_page(
                db=db,
                user_id=user_id,
                get_transaction_status=get_transaction_status,
                _lt_badge=_lt_badge,
            )

        elif page_key == "Notifications":
            _render_notifications()

        elif page_key == "Trust & Safety":
            render_trust_safety_page(db, user_id)

        elif page_key == "Past Transactions":
            render_past_transaction_page(db, user_id)

        elif page_key == "Dashboard":
            render_dashboard_page(db)

    # ── COMPANY PAGES ─────────────────────────────────────────────────────────
    elif user_type == "Company":
        if page_key == "Company Marketplace":
            render_company_marketplace(db, user_id)

        elif page_key == "Company Cart":
            render_company_cart(db, user_id)

        elif page_key == "Upload Inventory":
            render_company_upload(db, user_id)

        elif page_key == "Company Inventory":
            render_company_inventory_page(db, user_id)

        elif page_key == "My Items":
            render_company_items(db, user_id)

        elif page_key == "Company Dashboard":
            render_company_dashboard(db, user_id)

        elif page_key == "Company Transactions":
            render_company_past_transactions(db, user_id)

        elif page_key == "Company Trust & Safety":
            render_trust_safety_page(db, user_id)

        elif page_key == "Notifications":
            _render_notifications()
