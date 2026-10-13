import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import plotly.graph_objects as go
import joblib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.db.models import engine
from src.models.feature_engineering import compute_velocity_features, FEATURE_COLUMNS, classify_typology
from src.ui.theme import apply_custom_css, render_header, render_metric_card, render_sidebar
from src.ui.auth import require_auth

st.set_page_config(
    page_title="TraceX AI | Network Investigator",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_css()
require_auth()
render_sidebar()

render_header(
    title="AI Network Graph Investigator",
    subtitle="Directional topological mapping of money trails, mule rings, and smurfing hubs",
    badge_text="GRAPH TOPOLOGY",
    badge_type="emerald",
    icon="🕸️"
)

# Load Isolation Forest Model
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
    st.error("⚠️ Isolation Forest model not found! Please run the training pipeline first.")
    st.stop()

# Investigation Controls Expander
with st.expander("⚙️ Network Investigation Parameters", expanded=True):
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        max_anomalies = st.slider("Max Anomalous Links to Map", min_value=15, max_value=300, value=75, step=15)
    with col_p2:
        query_batch = st.select_slider("Search Space (Transactions)", options=[2500, 5000, 10000, 25000], value=5000)
    with col_p3:
        focus_typology = st.selectbox("Focus Filter", ["All Flagged Links", "Smurfing & High-Velocity Only", "High Value Only"])

with st.spinner("Analyzing transaction topology and computing network graph..."):
    query = f"""
    SELECT transaction_id, timestamp, sender_account, receiver_account, 
           amount_paid, amount_received, payment_format, is_laundering
    FROM transactions 
    ORDER BY transaction_id DESC 
    LIMIT {query_batch}
    """
    df = pd.read_sql(query, engine)
    
    if df.empty:
        st.warning("No transactions found.")
        st.stop()

    df = compute_velocity_features(df)
    
    # Predict with retrained model
    X = df[FEATURE_COLUMNS].astype(float)
    df['anomaly_score'] = model.predict(X)
    df['typology'] = df.apply(classify_typology, axis=1)

    # Heuristic boost for smurfing
    smurf_mask = (df['velocity_1h'] >= 4) & (df['amount_paid'] >= 5000)
    df.loc[smurf_mask, 'anomaly_score'] = -1

    # Filter down to anomalous transactions
    flagged = df[df['anomaly_score'] == -1].copy()

    if focus_typology == "Smurfing & High-Velocity Only":
        flagged = flagged[flagged['velocity_1h'] >= 3]
    elif focus_typology == "High Value Only":
        flagged = flagged[flagged['amount_paid'] >= 50000]

    anomalies = flagged.head(max_anomalies)

if anomalies.empty:
    st.info("No anomalies found matching the current investigation filter. Try adjusting the filter or search space.")
    st.stop()

# Build NetworkX DiGraph
G = nx.from_pandas_edgelist(
    anomalies,
    source='sender_account',
    target='receiver_account',
    edge_attr=['amount_paid', 'payment_format'],
    create_using=nx.DiGraph()
)

# Compute graph metrics
num_nodes = G.number_of_nodes()
num_edges = G.number_of_edges()

# In-degree & Out-degree
in_degrees = dict(G.in_degree())
out_degrees = dict(G.out_degree())
total_degrees = {node: in_degrees.get(node, 0) + out_degrees.get(node, 0) for node in G.nodes()}

# Top hub accounts
hub_accounts = sorted(total_degrees.items(), key=lambda x: x[1], reverse=True)
top_hub_node, top_hub_deg = hub_accounts[0] if hub_accounts else ("None", 0)

# Metric Cards Row
g1, g2, g3, g4 = st.columns(4)
with g1:
    render_metric_card(
        title="Accounts in Graph",
        value=f"{num_nodes:,}",
        subtext="Unique counterparties mapped",
        icon="🏦",
        accent="blue"
    )
with g2:
    render_metric_card(
        title="Flagged Money Trails",
        value=f"{num_edges:,}",
        subtext="Anomalous directional transfers",
        icon="🔗",
        accent="crimson",
        badge="FLAGGED TRAILS"
    )
with g3:
    render_metric_card(
        title="Primary Hub Node",
        value=f"{top_hub_node[:8]}...",
        subtext=f"{top_hub_deg} connections detected",
        icon="⚡",
        accent="amber",
        badge="HIGH DEGREE"
    )
with g4:
    total_flow = anomalies['amount_paid'].sum()
    render_metric_card(
        title="Total Graph Exposure",
        value=f"${total_flow/1e6:,.2f}M" if total_flow >= 1e6 else f"${total_flow:,.2f}",
        subtext="Combined value across active trails",
        icon="💰",
        accent="purple"
    )

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# Generate Network Layout
pos = nx.spring_layout(G, k=0.35, iterations=50, seed=42)

# Edge coordinates
edge_x = []
edge_y = []
for edge in G.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

edges_trace = go.Scatter(
    x=edge_x,
    y=edge_y,
    line=dict(width=1.2, color='rgba(148, 163, 184, 0.35)'),
    hoverinfo='none',
    mode='lines'
)

# Node coordinates and tooltips
node_x = []
node_y = []
node_text = []
node_colors = []
node_sizes = []

for node in G.nodes():
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)
    
    in_deg = in_degrees.get(node, 0)
    out_deg = out_degrees.get(node, 0)
    tot_deg = in_deg + out_deg
    
    role = "Mule Fan-Out Source" if out_deg > in_deg else ("Aggregator / Fan-In" if in_deg > out_deg else "Hop Transit Node")
    
    node_text.append(
        f"<b>Account:</b> {node}<br>"
        f"<b>Role:</b> {role}<br>"
        f"<b>Transfers Out:</b> {out_deg}<br>"
        f"<b>Transfers In:</b> {in_deg}<br>"
        f"<b>Total Degree:</b> {tot_deg}"
    )
    node_colors.append(tot_deg)
    node_sizes.append(min(12 + tot_deg * 4, 32))

nodes_trace = go.Scatter(
    x=node_x,
    y=node_y,
    mode='markers+text',
    hoverinfo='text',
    text=[node[:5] if total_degrees[node] > 2 else "" for node in G.nodes()],
    textposition="top center",
    textfont=dict(size=9, color="#94a3b8"),
    hovertext=node_text,
    marker=dict(
        showscale=True,
        colorscale='Plasma',
        size=node_sizes,
        color=node_colors,
        colorbar=dict(
            title=dict(text="Node Connections", font=dict(color="#cbd5e1", size=11)),
            tickfont=dict(color="#94a3b8")
        ),
        line=dict(width=1.5, color='rgba(255, 255, 255, 0.4)')
    )
)

fig = go.Figure(
    data=[edges_trace, nodes_trace],
    layout=go.Layout(
        showlegend=False,
        hovermode='closest',
        margin=dict(b=10, l=10, r=10, t=10),
        plot_bgcolor='#0b0f19',
        paper_bgcolor='#0b0f19',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=620
    )
)

st.plotly_chart(fig, use_container_width=True)

# Forensic Insight Alert Box
st.markdown("""
<div style="background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.25); border-radius:10px; padding:0.9rem 1.2rem; margin-top:0.5rem; margin-bottom:1.2rem;">
    <strong style="color:#f87171;">🚨 Investigation Guidance:</strong>
    <span style="color:#cbd5e1; font-size:0.88rem; margin-left:0.5rem;">
        Focus on bright/yellow-orange nodes with large markers. Accounts with disproportionate <b>Transfers Out</b> (Out-Degree > 3) represent 
        <b>smurfing disbursement mules</b>, while those with high <b>Transfers In</b> are <b>laundering aggregation sinks</b>.
    </span>
</div>
""", unsafe_allow_html=True)

# Drilldown Account Inspector
with st.expander("🔎 Account Forensic Dossier Drilldown", expanded=False):
    all_graph_accounts = sorted(list(G.nodes()))
    selected_acc = st.selectbox("Select Account from Graph to Inspect:", all_graph_accounts)
    
    if selected_acc:
        out_txs = anomalies[anomalies['sender_account'] == selected_acc]
        in_txs = anomalies[anomalies['receiver_account'] == selected_acc]
        
        c_sub1, c_sub2 = st.columns(2)
        with c_sub1:
            st.markdown(f"**Disbursements Initiated (Outbound):** `{len(out_txs)}` transfers")
            if not out_txs.empty:
                st.dataframe(
                    out_txs[['transaction_id', 'receiver_account', 'amount_paid', 'payment_format', 'velocity_1h']].rename(
                        columns={'receiver_account': 'Counterparty', 'amount_paid': 'Amount ($)', 'velocity_1h': 'Velocity (1h)'}
                    ),
                    use_container_width=True,
                    hide_index=True
                )
        with c_sub2:
            st.markdown(f"**Deposits Received (Inbound):** `{len(in_txs)}` transfers")
            if not in_txs.empty:
                st.dataframe(
                    in_txs[['transaction_id', 'sender_account', 'amount_paid', 'payment_format', 'velocity_1h']].rename(
                        columns={'sender_account': 'Counterparty', 'amount_paid': 'Amount ($)', 'velocity_1h': 'Velocity (1h)'}
                    ),
                    use_container_width=True,
                    hide_index=True
                )
