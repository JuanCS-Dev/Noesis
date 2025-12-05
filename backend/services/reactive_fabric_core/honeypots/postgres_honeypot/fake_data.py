"""
Fake Data Generation for PostgreSQL Honeypot.

Realistic customer and user data.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta


class FakeDataMixin:
    """Mixin providing fake data generation."""

    def _build_fake_customer_data(self) -> str:
        """Generate realistic but fake customer data."""
        sql = "\n-- Inserting fake customer data\n"

        # Generate 1000 fake customers
        first_names = [
            "John", "Jane", "Michael", "Sarah", "David", "Emily",
            "Robert", "Lisa", "James", "Mary", "William", "Patricia",
            "Richard", "Jennifer", "Charles",
        ]
        last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
            "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez",
            "Lopez", "Gonzalez",
        ]

        cities = [
            ("New York", "NY"),
            ("Los Angeles", "CA"),
            ("Chicago", "IL"),
            ("Houston", "TX"),
            ("Phoenix", "AZ"),
            ("Philadelphia", "PA"),
            ("San Antonio", "TX"),
            ("San Diego", "CA"),
            ("Dallas", "TX"),
        ]

        for i in range(1000):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = f"{first_name.lower()}.{last_name.lower()}{i}@email.com"

            # Generate fake SSN (not real format)
            ssn = (
                f"{random.randint(100, 999)}-"
                f"{random.randint(10, 99)}-"
                f"{random.randint(1000, 9999)}"
            )

            # Random date of birth
            days_ago = random.randint(18 * 365, 80 * 365)
            dob = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

            city, state = random.choice(cities)
            zip_code = f"{random.randint(10000, 99999)}"

            credit_card = f"{random.randint(1000, 9999)}"
            credit_limit = random.randint(1000, 50000)
            phone_suffix = random.randint(1000, 9999)

            sql += f"""
INSERT INTO customers (customer_code, first_name, last_name, email, phone, ssn,
                      date_of_birth, city, state, zip_code, credit_card_last4, credit_limit)
VALUES ('CUST{i:06d}', '{first_name}', '{last_name}', '{email}',
        '555-{phone_suffix}', '{ssn}', '{dob}',
        '{city}', '{state}', '{zip_code}', '{credit_card}', {credit_limit});
"""

        # Add some admin users with weak passwords
        sql += """
-- Admin user accounts (WEAK PASSWORDS - FOR TESTING ONLY!)
INSERT INTO user_accounts (username, password_hash, email, role)
VALUES
    ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7GxOJwxzKK', 'admin@company.com', 'administrator'),
    ('backup_admin', '$2b$12$4X1RhMCj8.kT4G8qv9R7Q.xLZR0Rd0/LewY5NU7GxOJwxzKK', 'backup@company.com', 'backup_admin'),
    ('db_admin', '$2b$12$5Y2SiNDk9.lU5H9rw0S8R.yMaSR1Se1/MfxZ6OV8HyPKyAKxxALL', 'dbadmin@company.com', 'dba');
"""

        return sql
