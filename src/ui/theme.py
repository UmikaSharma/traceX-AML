"""
TraceX AML - UI Theme & Design System
Provides custom dark-mode CSS and reusable UI components for an enterprise SaaS dashboard.
"""

import streamlit as st
from datetime import datetime
from src.data.stream_service import stream_service

CUSTOM_CSS = """
<style>
/* Import Inter and JetBrains Mono fonts */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #f8fafc;
}

/* Background canvas */
.stApp {
    background-color: #0b0f19;
    background-image: 
        radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.08) 0px, transparent 50%),
        radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.06) 0px, transparent 50%),
        radial-gradient(at 50% 100%, rgba(16, 185, 129, 0.04) 0px, transparent 50%);
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: #0d121f !important;
    border-right: 1px solid rgba(255, 255, 255, 0.07);
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}

/* Polished Card Container */
.tracex-card {
    background: linear-gradient(135deg, rgba(19, 26, 42, 0.9) 0%, rgba(13, 18, 30, 0.95) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
    margin-bottom: 1.2rem;
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    backdrop-filter: blur(8px);
}

.tracex-card:hover {
    border-color: rgba(59, 130, 246, 0.35);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
}

/* Metric Card */
.tracex-metric-card {
    background: linear-gradient(145deg, rgba(20, 28, 46, 0.85) 0%, rgba(12, 17, 29, 0.95) 100%);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 14px;
    padding: 1.25rem 1.4rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.tracex-metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
}

.metric-accent-blue { border-top: 3px solid #3b82f6; }
.metric-accent-emerald { border-top: 3px solid #10b981; }
.metric-accent-amber { border-top: 3px solid #f59e0b; }
.metric-accent-crimson { border-top: 3px solid #ef4444; }
.metric-accent-purple { border-top: 3px solid #8b5cf6; }

.tracex-metric-title {
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #94a3b8;
    margin-bottom: 0.4rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.tracex-metric-value {
    font-size: 1.95rem;
    font-weight: 800;
    color: #f8fafc;
    line-height: 1.15;
    letter-spacing: -0.02em;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.tracex-metric-subtext {
    font-size: 0.8rem;
    color: #64748b;
    margin-top: 0.45rem;
    display: flex;
    align-items: center;
    gap: 0.35rem;
}

/* Badges */
.tracex-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.22rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.badge-blue {
    background: rgba(59, 130, 246, 0.15);
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.3);
}

.badge-emerald {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.badge-amber {
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

.badge-crimson {
    background: rgba(239, 68, 68, 0.18);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.35);
}

/* Streamlit Native Expander styling */
div[data-testid="stExpander"] {
    background: rgba(18, 24, 38, 0.75) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 10px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
    margin-bottom: 0.85rem;
}

div[data-testid="stExpander"]:hover {
    border-color: rgba(59, 130, 246, 0.25) !important;
}

/* Native buttons overhaul */
button[kind="primary"] {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.25rem !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3) !important;
    transition: all 0.2s ease !important;
}

button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5) !important;
    transform: translateY(-1px) !important;
}

button[kind="secondary"] {
    background: rgba(22, 30, 48, 0.8) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #e2e8f0 !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}

button[kind="secondary"]:hover {
    background: rgba(30, 41, 59, 0.95) !important;
    border-color: rgba(59, 130, 246, 0.3) !important;
    color: #60a5fa !important;
}

/* Page Header banner */
.tracex-hero-header {
    background: linear-gradient(135deg, rgba(23, 32, 54, 0.7) 0%, rgba(14, 20, 34, 0.9) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-left: 4px solid #3b82f6;
    border-radius: 12px;
    padding: 1.4rem 1.75rem;
    margin-bottom: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.tracex-hero-title {
    font-size: 1.6rem;
    font-weight: 800;
    color: #f8fafc;
    letter-spacing: -0.02em;
    margin: 0;
}

.tracex-hero-subtitle {
    font-size: 0.88rem;
    color: #94a3b8;
    margin-top: 0.3rem;
}

/* Live Pulse Indicator */
.pulse-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse-glow 2s infinite;
}

.pulse-green {
    background-color: #10b981;
    box-shadow: 0 0 8px #10b981;
}

.pulse-red {
    background-color: #ef4444;
    box-shadow: 0 0 8px #ef4444;
}

@keyframes pulse-glow {
    0% { opacity: 0.5; transform: scale(0.95); }
    50% { opacity: 1; transform: scale(1.15); }
    100% { opacity: 0.5; transform: scale(0.95); }
}

/* Monospace accounts */
.mono-acc {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.86rem;
    background: rgba(0, 0, 0, 0.25);
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.06);
}
</style>
"""

def apply_custom_css():
    """Injects custom enterprise CSS into the active Streamlit page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def render_header(title: str, subtitle: str, badge_text: str = "PRODUCTION", badge_type: str = "blue", icon: str = "🛡️"):
    """Renders a sleek top executive banner with status pill."""
    apply_custom_css()
    badge_class = f"badge-{badge_type}"
    st.markdown(f"""
    <div class="tracex-hero-header">
        <div>
            <div class="tracex-hero-title">{icon} {title}</div>
            <div class="tracex-hero-subtitle">{subtitle}</div>
        </div>
        <div>
            <span class="tracex-badge {badge_class}">{badge_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_metric_card(title: str, value: str, subtext: str = None, icon: str = "📊", accent: str = "blue", badge: str = None):
    """Renders an enterprise styled metric card with custom accent borders and typography."""
    badge_html = f'<span class="tracex-badge badge-{accent}">{badge}</span>' if badge else f'<span style="font-size:1.1rem;">{icon}</span>'
    subtext_html = f'<div class="tracex-metric-subtext">{subtext}</div>' if subtext else ''
    card_html = f"""
    <div class="tracex-metric-card metric-accent-{accent}">
        <div class="tracex-metric-title">
            <span>{title}</span>
            {badge_html}
        </div>
        <div class="tracex-metric-value">{value}</div>
        {subtext_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def render_sidebar():
    """Renders standard branding, live streaming simulation controls, and telemetry in the sidebar."""
    with st.sidebar:
        # Session authentication status & Log Out button
        if st.session_state.get("authenticated", False):
            username = st.session_state.get("username", "admin")
            role = st.session_state.get("role", "Senior AML Officer")
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 0.55rem 0.75rem; margin-bottom: 0.75rem; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-size: 0.8rem; font-weight: 700; color: #f8fafc;">👤 {username}</div>
                    <div style="font-size: 0.7rem; color: #60a5fa;">{role}</div>
                </div>
                <span class="tracex-badge badge-emerald" style="font-size: 0.65rem;">ACTIVE</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚪 Log Out", key="global_logout_btn", use_container_width=True, type="secondary"):
                if stream_service.is_running():
                    stream_service.stop()
                st.session_state.clear()
                st.session_state["authenticated"] = False
                st.rerun()

        st.markdown("""
        <div style="padding-bottom: 0.8rem; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 1rem;">
            <div style="display:flex; align-items:center; gap:0.6rem;">
                <div style="font-size:1.7rem;">🛡️</div>
                <div>
                    <div style="font-weight:800; font-size:1.25rem; letter-spacing:-0.02em; color:#f8fafc;">TRACEX AI</div>
                    <div style="font-size:0.75rem; color:#60a5fa; font-weight:600; letter-spacing:0.05em;">SENTINEL AML PLATFORM</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### ⚡ Live Stream Controller")
        st.caption("Simulate real-time transaction ingestion & attack patterns.")

        is_running = stream_service.is_running()
        stats = stream_service.get_stats()

        if is_running:
            st.markdown("""
            <div style="background:rgba(16,185,129,0.12); border:1px solid rgba(16,185,129,0.3); border-radius:8px; padding:0.6rem 0.8rem; margin-bottom:0.75rem;">
                <span class="pulse-dot pulse-green"></span>
                <strong style="color:#34d399; font-size:0.85rem;">STREAM ACTIVE</strong>
                <div style="font-size:0.75rem; color:#94a3b8; margin-top:0.25rem;">Live transactions streaming to PostgreSQL</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("⏹️ Pause Live Stream", use_container_width=True, key="btn_stop_stream"):
                stream_service.stop()
                st.rerun()
        else:
            st.markdown("""
            <div style="background:rgba(100,116,139,0.12); border:1px solid rgba(100,116,139,0.25); border-radius:8px; padding:0.6rem 0.8rem; margin-bottom:0.75rem;">
                <span style="color:#94a3b8; font-size:0.85rem;">⚪ STREAM IDLE</span>
                <div style="font-size:0.75rem; color:#64748b; margin-top:0.25rem;">Standing by for simulated ingestion</div>
            </div>
            """, unsafe_allow_html=True)
            rate = st.slider("Streaming Speed (sec/tx)", min_value=0.5, max_value=5.0, value=1.5, step=0.5, key="slider_stream_rate")
            if st.button("▶️ Start Live Stream", type="primary", use_container_width=True, key="btn_start_stream"):
                stream_service.start(rate_sec=rate)
                st.rerun()

        # On-Demand Smurfing Injection Trigger
        with st.expander("🚨 Attack Injection Lab", expanded=False):
            st.caption("Inject controlled laundering patterns to test AML velocity models.")
            burst_size = st.slider("Burst Transactions", min_value=4, max_value=16, value=8, key="slider_burst_size")
            struct_amt = st.number_input("Structured Amount ($)", min_value=1000.0, max_value=9999.0, value=8750.0, step=250.0, key="input_struct_amt")
            if st.button("⚡ Inject Smurfing Attack Now", use_container_width=True, key="btn_inject_burst"):
                with st.spinner("Injecting structured burst..."):
                    burst = stream_service.inject_burst(burst_size=burst_size, structured_amount=struct_amt)
                    st.toast(f"🚨 Smurfing Burst Injected! {len(burst)} TXs sent from mule {burst[0]['sender_account']}", icon="🚨")
                    st.rerun()

        # Telemetry info
        st.divider()
        st.markdown("### 📡 System Telemetry")
        st.markdown(f"""
        <div style="font-size:0.8rem; line-height:1.7; color:#94a3b8;">
            <div>🐘 <b>Database:</b> <span style="color:#34d399;">Connected</span> (PostgreSQL)</div>
            <div>🤖 <b>Model:</b> <span style="color:#60a5fa;">IF-v2 (Amounts + Velocity)</span></div>
            <div>⚡ <b>Stream Ingested:</b> <span style="color:#f8fafc; font-weight:600;">{stats.get('total_ingested', 0):,} txs</span></div>
            <div>⚠️ <b>Bursts Injected:</b> <span style="color:#fbbf24; font-weight:600;">{stats.get('smurfing_bursts', 0):,} attacks</span></div>
        </div>
        """, unsafe_allow_html=True)
