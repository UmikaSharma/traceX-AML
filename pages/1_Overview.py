import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine

from src.db.models import engine
from src.ui.theme import apply_custom_css, render_header, render_metric_card, render_sidebar
from src.ui.auth import require_auth
from src.data.stream_service import stream_service

st.set_page_config(
    page_title="TraceX AI | Analytics & Overview",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_css()
require_auth()
render_sidebar()

render_header(
    title="Portfolio & Risk Analytics",
    subtitle="Macro telemetry, channel distribution, and high-velocity account surveillance",
    badge_text="TELEMETRY ACTIVE",
    badge_type="blue",
    icon="📊"
)

# Fetch portfolio summary sample
@st.cache_data(ttl=60)
def load_overview_analytics():
    query = """
    SELECT payment_format, payment_currency, amount_paid, is_laundering, timestamp
    FROM transactions 
    LIMIT 25000
    """
    df = pd.read_sql(query, engine)
    return df

@st.cache_data(ttl=60)
def load_top_velocity_senders():
    query = """
    SELECT sender_account, COUNT(*) as tx_count, SUM(amount_paid) as total_volume,
           MAX(timestamp) as last_seen
    FROM transactions 
    GROUP BY sender_account 
    ORDER BY tx_count DESC 
    LIMIT 10
    """
    return pd.read_sql(query, engine)

df_sample = load_overview_analytics()
top_senders = load_top_velocity_senders()

# Metric Cards Row
c1, c2, c3, c4 = st.columns(4)

with c1:
    avg_amt = df_sample['amount_paid'].mean() if not df_sample.empty else 0.0
    render_metric_card(
        title="Avg Transaction Size",
        value=f"${avg_amt:,.2f}",
        subtext="Sample baseline average",
        icon="💰",
        accent="blue"
    )

with c2:
    total_vol = df_sample['amount_paid'].sum() if not df_sample.empty else 0.0
    render_metric_card(
        title="Sample Volume",
        value=f"${total_vol/1e6:,.1f}M",
        subtext="25,000 batch window",
        icon="📈",
        accent="emerald"
    )

with c3:
    laundering_pct = (df_sample['is_laundering'].sum() / len(df_sample) * 100) if not df_sample.empty else 0.0
    render_metric_card(
        title="Known Illicit Ratio",
        value=f"{laundering_pct:.2f}%",
        subtext="Confirmed suspicious markers",
        icon="🚨",
        accent="crimson"
    )

with c4:
    dominant_format = df_sample['payment_format'].mode()[0] if not df_sample.empty else "N/A"
    render_metric_card(
        title="Primary Channel",
        value=str(dominant_format),
        subtext="High-frequency rail",
        icon="🏦",
        accent="purple"
    )

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# Charts Section
col_chart1, col_chart2 = st.columns(2)

dark_layout = dict(
    paper_bgcolor='#111827',
    plot_bgcolor='#111827',
    font=dict(color='#cbd5e1', family='Plus Jakarta Sans'),
    margin=dict(l=30, r=30, t=40, b=30)
)

with col_chart1:
    with st.container():
        st.markdown("#### 💳 Volume by Payment Channel")
        format_counts = df_sample.groupby('payment_format')['amount_paid'].agg(['count', 'sum']).reset_index()
        fig_bar = px.bar(
            format_counts,
            x='payment_format',
            y='count',
            color='payment_format',
            color_discrete_sequence=['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4'],
            labels={'payment_format': 'Channel', 'count': 'Transaction Count'}
        )
        fig_bar.update_layout(**dark_layout, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

with col_chart2:
    with st.container():
        st.markdown("#### 💱 Currency Distribution")
        curr_counts = df_sample['payment_currency'].value_counts().reset_index()
        curr_counts.columns = ['Currency', 'Count']
        fig_pie = px.pie(
            curr_counts,
            names='Currency',
            values='Count',
            color_discrete_sequence=['#3b82f6', '#6366f1', '#10b981', '#f59e0b', '#ec4899', '#14b8a6'],
            hole=0.45
        )
        fig_pie.update_layout(**dark_layout)
        st.plotly_chart(fig_pie, use_container_width=True)

# High-Velocity Accounts Surveillance
st.markdown("### ⚡ High-Velocity Sender Surveillance (Top Burst Accounts)")
st.caption("Accounts generating anomalous transaction frequencies — high smurfing risk candidates.")

if not top_senders.empty:
    top_senders_display = top_senders.copy()
    top_senders_display['total_volume'] = top_senders_display['total_volume'].apply(lambda x: f"${float(x):,.2f}")
    top_senders_display['tx_count'] = top_senders_display['tx_count'].apply(lambda x: f"{int(x):,} txs")
    top_senders_display = top_senders_display.rename(columns={
        'sender_account': 'Monitored Sender Account',
        'tx_count': 'Total Transfers Initiated',
        'total_volume': 'Cumulative Value',
        'last_seen': 'Last Timestamp'
    })
    st.dataframe(top_senders_display, use_container_width=True, hide_index=True)
