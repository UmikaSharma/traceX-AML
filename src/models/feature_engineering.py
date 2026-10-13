"""
TraceX AML - Feature Engineering Module
Calculates transaction velocity (count per hour/day) and behavioral signals to detect smurfing and structuring patterns.
"""

import pandas as pd
import numpy as np

FEATURE_COLUMNS = ['amount_paid', 'amount_received', 'velocity_1h', 'velocity_24h']

def compute_velocity_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes transaction velocity metrics (count per 1 hour and count per 24 hours)
    for each sender_account to detect smurfing (burst transactions below reporting limits).
    
    Args:
        df: DataFrame containing at least 'sender_account', 'timestamp', 'amount_paid', 'amount_received'.
        
    Returns:
        DataFrame with added 'velocity_1h' and 'velocity_24h' columns.
    """
    if df.empty:
        df_copy = df.copy()
        df_copy['velocity_1h'] = 0.0
        df_copy['velocity_24h'] = 0.0
        return df_copy

    df_out = df.copy()

    # Ensure timestamp is datetime
    if 'timestamp' in df_out.columns:
        df_out['timestamp'] = pd.to_datetime(df_out['timestamp'])
    else:
        df_out['timestamp'] = pd.Timestamp.now()

    # Ensure amount columns are numeric
    df_out['amount_paid'] = pd.to_numeric(df_out['amount_paid'], errors='coerce').fillna(0.0)
    if 'amount_received' not in df_out.columns:
        df_out['amount_received'] = df_out['amount_paid']
    else:
        df_out['amount_received'] = pd.to_numeric(df_out['amount_received'], errors='coerce').fillna(df_out['amount_paid'])

    if 'sender_account' not in df_out.columns:
        df_out['velocity_1h'] = 1.0
        df_out['velocity_24h'] = 1.0
        return df_out

    # Preserve initial index
    orig_index = df_out.index

    # Sort by sender and timestamp for rolling windows
    df_out = df_out.sort_values(by=['sender_account', 'timestamp'])

    # Calculate rolling counts
    # Rolling 1-hour window count
    try:
        velocity_1h = (
            df_out.groupby('sender_account')
            .rolling('1h', on='timestamp')['amount_paid']
            .count()
            .values
        )
        df_out['velocity_1h'] = velocity_1h
    except Exception:
        # Fallback if timestamps are duplicate or non-monotonic per group
        df_out['velocity_1h'] = df_out.groupby('sender_account')['amount_paid'].transform('count')

    # Rolling 24-hour window count (1 day)
    try:
        velocity_24h = (
            df_out.groupby('sender_account')
            .rolling('24h', on='timestamp')['amount_paid']
            .count()
            .values
        )
        df_out['velocity_24h'] = velocity_24h
    except Exception:
        df_out['velocity_24h'] = df_out.groupby('sender_account')['amount_paid'].transform('count')

    # Reindex back to original row order
    df_out = df_out.reindex(orig_index)

    df_out['velocity_1h'] = df_out['velocity_1h'].fillna(1.0).astype(float)
    df_out['velocity_24h'] = df_out['velocity_24h'].fillna(1.0).astype(float)

    return df_out


def get_velocity_sql_query(limit: int = 5000, order_by: str = "timestamp DESC") -> str:
    """
    High-performance PostgreSQL query utilizing SQL window functions to calculate
    transaction velocity over 1 hour and 24 hours directly inside the database.
    """
    return f"""
    SELECT 
        t.transaction_id,
        t.timestamp,
        t.sender_bank,
        t.sender_account,
        t.receiver_bank,
        t.receiver_account,
        t.amount_paid,
        t.payment_currency,
        t.amount_received,
        t.receiving_currency,
        t.payment_format,
        t.is_laundering,
        COUNT(*) OVER (
            PARTITION BY t.sender_account 
            ORDER BY t.timestamp 
            RANGE BETWEEN INTERVAL '1 hour' PRECEDING AND CURRENT ROW
        ) AS velocity_1h,
        COUNT(*) OVER (
            PARTITION BY t.sender_account 
            ORDER BY t.timestamp 
            RANGE BETWEEN INTERVAL '1 day' PRECEDING AND CURRENT ROW
        ) AS velocity_24h
    FROM (
        SELECT * FROM transactions 
        ORDER BY {order_by} 
        LIMIT {limit}
    ) t
    ORDER BY t.timestamp DESC;
    """


def classify_typology(row: pd.Series) -> str:
    """
    Classifies the specific money laundering typology based on amount and velocity signals.
    """
    v_1h = row.get('velocity_1h', 1.0)
    v_24h = row.get('velocity_24h', 1.0)
    amt = row.get('amount_paid', 0.0)

    is_smurfing = v_1h >= 5 or v_24h >= 10
    is_high_val = amt >= 100000.0
    is_structuring_amt = 7000.0 <= amt <= 9999.0

    if is_smurfing and is_structuring_amt:
        return "Smurfing & Structuring (Sub-threshold Burst)"
    elif is_smurfing:
        return "High-Velocity Mule Burst (Smurfing)"
    elif is_high_val:
        return "High-Value Capital Flight Outlier"
    elif is_structuring_amt:
        return "Threshold Avoidance Structuring ($7k-$10k)"
    else:
        return "Statistical Isolation Outlier"
