"""
TraceX AML - Streaming Simulation Service
Thread-safe background controller for dynamic transaction ingestion into PostgreSQL and Streamlit state.
"""

import threading
import time
import collections
from datetime import datetime
import pandas as pd
from src.data.stream_generator import TransactionStreamGenerator

class StreamSimulatorService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.generator = TransactionStreamGenerator()
        self.running = False
        self.thread = None
        self.rate_sec = 2.0
        self.burst_probability = 0.2
        self.recent_txs = collections.deque(maxlen=200)
        self.stats = {
            "total_ingested": 0,
            "smurfing_bursts": 0,
            "started_at": None,
            "last_tx_time": None,
            "last_amount": 0.0,
            "last_sender": None,
            "last_receiver": None
        }

    def _worker(self):
        while self.running:
            try:
                # Decide whether to produce a burst or single transaction
                import random
                if random.random() < self.burst_probability:
                    burst = self.generator.generate_smurfing_burst(burst_size=random.randint(5, 10))
                    self.generator.insert_transactions(burst)
                    for tx in burst:
                        self.recent_txs.append(tx)
                    self.stats["total_ingested"] += len(burst)
                    self.stats["smurfing_bursts"] += 1
                    self.stats["last_tx_time"] = datetime.now()
                    self.stats["last_amount"] = burst[-1]["amount_paid"]
                    self.stats["last_sender"] = burst[0]["sender_account"]
                    self.stats["last_receiver"] = burst[-1]["receiver_account"]
                else:
                    tx = self.generator.generate_single_transaction()
                    self.generator.insert_transactions([tx])
                    self.recent_txs.append(tx)
                    self.stats["total_ingested"] += 1
                    self.stats["last_tx_time"] = datetime.now()
                    self.stats["last_amount"] = tx["amount_paid"]
                    self.stats["last_sender"] = tx["sender_account"]
                    self.stats["last_receiver"] = tx["receiver_account"]

            except Exception as e:
                print(f"[StreamSimulatorService Error]: {e}")

            time.sleep(self.rate_sec)

    def start(self, rate_sec: float = 2.0, burst_probability: float = 0.2):
        if self.running:
            return
        self.rate_sec = max(0.2, rate_sec)
        self.burst_probability = burst_probability
        self.running = True
        self.stats["started_at"] = datetime.now()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.thread = None

    def inject_burst(self, burst_size: int = 8, structured_amount: float = None):
        """Immediately triggers a smurfing burst on demand."""
        burst = self.generator.generate_smurfing_burst(burst_size=burst_size, structured_amount=structured_amount)
        self.generator.insert_transactions(burst)
        for tx in burst:
            self.recent_txs.append(tx)
        self.stats["total_ingested"] += len(burst)
        self.stats["smurfing_bursts"] += 1
        self.stats["last_tx_time"] = datetime.now()
        self.stats["last_amount"] = burst[-1]["amount_paid"]
        self.stats["last_sender"] = burst[0]["sender_account"]
        self.stats["last_receiver"] = burst[-1]["receiver_account"]
        return burst

    def is_running(self) -> bool:
        return self.running and (self.thread is not None and self.thread.is_alive())

    def get_stats(self) -> dict:
        return dict(self.stats)

    def get_recent_transactions(self) -> pd.DataFrame:
        if not self.recent_txs:
            return pd.DataFrame()
        return pd.DataFrame(list(self.recent_txs))

# Global service instance
stream_service = StreamSimulatorService()
