-- TraceX PostgreSQL Database Schema
-- Anti-Money Laundering (AML) Intelligence Platform

CREATE TABLE IF NOT EXISTS accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    bank_id INTEGER
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    sender_bank INTEGER,
    sender_account VARCHAR(50) REFERENCES accounts(account_id),
    receiver_bank INTEGER,
    receiver_account VARCHAR(50) REFERENCES accounts(account_id),
    amount_paid NUMERIC(15, 2),
    payment_currency VARCHAR(50),
    amount_received NUMERIC(15, 2),
    receiving_currency VARCHAR(50),
    payment_format VARCHAR(50),
    is_laundering INTEGER DEFAULT 0
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS ix_transactions_timestamp ON transactions(timestamp);
CREATE INDEX IF NOT EXISTS ix_transactions_sender_account ON transactions(sender_account);
CREATE INDEX IF NOT EXISTS ix_transactions_receiver_account ON transactions(receiver_account);
