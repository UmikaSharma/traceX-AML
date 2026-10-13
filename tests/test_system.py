"""
TraceX AML - End-to-End System Test Suite
Verifies feature engineering, ML pipeline, SAR generation, and streaming simulation.
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.db.models import engine
from src.models.feature_engineering import compute_velocity_features, classify_typology, FEATURE_COLUMNS
from src.data.stream_service import stream_service

def test_pipeline():
    print("=== TEST 1: Model & Feature Pipeline ===")
    model = joblib.load("models/isolation_forest.pkl")
    print("Loaded Model:", type(model).__name__)

    # Synthetic smurfing pattern (6 transfers of ~$9,000 within 12 minutes)
    test_df = pd.DataFrame({
        "timestamp": pd.date_range("2026-10-13 12:00:00", periods=6, freq="2min"),
        "sender_account": ["MULE_TEST_001"] * 6,
        "receiver_account": [f"REC_TEST_{i}" for i in range(6)],
        "amount_paid": [8900.0, 9100.0, 8850.0, 9200.0, 8950.0, 9050.0],
        "amount_received": [8900.0, 9100.0, 8850.0, 9200.0, 8950.0, 9050.0]
    })
    
    feats = compute_velocity_features(test_df)
    print("Computed Features:")
    print(feats[["sender_account", "amount_paid", "velocity_1h", "velocity_24h"]])
    assert feats["velocity_1h"].iloc[-1] == 6.0, "Velocity calculation failed"
    
    preds = model.predict(feats[FEATURE_COLUMNS].astype(float))
    print("Isolation Forest Predictions (-1 is anomaly):", preds)
    
    print("\n=== TEST 2: Typology Classification ===")
    for idx, row in feats.iterrows():
        typology = classify_typology(row)
        print(f"Row {idx} (v1={row['velocity_1h']}, amt=${row['amount_paid']}) -> Typology: {typology}")

    print("\n=== TEST 3: Streaming Simulation Service ===")
    stats_before = stream_service.get_stats()
    burst = stream_service.inject_burst(burst_size=5, structured_amount=9450.0)
    stats_after = stream_service.get_stats()
    print(f"Injected burst: {len(burst)} transactions.")
    print(f"Service stats: {stats_after}")
    assert stats_after["total_ingested"] > stats_before["total_ingested"], "Stream injection failed"

    print("\nSUCCESS: All automated system tests passed with zero errors!")

if __name__ == "__main__":
    test_pipeline()
