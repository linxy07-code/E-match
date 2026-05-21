import streamlit as st
from datetime import datetime
import time

def render_trust_safety_page(db, user_id):
    """
    Renders the Trust & Safety components, displays the live user score,
    and handles report logging to the Supabase database.
    """
    st.markdown("""
    <div class="page-header">
        <h1>🛡️ Trust & Safety</h1>
        <p>Your reputation is your currency on E-match</p>
    </div>""", unsafe_allow_html=True)

    # 1. Fetch live profile data from Supabase to keep score perfectly synced
    user_data = db.get_user_by_id(user_id)
    if user_data:
        # Update session state with live data from database edits
        st.session_state.trust_score = float(user_data.get("trust_score", 10.0))

    trust_score = st.session_state.get("trust_score", 10.0)
    
    # Ensure math bounds for the UI layer (0% to 100%)
    trust_pct = int((max(0.0, min(10.0, trust_score)) / 10.0) * 100)

    # 2. Dynamic Metric Layout (Score Ring & Rules)
    col_score, col_rules = st.columns([1, 2])

    with col_score:
        # Determine visual standing based on point values
        if trust_score >= 8.0:
            standing = "Excellent Standing"
        elif trust_score >= 5.0:
            standing = "Good Standing"
        else:
            standing = "Needs Improvement"
            
        st.markdown(f"""
        <div class="trust-ring-wrap">
            <span style="font-size:2rem">⭐</span>
            <div style="margin-top:12px;text-align:center">
                <span class="trust-score-num">{trust_score:.1f}</span>
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

    # 3. Report Misconduct Form Interface
    st.markdown("---")
    st.markdown("### 🚨 Report Misconduct")
    
    r1, r2 = st.columns(2)
    with r1:
        report_user_input = st.text_input("Username to report", placeholder="Enter their username", key="rep_username")
    with r2:
        report_reason_input = st.selectbox("Reason", [
            "Misleading listing", 
            "No-show for pickup",
            "Inappropriate behaviour", 
            "Fraudulent activity", 
            "Other"
        ], key="rep_reason")
        
    report_details_input = st.text_area(
        "Additional details (optional)",
        placeholder="Describe what happened…", 
        height=90, 
        key="rep_details"
    )
    
    if st.button("Submit Report", key="btn_report", use_container_width="stretch"):
        if not report_user_input.strip():
            st.warning("⚠️ Please provide a username to file this report.")
        else:
            # Build report structure to push to your Supabase 'reports' table
            # ── FIXED: Omitted 'status' to sync properly with create_misconduct_report column layout ──
            report_payload = {
                "reporter_id": user_id,
                "reported_username": report_user_input.strip(),
                "reason": report_reason_input,
                "details": report_details_input,
                "created_at": datetime.now().isoformat()
            }
            
            # Send payload into your central database engine wrapper
            db_res = db.create_misconduct_report(report_payload)
            
            if db_res.get("success"):
                st.success("✅ Report submitted to database. Our team will review the evidence and adjust values accordingly.")
                time.sleep(1.0)
                st.rerun()
            else:
                st.error(f"❌ Could not submit report: {db_res.get('error', 'Unknown Error')}")