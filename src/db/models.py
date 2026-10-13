import os
from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "postgresql+psycopg2://postgres:admin123@localhost:5432/tracex"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Account(Base):
    __tablename__ = "accounts"
    account_id = Column(String(50), primary_key=True, index=True)
    bank_id = Column(Integer)

class Transaction(Base):
    __tablename__ = "transactions"
    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True)
    sender_bank = Column(Integer)
    sender_account = Column(String(50), ForeignKey("accounts.account_id"))
    receiver_bank = Column(Integer)
    receiver_account = Column(String(50), ForeignKey("accounts.account_id"))
    amount_paid = Column(Numeric(15, 2))
    payment_currency = Column(String(50)) # Increased to 50
    amount_received = Column(Numeric(15, 2))
    receiving_currency = Column(String(50)) # Increased to 50
    payment_format = Column(String(50))
    is_laundering = Column(Integer)