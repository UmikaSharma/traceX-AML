import os
import sys
import pandas as pd

# Add project root to sys.path so imports work cleanly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.db.models import engine, Base
def init_db():
    print("Dropping old tables and recreating with new schema...")
    Base.metadata.drop_all(bind=engine)  # This deletes the old tables
    Base.metadata.create_all(bind=engine) # This makes the new ones

def load_data(csv_path="data/HI-Small_Trans.csv"):
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    print(f"Reading {csv_path}...")
    df = pd.read_csv(csv_path)

    # Rename columns to match database schema
    df = df.rename(columns={
        'Timestamp': 'timestamp',
        'From Bank': 'sender_bank',
        'Account': 'sender_account',
        'To Bank': 'receiver_bank',
        'Account.1': 'receiver_account',
        'Amount Paid': 'amount_paid',
        'Payment Currency': 'payment_currency',
        'Amount Received': 'amount_received',
        'Receiving Currency': 'receiving_currency',
        'Payment Format': 'payment_format',
        'Is Laundering': 'is_laundering'
    })

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Extract unique accounts
    senders = df[['sender_account', 'sender_bank']].rename(
        columns={'sender_account': 'account_id', 'sender_bank': 'bank_id'}
    )
    receivers = df[['receiver_account', 'receiver_bank']].rename(
        columns={'receiver_account': 'account_id', 'receiver_bank': 'bank_id'}
    )
    accounts = pd.concat([senders, receivers]).drop_duplicates(subset=['account_id'])

    print(f"Inserting {len(accounts)} accounts into database...")
    accounts.to_sql('accounts', engine, if_exists='append', index=False, chunksize=10000)

    print(f"Inserting {len(df)} transactions into database...")
    df.to_sql('transactions', engine, if_exists='append', index=False, chunksize=10000)

    print("Ingestion complete!")

if __name__ == "__main__":
    init_db()
    load_data()