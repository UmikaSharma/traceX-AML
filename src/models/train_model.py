import os
import sys
import json
import time
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.ensemble import IsolationForest
import joblib

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.db.models import engine
from src.models.feature_engineering import compute_velocity_features, FEATURE_COLUMNS

def train_isolation_forest(sample_size: int = 150000, contamination: float = 0.025):
    """
    Trains an Isolation Forest anomaly detection pipeline incorporating transaction amounts
    and velocity (1-hour and 24-hour transaction frequency) to detect smurfing and structuring.
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] TraceX ML Pipeline Initiated")
    print(f"Fetching sample of {sample_size:,} transactions with chronological ordering...")
    
    t0 = time.time()
    # Fetch chronologically so rolling time windows for velocity are accurate
    query = f"""
    SELECT transaction_id, timestamp, sender_account, receiver_account, 
           amount_paid, amount_received, is_laundering
    FROM transactions 
    ORDER BY timestamp ASC 
    LIMIT {sample_size}
    """
    df = pd.read_sql(query, engine)
    print(f"Successfully loaded {len(df):,} transactions in {time.time() - t0:.2f}s")

    print("Computing transaction velocity (1-hour & 24-hour rolling frequency) for smurfing detection...")
    t_feat = time.time()
    df = compute_velocity_features(df)
    print(f"Feature engineering completed in {time.time() - t_feat:.2f}s")
    
    print("\nFeature Summary:")
    print(df[FEATURE_COLUMNS].describe().to_string())

    print(f"\nBuilding Pipeline with log-scaling & Isolation Forest on features: {FEATURE_COLUMNS}...")
    X = df[FEATURE_COLUMNS].astype(float)
    
    pipeline = Pipeline([
        ('log_transform', FunctionTransformer(np.log1p, validate=False)),
        ('isolation_forest', IsolationForest(
            n_estimators=120,
            contamination=contamination,
            max_samples='auto',
            random_state=42,
            n_jobs=-1
        ))
    ])
    
    t_train = time.time()
    pipeline.fit(X)
    print(f"Model training converged in {time.time() - t_train:.2f}s")

    # Evaluate predictions
    df['anomaly_prediction'] = pipeline.predict(X)
    df['anomaly_score'] = pipeline.decision_function(X) # lower = more anomalous
    
    flagged = df[df['anomaly_prediction'] == -1]
    flagged_count = len(flagged)
    print(f"\nEvaluation Results:")
    print(f"Total Transactions Scanned: {len(df):,}")
    print(f"Anomalies Flagged: {flagged_count:,} ({flagged_count/len(df)*100:.2f}%)")
    
    # Check smurfing / high velocity in flagged set
    high_velocity_flagged = flagged[flagged['velocity_1h'] >= 5]
    print(f"Smurfing / High-Velocity Bursts Detected (velocity_1h >= 5): {len(high_velocity_flagged):,}")
    
    if 'is_laundering' in df.columns:
        known_laundering = df[df['is_laundering'] == 1]
        known_flagged = known_laundering[known_laundering['anomaly_prediction'] == -1]
        print(f"Known Laundering Caught: {len(known_flagged)}/{len(known_laundering)} "
              f"({(len(known_flagged)/len(known_laundering)*100 if len(known_laundering)>0 else 0):.1f}%)")

    # Persist model and metadata
    os.makedirs("models", exist_ok=True)
    model_path = "models/isolation_forest.pkl"
    joblib.dump(pipeline, model_path)
    print(f"Model saved to '{model_path}'")

    iforest_step = pipeline.named_steps['isolation_forest']
    metadata = {
        "model_type": "Pipeline(FunctionTransformer(log1p) + IsolationForest)",
        "features": FEATURE_COLUMNS,
        "sample_size": len(df),
        "contamination": contamination,
        "n_estimators": 120,
        "trained_at": datetime.now().isoformat(),
        "total_flagged": int(flagged_count),
        "min_score": float(df['anomaly_score'].min()),
        "max_score": float(df['anomaly_score'].max()),
        "threshold_score": float(iforest_step.offset_)
    }
    
    metadata_path = "models/model_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=4)
    print(f"Model metadata saved to '{metadata_path}'")
    print(f"Training pipeline finished successfully in {time.time() - t0:.2f}s total.")
    return pipeline

if __name__ == "__main__":
    train_isolation_forest()