"""
TraceX AML - Unified Authentication & Session Gate
Locks the multipage dashboard and validates credentials (admin/admin123).
"""

import streamlit as st

def hide_sidebar_css():
    """Injects CSS to completely hide the sidebar and multipage navigation when unauthenticated."""
    st.markdown("""
    <style>
    [data-testid="stSidebar"], section[data-testid="stSidebar"], [data-testid="stSidebarNav"] {
        display: none !important;
    }
    button[data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

def require_auth():
    """
    Enforces authentication across pages in pages/.
    If user is not authenticated, redirects to app.py or stops execution.
    """
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        hide_sidebar_css()
        st.markdown("""
        <div style="text-align: center; padding: 4rem 1rem;">
            <div style="font-size: 3.5rem;">🔒</div>
            <h2 style="color: #f87171; margin-top: 0.5rem;">ACCESS RESTRICTED</h2>
            <p style="color: #94a3b8; font-size: 0.95rem; max-width: 480px; margin: 0 auto 1.5rem auto;">
                You must authenticate through the TraceX Security Gateway before accessing this surveillance module.
            </p>
        </div>
        """, unsafe_allow_html=True)
        try:
            st.switch_page("app.py")
        except Exception:
            pass
        st.stop()

def render_login_gate():
    """
    Renders the centered, dark glass-styled login screen at app.py.
    Returns True if user is authenticated; stops execution if not.
    """
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    # User is NOT authenticated: hide sidebar navigation completely
    hide_sidebar_css()

    # Center layout
    _, col_center, _ = st.columns([1, 1.6, 1])

    with col_center:
        st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

        # Prominent Blue Shield "TraceX" Logo Header
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="display: inline-flex; align-items: center; justify-content: center; width: 84px; height: 84px; border-radius: 20px; background: radial-gradient(circle, rgba(59, 130, 246, 0.25) 0%, rgba(37, 99, 235, 0.05) 70%); border: 1.5px solid rgba(59, 130, 246, 0.4); box-shadow: 0 0 35px rgba(59, 130, 246, 0.35); margin-bottom: 1rem;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    <path d="m9 12 2 2 4-4"/>
                </svg>
            </div>
            <h1 style="font-size: 2.3rem; font-weight: 800; letter-spacing: -0.03em; color: #f8fafc; margin: 0;">
                Trace<span style="color: #3b82f6;">X</span>
            </h1>
            <div style="font-size: 0.88rem; font-weight: 600; letter-spacing: 0.12em; color: #60a5fa; text-transform: uppercase; margin-top: 0.3rem;">
                AI-Powered AML Surveillance Gateway
            </div>
            <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.25rem;">
                Institutional Financial Crime & Anomaly Intelligence
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Dark Glass-Styled Login Box
        st.markdown("""
        <style>
        .login-glass-container {
            background: linear-gradient(145deg, rgba(19, 26, 42, 0.9) 0%, rgba(13, 18, 30, 0.98) 100%);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 16px;
            padding: 2rem 2.2rem;
            box-shadow: 0 15px 45px rgba(0, 0, 0, 0.65), 0 0 20px rgba(59, 130, 246, 0.15);
            backdrop-filter: blur(16px);
            margin-bottom: 1.5rem;
        }
        </style>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="login-glass-container">', unsafe_allow_html=True)
            
            st.markdown("""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.25rem;">
                <span style="font-weight:700; font-size:1.05rem; color:#f8fafc;">Authorized Sign-In</span>
                <span style="font-size:0.72rem; background:rgba(59,130,246,0.15); color:#60a5fa; border:1px solid rgba(59,130,246,0.3); padding:0.2rem 0.55rem; border-radius:999px; font-weight:700; text-transform:uppercase;">
                    FINCEN / BSA TIER 1
                </span>
            </div>
            """, unsafe_allow_html=True)

            with st.form("tracex_auth_form", clear_on_submit=False):
                username = st.text_input("Username", placeholder="Enter surveillance ID (e.g. admin)", key="input_user")
                password = st.text_input("Password", type="password", placeholder="Enter credentials", key="input_pass")
                st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
                submit = st.form_submit_button("Authenticate & Access Dashboard", type="primary", use_container_width=True)

                if submit:
                    if username == "admin" and password == "admin123":
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = "admin"
                        st.session_state["role"] = "Senior AML Officer"
                        st.success("✅ Credentials verified. Decrypting surveillance telemetry...")
                        st.rerun()
                    else:
                        st.error("❌ Authentication Failed: Invalid credentials. Incident logged to security audit trail.")

            st.markdown('</div>', unsafe_allow_html=True)

        # Strict Warnings at Bottom About Prohibited Unauthorized Access
        st.markdown("""
        <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 10px; padding: 1rem 1.25rem; font-size: 0.76rem; color: #cbd5e1; line-height: 1.55; text-align: left; margin-bottom: 2rem;">
            <div style="display: flex; align-items: center; gap: 0.4rem; color: #f87171; font-weight: 700; font-size: 0.8rem; margin-bottom: 0.4rem; letter-spacing: 0.04em; text-transform: uppercase;">
                <span>⚠️</span> RESTRICTED GOVERNMENT & FINANCIAL SYSTEM
            </div>
            <b>UNAUTHORIZED ACCESS PROHIBITED:</b> This system is restricted exclusively to authorized Anti-Money Laundering (AML) officers and compliance personnel. 
            Unauthorized attempts to access, inspect, or tamper with this dashboard are monitored, recorded, and subject to civil action and criminal prosecution under federal law (including 18 U.S.C. § 1030 and applicable Bank Secrecy Act / FinCEN statutes).
            <div style="color: #94a3b8; font-size: 0.72rem; margin-top: 0.5rem;">
                All IP addresses, hardware signatures, and failed authentication events are permanently logged in the PostgreSQL audit register.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Halt execution so dashboard content is never rendered when unauthenticated
    st.stop()
