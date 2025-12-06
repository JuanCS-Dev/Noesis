"""
Utility Functions for Honeytoken Manager.

Random string and password generation.
"""

from __future__ import annotations

import secrets


def generate_random_string(length: int, uppercase: bool = False) -> str:
    """Generate cryptographically secure random string."""
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    if uppercase:
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

    return ''.join(secrets.choice(chars) for _ in range(length))


def generate_strong_password(length: int = 16) -> str:
    """Generate strong password."""
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))
