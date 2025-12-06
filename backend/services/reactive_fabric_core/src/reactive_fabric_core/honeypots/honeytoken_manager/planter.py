"""
Token Planter for Honeytoken Manager.

Intelligent token placement in honeypots.
"""

from __future__ import annotations

import logging
from typing import List

from .models import Honeytoken

logger = logging.getLogger(__name__)


class PlanterMixin:
    """Mixin providing token planting capabilities."""

    async def generate_ssh_keypair(self, key_name: str) -> Honeytoken:
        """Generate SSH keypair (implemented in generators)."""
        raise NotImplementedError

    async def generate_aws_credentials(self, placement: str) -> Honeytoken:
        """Generate AWS credentials (implemented in generators)."""
        raise NotImplementedError

    async def generate_api_token(self, service: str, prefix: str) -> Honeytoken:
        """Generate API token (implemented in generators)."""
        raise NotImplementedError

    async def generate_database_credentials(self) -> Honeytoken:
        """Generate database credentials (implemented in generators)."""
        raise NotImplementedError

    async def plant_tokens_in_honeypot(
        self,
        honeypot_id: str,
        honeypot_type: str,
    ) -> List[Honeytoken]:
        """
        Intelligently plant honeytokens in a honeypot based on type.

        Args:
            honeypot_id: Honeypot identifier
            honeypot_type: Type of honeypot (ssh, web, database)

        Returns:
            List of planted honeytokens
        """
        planted: List[Honeytoken] = []

        if honeypot_type == "ssh":
            # Plant SSH keys and AWS credentials
            ssh_token = await self.generate_ssh_keypair(
                key_name=f"{honeypot_id}_deploy_key"
            )
            planted.append(ssh_token)

            aws_token = await self.generate_aws_credentials(
                placement="~/.aws/credentials"
            )
            planted.append(aws_token)

        elif honeypot_type == "web":
            # Plant API tokens in config files
            stripe_token = await self.generate_api_token("stripe", "sk_live")
            planted.append(stripe_token)

            github_token = await self.generate_api_token("github", "ghp")
            planted.append(github_token)

            # Plant database credentials
            db_token = await self.generate_database_credentials()
            planted.append(db_token)

        elif honeypot_type == "database":
            # Plant various credentials in tables
            aws_token = await self.generate_aws_credentials(
                placement="api_credentials_table"
            )
            planted.append(aws_token)

            ssh_token = await self.generate_ssh_keypair(
                key_name="production_backup_key"
            )
            planted.append(ssh_token)

        logger.info("Planted %d honeytokens in %s", len(planted), honeypot_id)
        return planted
