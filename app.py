import streamlit as st
from datetime import datetime
from database import EcoMatchDB
from upload import render_upload_page
from marketplace import render_marketplace_page
import time
from streamlit_cookies_controller import CookieController

# ── INITIALIZATION ────────────────────────────────────────────────────────────
db         = EcoMatchDB()
controller = CookieController()

st.set_page_config(
    page_title="E-match | Resource Sharing Platform",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state defaults ────────────────────────────────────────────────────
for key, default in [
    ("logged_in",    False),
    ("current_page", "🛒  Marketplace"),
    ("username",     ""),
    ("auth_tab",     "login"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Cookie auto-login ─────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    cookies = controller.getAll()
    if not cookies:
        time.sleep(0.1)
        cookies = controller.getAll()

    remembered_user_id = cookies.get("ematch_user")
    if remembered_user_id:
        user_data = db.get_user_by_id(remembered_user_id)
        if user_data:
            st.session_state.logged_in   = True
            st.session_state.user_id     = remembered_user_id
            st.session_state.username    = user_data.get("username", "User")
            st.session_state.region      = user_data.get("region", "Unknown")
            st.session_state.trust_score = user_data.get("trust_score", 10)
            st.rerun()

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Fraunces:opsz,wght@9..144,300;9..144,500;9..144,600&display=swap');

:root {
    --green-50:#f0fdf4; --green-100:#dcfce7; --green-200:#bbf7d0;
    --green-300:#86efac; --green-500:#22c55e; --green-600:#16a34a;
    --green-700:#15803d; --green-800:#166534; --green-900:#14532d;
    --teal-400:#2dd4bf;  --teal-500:#14b8a6;  --teal-600:#0d9488;
    --neutral-50:#fafafa; --neutral-100:#f5f5f5; --neutral-200:#e5e5e5;
    --neutral-500:#737373; --neutral-700:#404040; --neutral-900:#171717;
    --shadow-sm:0 1px 3px rgba(0,0,0,.06),0 1px 2px rgba(0,0,0,.04);
    --shadow-md:0 4px 12px rgba(0,0,0,.08),0 2px 4px rgba(0,0,0,.04);
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
.sidebar-brand h2 { font-family:'Fraunces',serif !important; font-size:1.5rem !important; color:#fff !important; margin:0 !important; }

.page-header {
    background:linear-gradient(135deg,var(--green-700) 0%,var(--teal-600) 100%);
    border-radius:var(--radius); padding:32px 36px; margin-bottom:28px; box-shadow:var(--shadow-lg);
}
.page-header h1 { font-family:'Fraunces',serif !important; font-size:2rem !important; color:#fff !important; margin:0 0 6px !important; }
.page-header p  { color:rgba(255,255,255,.75) !important; font-size:.95rem; margin:0; }

.card { background:#fff; border-radius:var(--radius); border:1px solid var(--green-200); box-shadow:var(--shadow-sm); padding:22px 24px; margin-bottom:15px; }

/* My Items card */
.my-item-card {
    background:#fff; border-radius:var(--radius); border:1px solid var(--green-200);
    box-shadow:var(--shadow-sm); padding:20px 24px; margin-bottom:8px;
}
.my-item-title { font-family:'Fraunces',serif; font-size:1.2rem; font-weight:600; color:var(--green-900); margin:0 0 10px 0; }
.my-item-row   { font-size:.85rem; color:var(--neutral-700); margin:3px 0; }
.my-item-row strong { color:var(--green-700); }
.my-item-desc  { font-size:.85rem; color:#525252; margin-top:10px; padding-top:10px; border-top:1px solid #f0fdf4; line-height:1.5; }

/* Listing type badges */
.lt-badge {
    display:inline-block; font-size:.75rem; font-weight:700;
    padding:3px 10px; border-radius:999px; margin-left:6px;
}
.lt-free     { background:#dcfce7; color:#15803d; border:1px solid #bbf7d0; }
.lt-exchange { background:#ede9fe; color:#5b21b6; border:1px solid #c4b5fd; }
.lt-sell     { background:#fef9c3; color:#854d0e; border:1px solid #fde68a; }

/* Notification panel */
.notif-item {
    padding:12px 14px; border-radius:10px; margin-bottom:8px;
    border-left:3px solid var(--green-500); background:#f0fdf4;
}
.notif-item.unread { background:#dcfce7; border-left-color:var(--teal-500); }
.notif-title  { font-weight:600; font-size:.875rem; color:var(--green-900); margin:0 0 4px 0; }
.notif-body   { font-size:.8rem; color:#404040; margin:0; }
.notif-time   { font-size:.72rem; color:#737373; margin-top:4px; }

/* Metrics */
.metric-row { display:flex; gap:16px; margin-bottom:24px; flex-wrap:wrap; }
.metric-card {
    flex:1; min-width:180px; background:white; border:1px solid var(--green-200);
    border-radius:var(--radius); padding:20px 22px; box-shadow:var(--shadow-sm);
    position:relative; overflow:hidden;
}
.metric-card::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg,var(--green-500),var(--teal-400)); }
.metric-value { font-family:'Fraunces',serif; font-size:1.9rem; font-weight:600; color:var(--green-800); line-height:1; margin-bottom:4px; }
.metric-label { font-size:.78rem; color:var(--neutral-500); text-transform:uppercase; font-weight:600; }
.metric-delta { font-size:.75rem; margin-top:4px; }

/* Trust */
.trust-ring-wrap { display:flex; flex-direction:column; align-items:center; padding:24px; background:white; border-radius:14px; border:1px solid #bbf7d0; }
.trust-score-num { font-family:'Fraunces',serif; font-size:3.5rem; color:#15803d; font-weight:600; }
.trust-score-denom { font-size:1.2rem; color:#737373; }
.trust-label { font-weight:700; color:#16a34a; margin-top:5px; }
.trust-bar-bg { height:10px; border-radius:999px; background:#dcfce7; width:100%; overflow:hidden; }
.trust-bar-fill { height:100%; background:linear-gradient(90deg,#22c55e,#2dd4bf); }
.rule-row { display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid #f0fdf4; }
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


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand"><h2>🌿 E-match</h2>'
        "<p>Resource Organisation Management</p></div>",
        unsafe_allow_html=True,
    )

    if st.session_state.logged_in:
        user_id = st.session_state.get("user_id")

        # Unread notification count
        unread = db.count_unread_notifications(user_id)
        notif_label = f"🔔 Notifications ({unread} new)" if unread else "🔔 Notifications"

        st.markdown(f"""
        <div style="padding:10px 4px">
            <p style="font-size:.78rem;line-height:1.8;color:#86efac!important">
            🌍 Region: <strong style="color:#d1fae5!important">{st.session_state.get('region','—')}</strong><br>
            👤 User: <strong style="color:#d1fae5!important">{st.session_state.username}</strong><br>
            ⭐ Trust: <strong style="color:#d1fae5!important">{st.session_state.get('trust_score',10)} / 10</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

        NAV_OPTIONS = [
            "🛒  Marketplace",
            "📦  Upload Item",
            "🧾  My Items",
            "🛡️  Trust & Safety",
            "📊  Dashboard",
            f"🔔  Notifications" + (f" ({unread})" if unread else ""),
        ]

        # Keep current_page in sync if the label changed (unread count ticked)
        if st.session_state.current_page not in NAV_OPTIONS and "Notifications" in st.session_state.current_page:
            st.session_state.current_page = NAV_OPTIONS[5]

        selection = st.radio(
            "Navigation", NAV_OPTIONS,
            index=NAV_OPTIONS.index(st.session_state.current_page)
                  if st.session_state.current_page in NAV_OPTIONS else 0,
            label_visibility="collapsed",
        )
        if selection != st.session_state.current_page:
            st.session_state.current_page = selection
            st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            controller.remove("ematch_user")
            st.session_state.clear()
            st.rerun()


# ── MAIN ROUTER ───────────────────────────────────────────────────────────────
page_key = st.session_state.current_page.strip().split("  ", 1)[-1]
# strip notification count from page_key e.g. "Notifications (3)"
if page_key.startswith("🔔"):
    page_key = "Notifications"

if not st.session_state.logged_in:
    # ── AUTH ──────────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="page-header"><h1>Welcome to E-match</h1>'
        "<p>Malaysia's trusted platform for community resource sharing</p></div>",
        unsafe_allow_html=True,
    )
    _, center, _ = st.columns([1, 2, 1])
    with center:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔑  Sign In", use_container_width=True, key="tab_login"):
                st.session_state.auth_tab = "login"; st.rerun()
        with c2:
            if st.button("📝  Create Account", use_container_width=True, key="tab_reg"):
                st.session_state.auth_tab = "register"; st.rerun()

        if st.session_state.auth_tab == "login":
            st.markdown('<div class="card"><h3>Sign In</h3><p style="color:#737373;font-size:.85rem">Access your account to continue.</p></div>', unsafe_allow_html=True)
            l_user = st.text_input("Username", key="l_user")
            l_pass = st.text_input("Password", type="password", key="l_pass")
            remember = st.checkbox("Remember me on this device")
            if st.button("Sign In →", use_container_width=True, key="do_login"):
                res = db.verify_user(l_user.strip(), l_pass)
                if res["success"]:
                    st.session_state.logged_in   = True
                    st.session_state.user_id     = res["user_id"]
                    st.session_state.username    = l_user.strip()
                    st.session_state.region      = res["region"]
                    st.session_state.trust_score = res.get("trust_score", 10)
                    if remember:
                        controller.set("ematch_user", res["user_id"])
                    st.rerun()
                else:
                    st.error(f"❌ {res['error']}")
        else:
            st.markdown('<div class="card"><h3>Create Account</h3><p style="color:#737373;font-size:.85rem">Join the E-match community.</p></div>', unsafe_allow_html=True)
            r_user  = st.text_input("Username", key="r_user")
            r_email = st.text_input("Email",    key="r_email")
            r_pass  = st.text_input("Password", type="password", key="r_pass")
            r_reg   = st.selectbox("Region", ["Selangor", "Kuala Lumpur", "Penang", "Johor",
                                               "Melaka", "Sabah", "Sarawak"])
            if st.button("Create My Account →", use_container_width=True):
                res = db.add_user(r_user, r_pass, r_reg, "Personal")
                if res["success"]:
                    st.success("Account created! Please sign in.")
                    st.session_state.auth_tab = "login"
                    st.rerun()
                else:
                    st.error(f"❌ {res.get('error')}")

else:
    # ── LOGGED-IN PAGES ───────────────────────────────────────────────────────
    user_id = st.session_state.get("user_id")

    # ── Marketplace ───────────────────────────────────────────────────────────
    if page_key == "Marketplace":
        render_marketplace_page()

    # ── Upload Item ───────────────────────────────────────────────────────────
    elif page_key == "Upload Item":
        render_upload_page()

    # ── My Items ──────────────────────────────────────────────────────────────
    elif page_key == "My Items":
        st.markdown(
            '<div class="page-header"><h1>🧾 My Listings</h1>'
            "<p>All items you have posted to the marketplace</p></div>",
            unsafe_allow_html=True,
        )

        items_res = db.get_user_items(user_id)
        items = items_res.get("items", [])

        if not items:
            st.info("You haven't posted any items yet. Go to **Upload Item** to get started!")
        else:
            st.caption(f"{len(items)} active listing(s)")
            for item in items:
                lt    = item.get("listing_type") or "free"
                price = item.get("price")
                desc  = item.get("description") or ""
                exp   = item.get("expiry_date")

                badge = _lt_badge(lt, price)
                price_row = (
                    f"<div class='my-item-row'>💰 <strong>Price:</strong> RM {float(price):.2f}</div>"
                    if lt == "sell" and price else ""
                )
                expiry_row = (
                    f"<div class='my-item-row'>📅 <strong>Expires:</strong> {exp}</div>"
                    if exp else ""
                )
                desc_block = (
                    f"<p class='my-item-desc'>{desc}</p>" if desc else ""
                )

                img_col, info_col = st.columns([1, 2])

                with img_col:
                    if item.get("image_path"):
                        st.image(item["image_path"], use_container_width=True)
                    else:
                        st.markdown(
                            "<div style='height:140px;background:#f0fdf4;border-radius:10px;"
                            "display:flex;align-items:center;justify-content:center;"
                            "color:#86efac;font-size:2.5rem'>📦</div>",
                            unsafe_allow_html=True,
                        )

                with info_col:
                    st.markdown(f"""
<div class="my-item-card">
    <p class="my-item-title">{item['item_name']} {badge}</p>

    <div class="my-item-row">🏷️ <strong>Category:</strong> {item.get('category','—')}</div>
    <div class="my-item-row">📍 <strong>Region:</strong> {item.get('region','—')}</div>
    <div class="my-item-row">🔍 <strong>Condition:</strong> {item.get('condition','—')}</div>
    <div class="my-item-row">📦 <strong>Quantity:</strong> {item.get('quantity', 1)}</div>
    {price_row}
    {expiry_row}
    {desc_block}
</div>
""", unsafe_allow_html=True)

                    if st.button("🗑️ Delete listing", key=f"del_{item['item_id']}", use_container_width=True):
                        result = db.delete_item(item["item_id"], user_id)
                        if result["success"]:
                            st.success("Listing deleted.")
                            st.rerun()
                        else:
                            st.error(f"Could not delete: {result.get('error')}")

                st.divider()

    # ── Notifications ─────────────────────────────────────────────────────────
    elif page_key == "Notifications":
        st.markdown(
            '<div class="page-header"><h1>🔔 Notifications</h1>'
            "<p>Requests and updates from the community</p></div>",
            unsafe_allow_html=True,
        )

        notif_res = db.get_notifications(user_id)
        notifs    = notif_res.get("notifications", [])

        if not notifs:
            st.info("No notifications yet. When someone requests your item, you'll see it here.")
        else:
            col_hdr, col_btn = st.columns([3, 1])
            col_hdr.caption(f"{len(notifs)} notification(s)")
            if col_btn.button("✅ Mark all as read", use_container_width=True):
                db.mark_notifications_read(user_id)
                st.rerun()

            for n in notifs:
                is_unread  = not n.get("is_read", True)
                card_class = "notif-item unread" if is_unread else "notif-item"
                dot        = "🟢 " if is_unread else ""

                # Format timestamp
                created = n.get("created_at")
                if created:
                    try:
                        ts = created.strftime("%d %b %Y, %I:%M %p")
                    except Exception:
                        ts = str(created)
                else:
                    ts = ""

                st.markdown(f"""
<div class="{card_class}">
    <p class="notif-title">{dot}{n['title']}</p>
    <p class="notif-body">{n['body']}</p>
    <p class="notif-time">🕐 {ts}</p>
</div>
""", unsafe_allow_html=True)

    # ── Trust & Safety ────────────────────────────────────────────────────────
    elif page_key == "Trust & Safety":
        st.markdown("""
        <div class="page-header">
            <h1>🛡️ Trust & Safety</h1>
            <p>Your reputation is your currency on E-match</p>
        </div>""", unsafe_allow_html=True)

        trust_score = st.session_state.get("trust_score", 10)
        trust_pct   = int((trust_score / 10) * 100)
        col_score, col_rules = st.columns([1, 2])

        with col_score:
            standing = ("Excellent Standing" if trust_score >= 8
                        else "Good Standing" if trust_score >= 5
                        else "Needs Improvement")
            st.markdown(f"""
            <div class="trust-ring-wrap">
                <span style="font-size:2rem">⭐</span>
                <div style="margin-top:12px;text-align:center">
                    <span class="trust-score-num">{trust_score}</span>
                    <span class="trust-score-denom"> / 10</span>
                </div>
                <div class="trust-label">{standing}</div>
                <div class="trust-bar-bg" style="margin-top:14px">
                    <div class="trust-bar-fill" style="width:{trust_pct}%"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_rules:
            st.markdown("<div class='card'><p style='font-weight:700;border-bottom:1px solid #dcfce7;padding-bottom:10px'>📋 Score Rules</p>", unsafe_allow_html=True)
            rules = [
                ("Successful match completed",       "+1.0", True),
                ("Item listed with accurate info",   "+0.5", True),
                ("Uploaded a clear item photo",      "+0.5", True),
                ("Fast response to claim request",   "+0.5", True),
                ("Misconduct reported & verified",   "−3.0", False),
                ("Listing an expired item",          "−1.0", False),
                ("No-show for agreed pickup",        "−2.0", False),
            ]
            for rule, impact, pos in rules:
                cls = "rule-impact-pos" if pos else "rule-impact-neg"
                st.markdown(f"""
                <div class="rule-row">
                    <span style="font-size:.875rem;color:#404040">{rule}</span>
                    <span class="{cls}">{impact}</span>
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🚨 Report Misconduct")
        r1, r2 = st.columns(2)
        with r1:
            st.text_input("Username to report", placeholder="Enter their username")
        with r2:
            st.selectbox("Reason", ["Misleading listing", "No-show for pickup",
                                     "Inappropriate behaviour", "Fraudulent activity", "Other"])
        st.text_area("Additional details (optional)",
                     placeholder="Describe what happened…", height=90)
        if st.button("Submit Report", key="btn_report"):
            st.error("⚠️ Report submitted. Our team will review and adjust trust scores after verification.")

    # ── Dashboard ─────────────────────────────────────────────────────────────
    elif page_key == "Dashboard":
        st.markdown("""
        <div class="page-header">
            <h1>📊 Analytics Dashboard</h1>
            <p>Platform performance and regional activity overview</p>
        </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div class="metric-row">
            <div class="metric-card"><div class="metric-value">430</div><div class="metric-label">Total Matches</div><div class="metric-delta">↑ +12 this week</div></div>
            <div class="metric-card"><div class="metric-value">87</div><div class="metric-label">Active Listings</div><div class="metric-delta">↑ +5 today</div></div>
            <div class="metric-card"><div class="metric-value">1,240</div><div class="metric-label">Registered Users</div><div class="metric-delta">↑ +34 this month</div></div>
            <div class="metric-card"><div class="metric-value">14</div><div class="metric-label">Near Expiry</div><div class="metric-delta" style="color:#dc2626">⚠ Needs attention</div></div>
            <div class="metric-card"><div class="metric-value">9.4</div><div class="metric-label">Avg Trust Score</div><div class="metric-delta">↑ Excellent</div></div>
        </div>
        """, unsafe_allow_html=True)

        tab_a, tab_b = st.tabs(["📈  Monthly Trends", "🗺️  Regional Breakdown"])
        with tab_a:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("*Monthly Matches — 2025*")
                st.bar_chart({"Matches": [45,60,72,58,80,95,110,102,88,120,130,125]}, height=260)
            with c2:
                st.markdown("*Items Listed per Month — 2025*")
                st.bar_chart({"Items Listed": [30,48,55,42,67,78,92,85,70,105,112,99]}, height=260)
        with tab_b:
            c3, c4 = st.columns(2)
            with c3:
                st.markdown("*Matches by Region*")
                st.bar_chart({"Matches": [120,95,80,65,40]}, height=260)
                st.caption("Selangor · KL · Penang · Johor · Others")
            with c4:
                st.markdown("*Users by Region*")
                st.bar_chart({"Users": [420,380,210,150,80]}, height=260)
                st.caption("Selangor · KL · Penang · Johor · Others")

        st.markdown("---")
        st.markdown("### ⏳ Items Approaching Expiry")
        st.dataframe({
            "Item":      ["Canned Goods Bundle","Fresh Vegetables Pack","Baby Formula Tins","Bread Loaves"],
            "Region":    ["Penang","Selangor","KL","Johor"],
            "Posted By": ["Ahmad Fauzi","Nurul Ain","Mei Lin","Raj Kumar"],
            "Days Left": [3, 5, 6, 2],
            "Status":    ["🚨 Critical","⚠️ Warning","⚠️ Warning","🚨 Critical"],
        }, use_container_width=True, hide_index=True)