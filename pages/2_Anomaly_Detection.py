import os
import sys
import uuid
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import joblib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.db.models import engine
from src.models.feature_engineering import compute_velocity_features, classify_typology, FEATURE_COLUMNS
from src.ui.theme import apply_custom_css, render_header, render_metric_card, render_sidebar
from src.ui.auth import require_auth
from src.data.stream_service import stream_service

st.set_page_config(
    page_title="TraceX AI | Anomaly & Smurfing Detection",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_css()
require_auth()
render_sidebar()

render_header(
    title="AI Anomaly & Smurfing Detection",
    subtitle="Dual-signal surveillance combining transaction amounts and rolling velocity metrics",
    badge_text="ISOLATION FOREST v2",
    badge_type="crimson",
    icon="🚨"
)

# Model Loader
@st.cache_resource
def load_isolation_model():
    model_path = "models/isolation_forest.pkl"
    if os.path.exists(model_path):
        try:
            return joblib.load(model_path)
        except Exception as e:
            st.error(f"Error loading model: {e}")
            return None
    return None

model = load_isolation_model()

if not model:
    st.error("⚠️ Isolation Forest model not found! Please run `python src/models/train_model.py` first.")
    st.stop()

# Interactive Scan Parameters inside Expander
with st.expander("⚙️ Scan Configuration & Detection Filters", expanded=True):
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        scan_size = st.slider("Transaction Batch Size", min_value=500, max_value=10000, value=2500, step=500)
    with col_c2:
        scan_source = st.selectbox("Data Window", ["Latest Ingested Transactions (Real-Time)", "Historical Chronological"])
    with col_c3:
        min_risk_threshold = st.slider("Minimum Risk Score Filter (%)", min_value=0, max_value=90, value=50, step=5)

# Execute Scan Button & Logic
col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    run_scan = st.button("🔍 Scan for Anomalies", type="primary", use_container_width=True)

# Maintain scan results in session state so download and interactions don't reset state
if "scan_df" not in st.session_state:
    st.session_state.scan_df = None

if run_scan or st.session_state.scan_df is None:
    with st.spinner("Extracting transactions, computing velocity windows, and scoring with Isolation Forest..."):
        order_clause = "transaction_id DESC" if "Real-Time" in scan_source else "timestamp ASC"
        query = f"""
        SELECT transaction_id, timestamp, sender_bank, sender_account, 
               receiver_bank, receiver_account, amount_paid, payment_currency, 
               amount_received, receiving_currency, payment_format, is_laundering
        FROM transactions 
        ORDER BY {order_clause} 
        LIMIT {scan_size}
        """
        raw_df = pd.read_sql(query, engine)
        
        if raw_df.empty:
            st.warning("No transactions returned from database.")
            st.stop()
            
        # Calculate velocity features
        processed_df = compute_velocity_features(raw_df)
        
        # Scikit-learn Prediction
        X = processed_df[FEATURE_COLUMNS].astype(float)
        processed_df['anomaly_pred'] = model.predict(X)
        raw_scores = model.decision_function(X)
        processed_df['raw_score'] = raw_scores
        
        # Calibrated 0-100% Risk Score
        min_s, max_s = raw_scores.min(), raw_scores.max()
        if max_s > min_s:
            processed_df['risk_score'] = ((max_s - raw_scores) / (max_s - min_s)) * 100.0
        else:
            processed_df['risk_score'] = 50.0

        # Heuristic boost: high velocity bursts (>5 tx/hr) with structured amounts are escalated to high risk
        smurf_mask = (processed_df['velocity_1h'] >= 4) & (processed_df['amount_paid'] >= 5000)
        processed_df.loc[smurf_mask, 'anomaly_pred'] = -1
        processed_df.loc[smurf_mask, 'risk_score'] = np.maximum(processed_df.loc[smurf_mask, 'risk_score'], 85.0)

        # Classify typologies
        processed_df['typology'] = processed_df.apply(classify_typology, axis=1)
        
        st.session_state.scan_df = processed_df

df = st.session_state.scan_df

# Filter anomalies
flagged_all = df[df['anomaly_pred'] == -1].copy()
filtered_anomalies = flagged_all[flagged_all['risk_score'] >= min_risk_threshold].copy()
smurfing_cases = filtered_anomalies[filtered_anomalies['velocity_1h'] >= 4]

# Metric Cards Row
m1, m2, m3, m4 = st.columns(4)
with m1:
    render_metric_card(
        title="Transactions Scanned",
        value=f"{len(df):,}",
        subtext="Evaluated multi-dimensional vectors",
        icon="📊",
        accent="blue"
    )
with m2:
    render_metric_card(
        title="Anomalies Flagged",
        value=f"{len(filtered_anomalies):,}",
        subtext=f"{len(filtered_anomalies)/len(df)*100:.2f}% anomaly rate",
        icon="🚨",
        accent="crimson",
        badge="FLAGGED"
    )
with m3:
    render_metric_card(
        title="Smurfing Bursts",
        value=f"{len(smurfing_cases):,}",
        subtext="High velocity structuring clusters",
        icon="⚡",
        accent="amber",
        badge="HIGH VELOCITY"
    )
with m4:
    total_flagged_val = filtered_anomalies['amount_paid'].sum() if not filtered_anomalies.empty else 0.0
    render_metric_card(
        title="Suspicious Exposure",
        value=f"${total_flagged_val/1e6:,.2f}M" if total_flagged_val >= 1e6 else f"${total_flagged_val:,.2f}",
        subtext="Total cumulative value under review",
        icon="💰",
        accent="purple"
    )

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# Scatter Visualization: Amount Paid vs 1-Hour Velocity
st.markdown("### 🔬 Multi-Dimensional Anomaly Analysis (Amount vs. Velocity)")
st.caption("Notice how Isolation Forest isolates smurfing clusters (high velocity) and capital flight (high amounts).")

chart_sample = df.sample(min(1500, len(df)), random_state=42).copy()
chart_sample['Detection Status'] = chart_sample['anomaly_pred'].apply(
    lambda x: "🚨 Suspicious Anomaly" if x == -1 else "Verified Normal"
)

fig_scatter = px.scatter(
    chart_sample,
    x='velocity_1h',
    y='amount_paid',
    color='Detection Status',
    color_discrete_map={
        "🚨 Suspicious Anomaly": "#ef4444",
        "Verified Normal": "#3b82f6"
    },
    hover_data=['sender_account', 'receiver_account', 'velocity_24h', 'typology'],
    labels={'velocity_1h': 'Hourly Velocity (Tx count / 1h)', 'amount_paid': 'Amount Paid ($)'},
    log_y=True
)

fig_scatter.update_layout(
    paper_bgcolor='#111827',
    plot_bgcolor='#111827',
    font=dict(color='#cbd5e1', family='Plus Jakarta Sans'),
    margin=dict(l=40, r=30, t=20, b=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# SAR Export Section (Suspicious Activity Report)
st.markdown("### 📋 Regulatory SAR Filing Center (Suspicious Activity Report Export)")
st.markdown("Generate FinCEN-compliant regulatory SAR packages for compliance review and download.")

if filtered_anomalies.empty:
    st.info("✅ No anomalies matching the selected filters. Adjust the risk threshold or scan parameters above.")
else:
    # Build regulatory SAR DataFrame
    def generate_sar_narrative(row):
        amt = float(row.get('amount_paid', 0.0))
        v1 = int(row.get('velocity_1h', 1))
        v24 = int(row.get('velocity_24h', 1))
        sender = row.get('sender_account', 'Unknown')
        typology = row.get('typology', 'General Anomaly')
        
        if "Smurfing" in typology or v1 >= 4:
            return (f"Suspicious activity detected: Account {sender} initiated {v1} rapid transfers within 1 hour "
                    f"({v24} within 24 hours) totaling ${amt:,.2f}. Transfer amounts were structured "
                    f"below currency transaction reporting (CTR) thresholds, exhibiting classic smurfing layering typology.")
        elif "Capital Flight" in typology or amt >= 100000:
            return (f"High-value anomaly: Account {sender} transferred an exceptional outlier amount of ${amt:,.2f}, "
                    f"deviating significantly from institutional baseline volume.")
        else:
            return (f"Transaction flagged by Isolation Forest: Account {sender} exhibited anomalous behavior "
                    f"with risk score of {row.get('risk_score', 0):.1f}% and pattern classification '{typology}'.")

    sar_df = filtered_anomalies.copy()
    sar_df['SAR_Reference_ID'] = [f"SAR-2026-{uuid.uuid4().hex[:8].upper()}" for _ in range(len(sar_df))]
    sar_df['Filing_Date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sar_df['Narrative_Summary'] = sar_df.apply(generate_sar_narrative, axis=1)

    export_columns = [
        'SAR_Reference_ID', 'Filing_Date', 'transaction_id', 'timestamp',
        'sender_bank', 'sender_account', 'receiver_bank', 'receiver_account',
        'amount_paid', 'payment_currency', 'payment_format',
        'velocity_1h', 'velocity_24h', 'risk_score', 'typology', 'Narrative_Summary'
    ]
    sar_export = sar_df[export_columns].rename(columns={
        'transaction_id': 'Transaction_ID',
        'timestamp': 'Transaction_Timestamp',
        'sender_bank': 'Sender_Bank_ID',
        'sender_account': 'Sender_Account_ID',
        'receiver_bank': 'Receiver_Bank_ID',
        'receiver_account': 'Receiver_Account_ID',
        'amount_paid': 'Amount_USD',
        'payment_currency': 'Currency',
        'payment_format': 'Channel',
        'velocity_1h': 'Velocity_1h_Count',
        'velocity_24h': 'Velocity_24h_Count',
        'risk_score': 'Risk_Score_Pct',
        'typology': 'Laundering_Typology'
    })

    # SAR Download Action Bar
    csv_bytes = sar_export.to_csv(index=False).encode('utf-8')
    filename = f"SAR_Suspicious_Activity_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    col_sar_action, col_sar_stats = st.columns([2, 3])
    with col_sar_action:
        st.download_button(
            label="📥 Export Flagged Anomalies as SAR CSV",
            data=csv_bytes,
            file_name=filename,
            mime="text/csv",
            type="primary",
            use_container_width=True
        )
    with col_sar_stats:
        st.markdown(f"""
        <div style="font-size:0.86rem; color:#94a3b8; padding-top:0.4rem;">
            Ready to export <b>{len(sar_export):,}</b> flagged cases | File: <code>{filename}</code>
        </div>
        """, unsafe_allow_html=True)

    # Preview SAR Records
    st.markdown("#### 📑 SAR Filing Preview & Case Review")
    
    preview_df = sar_df.copy()
    preview_df['Amount'] = preview_df['amount_paid'].apply(lambda x: f"${float(x):,.2f}")
    preview_df['Risk'] = preview_df['risk_score'].apply(lambda x: f"{x:.1f}%")
    preview_df['Velocity (1h)'] = preview_df['velocity_1h'].astype(int)
    preview_df['Velocity (24h)'] = preview_df['velocity_24h'].astype(int)

    st.dataframe(
        preview_df[[
            'SAR_Reference_ID', 'transaction_id', 'sender_account', 'receiver_account',
            'Amount', 'Velocity (1h)', 'Velocity (24h)', 'Risk', 'typology'
        ]].rename(columns={
            'SAR_Reference_ID': 'SAR Ref',
            'transaction_id': 'TX ID',
            'sender_account': 'Sender Account',
            'receiver_account': 'Receiver Account',
            'typology': 'Classified Typology'
        }),
        use_container_width=True,
        hide_index=True
    )

    # Expanders for top flagged accounts
    st.markdown("#### 🔎 Top High-Risk Case Investigations")
    top_cases = sar_df.sort_values(by='risk_score', ascending=False).head(5)
    for idx, case in top_cases.iterrows():
        with st.expander(f"Case {case['SAR_Reference_ID']} — Sender {case['sender_account']} (${float(case['amount_paid']):,.2f} | Risk: {case['risk_score']:.1f}%)"):
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.write(f"**Transaction ID:** `{case['transaction_id']}`")
                st.write(f"**Sender Account:** `{case['sender_account']}` (Bank {case['sender_bank']})")
                st.write(f"**Receiver Account:** `{case['receiver_account']}` (Bank {case['receiver_bank']})")
                st.write(f"**Timestamp:** `{case['timestamp']}`")
            with col_d2:
                st.write(f"**1-Hour Velocity:** `{int(case['velocity_1h'])} transfers`")
                st.write(f"**24-Hour Velocity:** `{int(case['velocity_24h'])} transfers`")
                st.write(f"**Typology:** `{case['typology']}`")
                st.write(f"**Channel:** `{case['payment_format']}` ({case['payment_currency']})")
            st.markdown(f"**Regulatory Narrative:**\n> {case['Narrative_Summary']}")