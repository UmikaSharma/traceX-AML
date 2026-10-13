"""
TraceX AML - Real-Time Transaction Stream Generator
Simulates live financial transaction ingestion into PostgreSQL, including
normal baseline flows and synthetic smurfing/structuring burst attacks.
"""

import os
import sys
import time
import random
import argparse
from datetime import datetime
import pandas as pd
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.db.models import engine

CURRENCIES = ['US Dollar', 'Euro', 'UK Pound', 'Yen', 'Swiss Franc', 'Canadian Dollar']
PAYMENT_FORMATS = ['ACH', 'Wire', 'Credit Card', 'Cash', 'Cheque', 'Reinvestment']

class TransactionStreamGenerator:
    def __init__(self, pool_size: int = 500):
        self.pool_size = pool_size
        self._load_account_pool()
        self.generated_count = 0
        self.smurfing_bursts_count = 0

    def _load_account_pool(self):
        """Pre-loads a cached pool of accounts from the database for fast generator lookups."""
        try:
            query = f"SELECT account_id, bank_id FROM accounts LIMIT {self.pool_size}"
            df = pd.read_sql(query, engine)
            if df.empty:
                # Fallback mock accounts if empty
                self.accounts = [(f"ACC_{i:06d}", 100 + (i % 20)) for i in range(500)]
            else:
                self.accounts = list(zip(df['account_id'].tolist(), df['bank_id'].tolist()))
        except Exception as e:
            print(f"Warning: Could not fetch accounts from DB: {e}. Using fallback pool.")
            self.accounts = [(f"ACC_{i:06d}", 100 + (i % 20)) for i in range(500)]

    def generate_single_transaction(self, sender=None, receiver=None, is_laundering=0, amount=None, timestamp=None):
        """Generates a single synthetic transaction record."""
        if not sender:
            sender = random.choice(self.accounts)
        if not receiver:
            receiver = random.choice(self.accounts)
            while receiver[0] == sender[0]:
                receiver = random.choice(self.accounts)

        currency = random.choices(CURRENCIES, weights=[0.65, 0.15, 0.08, 0.05, 0.04, 0.03])[0]
        fmt = random.choice(PAYMENT_FORMATS)

        if amount is None:
            if is_laundering:
                # Smurfing structured amount: right below $10k reporting limit
                amount = round(random.uniform(7500.0, 9950.0), 2)
            else:
                # Pareto/log-normal distribution for typical retail/business transfers
                amount = round(random.expovariate(1 / 1200) + 15.0, 2)
                amount = min(amount, 750000.0)

        ts = timestamp or datetime.now()

        tx = {
            'timestamp': ts,
            'sender_bank': sender[1],
            'sender_account': sender[0],
            'receiver_bank': receiver[1],
            'receiver_account': receiver[0],
            'amount_paid': amount,
            'payment_currency': currency,
            'amount_received': amount,
            'receiving_currency': currency,
            'payment_format': fmt,
            'is_laundering': is_laundering
        }
        return tx

    def generate_smurfing_burst(self, burst_size: int = 8, structured_amount: float = None):
        """
        Generates a classic smurfing burst attack:
        One sender rapidly disburses multiple structured amounts right under $10,000
        to several different receiver accounts within minutes.
        """
        sender = random.choice(self.accounts)
        available_receivers = [acc for acc in self.accounts if acc[0] != sender[0]]
        receivers = random.sample(available_receivers, min(burst_size, len(available_receivers)))
        
        now = datetime.now()
        burst = []
        for i, rec in enumerate(receivers):
            amt = structured_amount or round(random.uniform(8400.0, 9920.0), 2)
            # rapid succession (seconds apart)
            tx_time = now + pd.Timedelta(seconds=i * 15)
            tx = self.generate_single_transaction(
                sender=sender,
                receiver=rec,
                is_laundering=1,
                amount=amt,
                timestamp=tx_time
            )
            burst.append(tx)
        
        self.smurfing_bursts_count += 1
        return burst

    def insert_transactions(self, tx_list):
        """Inserts generated transactions into PostgreSQL."""
        if not tx_list:
            return 0
        df = pd.DataFrame(tx_list)
        df.to_sql('transactions', engine, if_exists='append', index=False)
        self.generated_count += len(tx_list)
        return len(tx_list)

    def run_stream(self, rate_sec: float = 1.0, burst_interval_sec: int = 15, duration_sec: int = None):
        """Runs continuous transaction stream generator."""
        print(f"Starting transaction stream: 1 tx every {rate_sec}s, bursts every {burst_interval_sec}s...")
        start_time = time.time()
        last_burst_time = time.time()

        try:
            while True:
                if duration_sec and (time.time() - start_time) > duration_sec:
                    break

                now = time.time()
                # Check if it's time to trigger a smurfing burst
                if now - last_burst_time >= burst_interval_sec:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 INJECTING SMURFING BURST ATTACK!")
                    burst = self.generate_smurfing_burst(burst_size=random.randint(6, 12))
                    self.insert_transactions(burst)
                    print(f"-> Injected {len(burst)} structured transactions from mule sender {burst[0]['sender_account']}")
                    last_burst_time = now
                else:
                    # Regular single transaction
                    tx = self.generate_single_transaction()
                    self.insert_transactions([tx])
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Ingested TX | {tx['sender_account']} -> {tx['receiver_account']} | ${tx['amount_paid']:,.2f} ({tx['payment_format']})")

                time.sleep(rate_sec)
        except KeyboardInterrupt:
            print("\nStream stopped by user.")
        print(f"Summary: Ingested {self.generated_count} total transactions ({self.smurfing_bursts_count} smurfing bursts).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TraceX Real-Time Transaction Stream Generator")
    parser.add_argument("--rate", type=float, default=1.5, help="Seconds between single transactions")
    parser.add_argument("--burst-interval", type=int, default=20, help="Seconds between smurfing burst attacks")
    parser.add_argument("--duration", type=int, default=None, help="Total run duration in seconds")
    args = parser.parse_args()

    generator = TransactionStreamGenerator()
    generator.run_stream(rate_sec=args.rate, burst_interval_sec=args.burst_interval, duration_sec=args.duration)
