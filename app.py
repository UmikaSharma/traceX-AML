import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from sqlalchemy import create_engine

from src.db.models import engine
from src.ui.theme import apply_custom_css, render_header, render_metric_card, render_sidebar
from src.ui.auth import render_login_gate
from src.data.stream_service import stream_service

st.set_page_config(
    page_title="TraceX AI | Executive AML Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_css()

# Unified Authentication Gate: locks multipage dashboard unless authorized
render_login_gate()

render_sidebar()

render_header(
    title="TraceX Sentinel — Executive AML Intelligence",
    subtitle="Next-generation Anti-Money Laundering monitoring, velocity anomaly detection & graph analytics",
    badge_text="LIVE PRODUCTION",
    badge_type="emerald",
    icon="🛡️"
)

# Helper function with short cache
def get_db_stats():
    with engine.connect() as conn:
        acc_count = pd.read_sql("SELECT COUNT(*) FROM accounts", conn).iloc[0, 0]
        tx_count = pd.read_sql("SELECT COUNT(*) FROM transactions", conn).iloc[0, 0]
    return acc_count, tx_count

# Telemetry metrics fragment that can auto-refresh
@st.fragment(run_every=4 if stream_service.is_running() else None)
def render_live_telemetry():
    acc_count, tx_count = get_db_stats()
    stream_stats = stream_service.get_stats()
    is_streaming = stream_service.is_running()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card(
            title="Monitored Accounts",
            value=f"{acc_count:,}",
            subtext="Global institutional nodes",
            icon="🏦",
            accent="blue"
        )
    with col2:
        render_metric_card(
            title="Total Transactions",
            value=f"{tx_count:,}",
            subtext="Ingested in PostgreSQL",
            icon="💳",
            accent="emerald"
        )
    with col3:
        render_metric_card(
            title="Smurfing Bursts Injected",
            value=f"{stream_stats.get('smurfing_bursts', 0):,}",
            subtext="High-frequency mule attacks",
            icon="⚡",
            accent="amber"
        )
    with col4:
        stream_label = "STREAMING (LIVE)" if is_streaming else "STANDBY"
        stream_color = "crimson" if is_streaming else "purple"
        render_metric_card(
            title="Real-Time Telemetry",
            value=stream_label,
            subtext=f"{stream_stats.get('total_ingested', 0):,} stream txs ingested",
            icon="📡",
            accent=stream_color
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Live feed of latest transactions
    st.markdown("### ⚡ Live Transaction Stream Feed")
    st.caption("Latest transactions ingested into PostgreSQL database in real-time.")

    query = """
    SELECT transaction_id, timestamp, sender_account, receiver_account, 
           amount_paid, payment_currency, payment_format, is_laundering
    FROM transactions 
    ORDER BY transaction_id DESC 
    LIMIT 10
    """
    recent_df = pd.read_sql(query, engine)
    
    if not recent_df.empty:
        # Format columns for crisp SaaS presentation
        display_df = recent_df.copy()
        display_df['amount_paid'] = display_df['amount_paid'].apply(lambda x: f"${float(x):,.2f}")
        display_df['Status'] = display_df['is_laundering'].apply(
            lambda x: "🚨 Suspicious" if x == 1 else "✅ Verified"
        )
        display_df = display_df.rename(columns={
            'transaction_id': 'TX ID',
            'timestamp': 'Timestamp',
            'sender_account': 'Sender Account',
            'receiver_account': 'Receiver Account',
            'amount_paid': 'Amount',
            'payment_currency': 'Currency',
            'payment_format': 'Channel'
        })
        
        st.dataframe(
            display_df[['TX ID', 'Timestamp', 'Sender Account', 'Receiver Account', 'Amount', 'Currency', 'Channel', 'Status']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No transaction data available.")

render_live_telemetry()

st.divider()

# Core Capabilities & Quick Actions
st.markdown("### 🚀 TraceX Core Investigation Modules")

col_a, col_b = st.columns(2)

with col_a:
    with st.container():
        st.markdown("""
        <div class="tracex-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h4 style="margin:0; color:#60a5fa;">🚨 AI Anomaly & Smurfing Detection</h4>
                <span class="tracex-badge badge-blue">ISOLATION FOREST v2</span>
            </div>
            <p style="color:#94a3b8; font-size:0.88rem; margin-top:0.6rem;">
                Advanced ML engine scanning both <b>transaction amounts</b> and <b>rolling velocity</b> (1h/24h frequency) to uncover structuring, rapid mule bursts, and smurfing rings.
            </p>
            <ul style="color:#cbd5e1; font-size:0.84rem; padding-left:1.2rem;">
                <li>Real-time isolation score & calibrated risk rating (0-100%)</li>
                <li>One-click regulatory <b>Suspicious Activity Report (SAR) CSV export</b></li>
                <li>Smurfing typology classification</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👉 Launch Anomaly Detection", key="nav_anomaly", use_container_width=True, type="primary"):
            st.switch_page("pages/2_Anomaly_Detection.py")

with col_b:
    with st.container():
        st.markdown("""
        <div class="tracex-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h4 style="margin:0; color:#34d399;">🕸️ AI Graph Network Investigator</h4>
                <span class="tracex-badge badge-emerald">GRAPH TOPOLOGY</span>
            </div>
            <p style="color:#94a3b8; font-size:0.88rem; margin-top:0.6rem;">
                Interactive directional graph powered by NetworkX and Plotly. Visually isolates laundering hubs, layering cycles, fan-out disbursement trees, and high-degree mules.
            </p>
            <ul style="color:#cbd5e1; font-size:0.84rem; padding-left:1.2rem;">
                <li>Heat-mapped node degree visualization</li>
                <li>Mule account connectivity drilldown</li>
                <li>Directional money trail tracing</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👉 Launch Network Investigator", key="nav_network", use_container_width=True, type="secondary"):
            st.switch_page("pages/3_Network_Investigation.py")

# Expanders for system architecture & FinCEN compliance
with st.expander("ℹ️ System Architecture & Smurfing Detection Methodology", expanded=False):
    st.markdown("""
    **How TraceX Detects Smurfing (Structuring):**
    - Smurfing is the fragmentation of illicit funds into sub-threshold transactions (e.g. $8,500-$9,900) to evade automatic $10,000 regulatory reporting.
    - Traditional amount-only models fail because the amounts themselves appear legitimate.
    - **TraceX Solution:** Calculates continuous rolling window velocities:
      - `velocity_1h`: Number of transfers initiated by the sender account within 60 minutes.
      - `velocity_24h`: Cumulative transactions initiated within 24 hours.
    - The retrained **Isolation Forest** evaluates amounts and velocity concurrently in multi-dimensional space, isolating burst outliers and flagging smurfs with high precision.
    """)