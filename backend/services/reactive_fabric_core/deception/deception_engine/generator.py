"""
Honeytoken Generator for Deception Engine.

Generates various types of honeytokens.
"""

from __future__ import annotations

import base64
import json
import secrets
import string
from datetime import datetime, timedelta
from typing import Dict


class HoneytokenGenerator:
    """Generates various types of honeytokens."""

    @staticmethod
    def generate_api_key() -> str:
        """Generate fake API key."""
        prefix = secrets.choice(["sk", "pk", "api", "key"])
        chars = string.ascii_letters + string.digits
        key = ''.join(secrets.choice(chars) for _ in range(32))
        return f"{prefix}_{key}"

    @staticmethod
    def generate_password() -> str:
        """Generate fake password."""
        words = ["Admin", "Secret", "Password", "System", "Database"]
        numbers = ''.join(secrets.choice(string.digits) for _ in range(4))
        special = secrets.choice("!@#$%")
        return f"{secrets.choice(words)}{numbers}{special}"

    @staticmethod
    def generate_ssh_key() -> str:
        """Generate fake SSH private key header."""
        key_type = secrets.choice(["RSA", "DSA", "ECDSA", "ED25519"])
        fake_key = ''.join(
            secrets.choice(string.ascii_letters + string.digits)
            for _ in range(64)
        )
        return (
            f"-----BEGIN {key_type} PRIVATE KEY-----\n"
            f"{fake_key}\n"
            f"-----END {key_type} PRIVATE KEY-----"
        )

    @staticmethod
    def generate_database_cred() -> Dict[str, str]:
        """Generate fake database credentials."""
        return {
            "host": f"db-{secrets.token_hex(4)}.internal",
            "port": str(secrets.choice([3306, 5432, 1433, 27017])),
            "username": f"db_user_{secrets.token_hex(4)}",
            "password": HoneytokenGenerator.generate_password(),
            "database": f"prod_db_{secrets.token_hex(4)}"
        }

    @staticmethod
    def generate_aws_key() -> Dict[str, str]:
        """Generate fake AWS credentials."""
        access_key = "AKIA" + ''.join(
            secrets.choice(string.ascii_uppercase + string.digits)
            for _ in range(16)
        )
        secret_key = ''.join(
            secrets.choice(string.ascii_letters + string.digits)
            for _ in range(40)
        )
        return {
            "access_key_id": access_key,
            "secret_access_key": secret_key,
            "region": secrets.choice(["us-east-1", "us-west-2", "eu-west-1"])
        }

    @staticmethod
    def generate_jwt() -> str:
        """Generate fake JWT token."""
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": f"user_{secrets.token_hex(4)}",
            "iat": int(datetime.utcnow().timestamp()),
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        }
        header_b64 = base64.b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        signature = secrets.token_urlsafe(32)
        return f"{header_b64}.{payload_b64}.{signature}"
