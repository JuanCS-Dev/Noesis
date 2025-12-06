"""
Database Schema for PostgreSQL Honeypot.

Realistic database schema generation.
"""

from __future__ import annotations


class SchemaMixin:
    """Mixin providing database schema generation."""

    def _build_database_schema(self) -> str:
        """Build realistic database schema."""
        return """
-- Production Backup Database
-- Created: 2025-10-13
-- CONFIDENTIAL - Internal Use Only

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    customer_code VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    ssn VARCHAR(11),  -- Social Security Number (SENSITIVE!)
    date_of_birth DATE,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    credit_card_last4 VARCHAR(4),
    credit_limit DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active'
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    transaction_date TIMESTAMP NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    description TEXT,
    merchant VARCHAR(255),
    category VARCHAR(50),
    status VARCHAR(20) DEFAULT 'completed'
);

-- User accounts table
CREATE TABLE IF NOT EXISTS user_accounts (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    last_login TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    account_locked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_ssn ON customers(ssn);
CREATE INDEX idx_transactions_customer ON transactions(customer_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);

"""
