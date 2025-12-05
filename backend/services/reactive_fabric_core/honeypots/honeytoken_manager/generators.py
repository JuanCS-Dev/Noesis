"""
Token Generators for Honeytoken Manager.

AWS, API, SSH, database, and document token generation.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from .models import Honeytoken, HoneytokenType
from .utils import generate_random_string, generate_strong_password

logger = logging.getLogger(__name__)


class GeneratorMixin:
    """Mixin providing token generation capabilities."""

    active_tokens: Dict[str, Honeytoken]
    stats: Dict[str, int]

    async def _register_token(self, token: Honeytoken) -> None:
        """Register a new token (implemented in manager)."""
        raise NotImplementedError

    async def generate_aws_credentials(
        self,
        placement: str = "config_file",
        region: str = "us-east-1",
    ) -> Honeytoken:
        """
        Generate fake AWS credentials that look realistic.

        Args:
            placement: Where token will be placed
            region: AWS region to simulate

        Returns:
            Honeytoken with AWS credentials
        """
        # Generate realistic-looking access key
        access_key = f"AKIA{generate_random_string(16, uppercase=True)}"

        # Generate secret key (40 chars, base64-like)
        secret_key = generate_random_string(40)

        token_id = str(uuid.uuid4())

        honeytoken = Honeytoken(
            token_id=token_id,
            token_type=HoneytokenType.AWS_CREDENTIALS,
            value=json.dumps({
                "access_key_id": access_key,
                "secret_access_key": secret_key,
                "region": region,
            }),
            metadata={
                "placement": placement,
                "region": region,
                "purpose": "Production AWS credentials (CONFIDENTIAL)",
            },
        )

        await self._register_token(honeytoken)

        logger.info("Generated AWS credentials honeytoken: %s", access_key)
        return honeytoken

    async def generate_api_token(
        self,
        service: str,
        prefix: str = "sk_live",
    ) -> Honeytoken:
        """
        Generate fake API token for services like Stripe, SendGrid, etc.

        Args:
            service: Service name (stripe, sendgrid, github, etc.)
            prefix: Token prefix

        Returns:
            Honeytoken with API token
        """
        token_body = generate_random_string(32)
        api_token = f"{prefix}_{token_body}"

        token_id = str(uuid.uuid4())

        honeytoken = Honeytoken(
            token_id=token_id,
            token_type=HoneytokenType.API_TOKEN,
            value=api_token,
            metadata={
                "service": service,
                "prefix": prefix,
                "environment": "production",
            },
        )

        await self._register_token(honeytoken)

        logger.info("Generated %s API token: %s...", service, api_token[:20])
        return honeytoken

    async def generate_ssh_keypair(
        self,
        key_name: str = "production-server",
        key_size: int = 2048,
    ) -> Honeytoken:
        """
        Generate fake SSH key pair.

        Args:
            key_name: Name for the key
            key_size: RSA key size

        Returns:
            Honeytoken with SSH keys
        """
        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend(),
        )

        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

        # Serialize public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        ).decode()

        token_id = str(uuid.uuid4())

        honeytoken = Honeytoken(
            token_id=token_id,
            token_type=HoneytokenType.SSH_KEY,
            value=json.dumps({
                "private_key": private_pem,
                "public_key": public_pem,
                "key_name": key_name,
            }),
            metadata={
                "key_name": key_name,
                "key_size": key_size,
                "server": f"{key_name}.internal.company.com",
            },
        )

        await self._register_token(honeytoken)

        logger.info("Generated SSH keypair honeytoken: %s", key_name)
        return honeytoken

    async def generate_database_credentials(
        self,
        db_type: str = "postgresql",
        environment: str = "production",
    ) -> Honeytoken:
        """
        Generate fake database credentials.

        Args:
            db_type: Database type
            environment: Environment name

        Returns:
            Honeytoken with DB credentials
        """
        username = f"{db_type}_admin"
        password = generate_strong_password()
        host = f"{db_type}-{environment}.internal.company.com"

        token_id = str(uuid.uuid4())

        honeytoken = Honeytoken(
            token_id=token_id,
            token_type=HoneytokenType.DATABASE_CREDS,
            value=json.dumps({
                "host": host,
                "port": 5432 if db_type == "postgresql" else 3306,
                "username": username,
                "password": password,
                "database": f"{environment}_data",
            }),
            metadata={
                "db_type": db_type,
                "environment": environment,
                "purpose": "Backup database access",
            },
        )

        await self._register_token(honeytoken)

        logger.info("Generated %s credentials honeytoken", db_type)
        return honeytoken

    async def generate_document_with_watermark(
        self,
        doc_type: str = "pdf",
        content: str = "Confidential",
    ) -> Honeytoken:
        """
        Generate document with invisible tracking.

        Args:
            doc_type: Document type
            content: Document content

        Returns:
            Honeytoken for tracked document
        """
        doc_id = str(uuid.uuid4())
        tracking_url = f"https://tracking.internal.company.com/pixel/{doc_id}.gif"

        token_id = str(uuid.uuid4())

        honeytoken = Honeytoken(
            token_id=token_id,
            token_type=HoneytokenType.DOCUMENT,
            value=json.dumps({
                "document_id": doc_id,
                "tracking_url": tracking_url,
                "filename": f"confidential_{doc_id}.{doc_type}",
            }),
            metadata={
                "doc_type": doc_type,
                "content_preview": content[:50],
                "tracking_method": "invisible_pixel",
            },
        )

        await self._register_token(honeytoken)

        logger.info("Generated tracked document honeytoken: %s", doc_id)
        return honeytoken
