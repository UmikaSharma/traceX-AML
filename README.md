# TraceX Sentinel — Executive AML Intelligence Platform

TraceX Sentinel is an enterprise-grade Anti-Money Laundering (AML) surveillance system engineered to detect capital flight, transaction bursts (smurfing), and coordinated financial crime topologies across high-volume transaction databases.

---

## Key Features

- **Multi-Dimensional Anomaly Detection:** Utilizes an Isolation Forest machine learning model trained on transaction amounts and rolling velocity metrics to uncover high-risk accounts and capital flight.
- **Topological Network Investigator:** Directional graph engine powered by NetworkX and Plotly that isolates mule rings, hub nodes, layering cycles, and dispersal networks.
- **Regulatory Compliance Center:** One-click automated export of FinCEN-ready Suspicious Activity Reports (SAR) in CSV format.
- **Live Stream Simulation & Telemetry:** Configurable real-time transaction ingestion engine and synthetic attack injection testing suite.
- **Secure Authentication Gate:** Role-based access control interface with dark-mode enterprise branding and session-state security.

---

## Tech Stack

- **Backend & Database:** PostgreSQL, SQLAlchemy, Psycopg2
- **Machine Learning:** Scikit-Learn (Isolation Forest), Joblib
- **Network Analysis:** NetworkX
- **Frontend & Visualization:** Streamlit, Plotly
- **Data Engineering:** Pandas, NumPy

---

## Project Structure

```text
├── .streamlit/        # Streamlit configuration and custom theme settings
├── data/              # Raw data storage and ingest pipelines
├── models/            # Serialized machine learning models (.pkl)
├── pages/             # Multipage dashboard views (Anomaly Detection, Network Graph)
├── sql/               # Database schemas and indexing queries
├── src/               # Application logic, data loaders, and model pipelines
├── tests/             # Unit and integration test suites
├── app.py             # Main entry point and authentication gate
├── requirements.txt   # Project dependencies
└── README.md          # Project documentation
