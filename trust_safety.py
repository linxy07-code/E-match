# trust_safety.py
import streamlit as st
from datetime import datetime
import time


def render_trust_safety_page(db, user_id):

    user_type = st.session_state.get("user_type", "Personal")
    is_company = (user_type == "Company")

    # ── PAGE HEADER ───────────────────────────────────────────────────────────
    if is_company:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#1e3a5f 0%,#0d6efd 100%);
        border-radius:14px;padding:32px 36px;margin-bottom:28px;
        box-shadow:0 10px 30px rgba(0,0,0,.10);">
            <h1 style="font-family:'Fraunces',serif;font-size:2rem;color:#fff;margin:0 0 6px 0;">
                🛡️ Trust & Safety
            </h1>
            <p style="color:rgba(255,255,255,.75);font-size:.95rem;margin:0;">
                Your company's reputation on E-match
            </p>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="page-header">
            <h1>🛡️ Trust & Safety</h1>
            <p>Your reputation is your currency on E-match</p>
        </div>""", unsafe_allow_html=True)

    # ── 1. LIVE TRUST SCORE ───────────────────────────────────────────────────
    user_data = db.get_user_by_id(user_id)
    if user_data:
        st.session_state.trust_score = float(user_data.get("trust_score", 10.0))

    trust_score = st.session_state.get("trust_score", 10.0)
    trust_pct   = int((max(0.0, min(10.0, trust_score)) / 10.0) * 100)

    if trust_score >= 8.0:
        standing       = "Excellent Standing"
        standing_color = "#15803d" if not is_company else "#1d4ed8"
    elif trust_score >= 5.0:
        standing       = "Good Standing"
        standing_color = "#16a34a" if not is_company else "#2563eb"
    else:
        standing       = "Needs Improvement"
        standing_color = "#dc2626"

    bar_gradient = (
        "linear-gradient(90deg,#2563eb,#60a5fa)" if is_company
        else "linear-gradient(90deg,#22c55e,#2dd4bf)"
    )
    score_color   = "#1d4ed8" if is_company else "#15803d"
    bar_bg_color  = "#dbeafe" if is_company else "#dcfce7"
    card_border   = "#bfdbfe" if is_company else "#bbf7d0"
    rule_head_border = "#eff6ff" if is_company else "#dcfce7"

    col_score, col_rules = st.columns([1, 2])

    with col_score:
        st.markdown(f"""
        <div style="display:flex;flex-direction:column;align-items:center;
        padding:24px;background:white;border-radius:14px;
        border:1px solid {card_border};box-shadow:0 1px 3px rgba(0,0,0,.06);">
            <span style="font-size:2rem">{'🏢' if is_company else '⭐'}</span>
            <div style="margin-top:12px;text-align:center;">
                <span style="font-family:'Fraunces',serif;font-size:3.5rem;
                color:{score_color};font-weight:600;">{trust_score:.1f}</span>
                <span style="font-size:1.2rem;color:#737373;"> / 10</span>
            </div>
            <div style="font-weight:700;color:{standing_color};margin-top:5px;">
                {standing}
            </div>
            <div style="height:10px;border-radius:999px;background:{bar_bg_color};
            width:100%;overflow:hidden;margin-top:14px;">
                <div style="height:100%;background:{bar_gradient};
                width:{trust_pct}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_rules:
        rule_title = "📋 Company Trust Rules" if is_company else "📋 Score Rules"
        pos_color  = "#2563eb" if is_company else "#16a34a"
        st.markdown(f"""
        <div style="background:white;border-radius:14px;border:1px solid {card_border};
        box-shadow:0 1px 3px rgba(0,0,0,.06);padding:22px 24px;">
            <p style="font-weight:700;border-bottom:1px solid {rule_head_border};
            padding-bottom:10px;margin:0 0 8px 0;">{rule_title}</p>
        """, unsafe_allow_html=True)

        rules = [
            ("Successful match completed",     "+1.0", True),
            ("Item listed with accurate info",  "+0.5", True),
            ("Uploaded a clear item photo",     "+0.5", True),
            ("Fast response to requests",       "+0.5", True),
            ("Misconduct reported & verified",  "−3.0", False),
            ("Listing an expired item",         "−1.0", False),
            ("No-show for agreed pickup",       "−2.0", False),
        ]
        for rule, impact, pos in rules:
            color = pos_color if pos else "#dc2626"
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;
            padding:10px 0;border-bottom:1px solid {rule_head_border};">
                <span style="font-size:.875rem;color:#404040;">{rule}</span>
                <span style="color:{color};font-weight:700;">{impact}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 2. REPORT SECTION ─────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🚨 Report Misconduct")

    # FIX #9: show thank-you state if report was just submitted
    if st.session_state.get("report_submitted"):
        reported_name = st.session_state.get("report_submitted_username", "the user")
        st.markdown(f"""
        <div style="background:#f0fdf4;border:1px solid #86efac;border-left:4px solid #16a34a;
        border-radius:14px;padding:24px 28px;margin-bottom:16px;">
            <h3 style="font-family:'Fraunces',serif;color:#14532d;margin:0 0 12px 0;">
                🙏 Thank You for Your Report
            </h3>
            <p style="color:#166534;font-size:.95rem;margin:0 0 10px 0;">
                Your report against <strong>{reported_name}</strong> has been successfully submitted
                to the E-match moderation team.
            </p>
            <div style="background:#dcfce7;border-radius:10px;padding:14px 16px;margin-bottom:12px;">
                <p style="margin:0;color:#14532d;font-weight:600;font-size:.9rem;">
                    📋 What happens next:
                </p>
                <ul style="margin:8px 0 0 0;padding-left:18px;color:#166534;font-size:.85rem;line-height:2;">
                    <li>Our team will <strong>review the evidence</strong> within 1–3 business days</li>
                    <li>You will receive an <strong>email update</strong> once a decision is made</li>
                    <li>If the report is approved, the user's <strong>trust score will be adjusted</strong></li>
                    <li>Repeat violations may result in <strong>account suspension</strong></li>
                </ul>
            </div>
            <p style="color:#374151;font-size:.85rem;margin:0;">
                💡 <strong>Want to add more evidence?</strong> Reply to the confirmation email with
                screenshots or additional details to support your report.
            </p>
        </div>
        """, unsafe_allow_html=True)

        col_new, col_done = st.columns(2)
        with col_new:
            if st.button("📋 Submit Another Report", use_container_width=True):
                st.session_state.report_submitted = False
                st.session_state.report_submitted_username = None
                st.rerun()
        with col_done:
            dest = "Company Dashboard" if is_company else "Marketplace"
            if st.button("✅ Done", use_container_width=True):
                st.session_state.report_submitted = False
                st.session_state.current_page = dest
                st.rerun()
        return

    r1, r2 = st.columns(2)
    with r1:
        report_user_input = st.text_input(
            "Username to report",
            placeholder="Enter their username",
            key="rep_username"
        )
    with r2:
        if is_company:
            reasons = [
                "Fake listing",
                "Fraudulent activity",
                "Inappropriate behaviour",
                "No delivery / pickup issue",
                "Other",
            ]
        else:
            reasons = [
                "Misleading listing",
                "No-show for pickup",
                "Inappropriate behaviour",
                "Fraudulent activity",
                "Other",
            ]
        report_reason_input = st.selectbox("Reason", reasons, key="rep_reason")

    report_details_input = st.text_area(
        "Additional details (optional)",
        placeholder="Describe what happened… (screenshots and evidence can be emailed to support@ematch.my)",
        height=100,
        key="rep_details"
    )

    if st.button("Submit Report", key="btn_report", use_container_width=True):
        if not report_user_input.strip():
            st.warning("⚠️ Please provide a username to file this report.")
        else:
            report_payload = {
                "reporter_id":       user_id,
                "reported_username": report_user_input.strip(),
                "reason":            report_reason_input,
                "details":           report_details_input,
                "created_at":        datetime.now().isoformat()
            }
            db_res = db.create_misconduct_report(report_payload)
            if db_res.get("success"):
                # FIX #9: set thank-you state instead of rerunning immediately
                st.session_state.report_submitted = True
                st.session_state.report_submitted_username = report_user_input.strip()
                # clear form fields
                for k in ["rep_username", "rep_reason", "rep_details"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()
            else:
                st.error(f"❌ Could not submit report: {db_res.get('error', 'Unknown Error')}")