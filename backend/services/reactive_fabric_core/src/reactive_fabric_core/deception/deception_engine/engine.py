"""
Deception Engine for creating and managing deceptive elements.

This engine manages:
- Honeytokens: Fake credentials and tokens
- Decoy Systems: Fake services and endpoints
- Trap Documents: Documents with tracking capabilities
- Breadcrumb Trails: False paths for attackers

Phase 1: PASSIVE deception only - monitoring without active engagement
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .checkers import DeceptionCheckerMixin
from .generator import HoneytokenGenerator
from .models import (
    BreadcrumbTrail,
    DeceptionConfig,
    DeceptionEvent,
    DecoySystem,
    Honeytoken,
    TokenType,
    TrapDocument,
)

logger = logging.getLogger(__name__)


class DeceptionEngine(DeceptionCheckerMixin):
    """
    Main deception engine for creating and managing deceptive elements.

    Phase 1: PASSIVE deception only - creates elements and monitors access,
    but does not actively engage with attackers.
    """

    def __init__(self, config: DeceptionConfig):
        """Initialize deception engine."""
        self.config = config
        self.generator = HoneytokenGenerator()

        self.honeytokens: Dict[str, Honeytoken] = {}
        self.decoy_systems: Dict[str, DecoySystem] = {}
        self.trap_documents: Dict[str, TrapDocument] = {}
        self.breadcrumbs: Dict[str, BreadcrumbTrail] = {}
        self.events: List[DeceptionEvent] = []

        self._running = False
        self.triggers_count = 0

    async def initialize(self) -> None:
        """Initialize deception elements."""
        await self._generate_honeytokens()
        await self._create_decoy_systems()
        await self._deploy_trap_documents()
        await self._create_breadcrumbs()

        logger.info(
            "Deception Engine initialized - Tokens: %d, Decoys: %d, Traps: %d",
            len(self.honeytokens), len(self.decoy_systems), len(self.trap_documents)
        )

    async def _generate_honeytokens(self) -> None:
        """Generate honeytokens based on configuration."""
        for token_type in self.config.honeytoken_types:
            for _ in range(self.config.honeytokens_per_type):
                token = await self._create_honeytoken(token_type)
                self.honeytokens[token.token_id] = token

    async def _create_honeytoken(self, token_type: TokenType) -> Honeytoken:
        """Create a single honeytoken."""
        token_value = ""
        metadata = {}

        if token_type == TokenType.API_KEY:
            token_value = self.generator.generate_api_key()
            metadata = {"service": "internal_api", "scope": "read"}

        elif token_type == TokenType.PASSWORD:
            token_value = self.generator.generate_password()
            metadata = {"username": f"admin_{secrets.token_hex(4)}", "system": "production"}

        elif token_type == TokenType.SSH_KEY:
            token_value = self.generator.generate_ssh_key()
            metadata = {"host": f"server-{secrets.token_hex(4)}.internal", "user": "root"}

        elif token_type == TokenType.DATABASE_CRED:
            creds = self.generator.generate_database_cred()
            token_value = json.dumps(creds)
            metadata = creds

        elif token_type == TokenType.AWS_KEY:
            creds = self.generator.generate_aws_key()
            token_value = json.dumps(creds)
            metadata = creds

        elif token_type == TokenType.JWT:
            token_value = self.generator.generate_jwt()
            metadata = {"issuer": "auth.internal", "audience": "api.internal"}

        else:
            token_value = secrets.token_urlsafe(32)
            metadata = {"type": "generic"}

        return Honeytoken(
            token_type=token_type,
            token_value=token_value,
            metadata=metadata
        )

    async def _create_decoy_systems(self) -> None:
        """Create decoy systems."""
        for i in range(min(5, self.config.max_decoy_systems)):
            decoy = DecoySystem(
                hostname=f"prod-server-{secrets.token_hex(4)}",
                ip_address=f"10.0.{i}.{secrets.randbelow(255)}",
                services=[
                    {"name": "ssh", "port": 22, "banner": "OpenSSH_7.4"},
                    {"name": "http", "port": 80, "banner": "Apache/2.4.41"}
                ]
            )

            token_ids = list(self.honeytokens.keys())[:2]
            decoy.honeytokens = token_ids

            self.decoy_systems[decoy.decoy_id] = decoy

    async def _deploy_trap_documents(self) -> None:
        """Deploy trap documents."""
        doc_names = [
            "passwords.txt",
            "api_keys.xlsx",
            "database_backup.sql",
            "aws_credentials.json",
            "financial_report.pdf",
            "employee_data.csv"
        ]

        for name in doc_names[:self.config.max_trap_documents]:
            doc_type = name.split('.')[-1]
            if doc_type in self.config.trap_document_types:
                trap = TrapDocument(
                    filename=name,
                    document_type=doc_type,
                    content_hash=hashlib.sha256(name.encode()).hexdigest(),
                    tracking_token=secrets.token_urlsafe(16),
                    deployed_paths=[
                        f"/tmp/{name}",
                        f"/var/www/html/backup/{name}",
                        f"/home/admin/Documents/{name}"
                    ]
                )
                self.trap_documents[trap.document_id] = trap

    async def _create_breadcrumbs(self) -> None:
        """Create breadcrumb trails."""
        trails = [
            BreadcrumbTrail(
                trail_type="file_path",
                false_path="/etc/secret_config/master_key.pem",
                real_path=None
            ),
            BreadcrumbTrail(
                trail_type="network_path",
                false_path="admin.internal.company.com",
                real_path=None
            ),
            BreadcrumbTrail(
                trail_type="config_entry",
                false_path="DATABASE_MASTER_PASSWORD=SuperSecret123!",
                real_path=None
            )
        ]

        for trail in trails:
            if self.honeytokens:
                trail.honeytokens = [list(self.honeytokens.keys())[0]]
            self.breadcrumbs[trail.trail_id] = trail

    async def get_deception_status(self) -> Dict[str, Any]:
        """Get current status of deception elements."""
        total_honeytokens = len(self.honeytokens)
        triggered_tokens = sum(1 for t in self.honeytokens.values() if t.triggered)

        total_decoys = len(self.decoy_systems)
        triggered_decoys = sum(1 for d in self.decoy_systems.values() if d.triggered)

        total_traps = len(self.trap_documents)
        triggered_traps = sum(1 for t in self.trap_documents.values() if t.triggered)

        total_breadcrumbs = len(self.breadcrumbs)
        followed_breadcrumbs = sum(1 for b in self.breadcrumbs.values() if b.followed)

        return {
            "active": self._running,
            "honeytokens": {
                "total": total_honeytokens,
                "triggered": triggered_tokens,
                "percentage": (triggered_tokens / total_honeytokens * 100) if total_honeytokens else 0
            },
            "decoy_systems": {
                "total": total_decoys,
                "triggered": triggered_decoys,
                "percentage": (triggered_decoys / total_decoys * 100) if total_decoys else 0
            },
            "trap_documents": {
                "total": total_traps,
                "triggered": triggered_traps,
                "percentage": (triggered_traps / total_traps * 100) if total_traps else 0
            },
            "breadcrumbs": {
                "total": total_breadcrumbs,
                "followed": followed_breadcrumbs,
                "percentage": (followed_breadcrumbs / total_breadcrumbs * 100) if total_breadcrumbs else 0
            },
            "total_triggers": self.triggers_count,
            "recent_events": self.events[-10:]
        }

    async def rotate_honeytokens(self) -> int:
        """Rotate old honeytokens. Returns number of tokens rotated."""
        rotated = 0
        cutoff = datetime.utcnow() - timedelta(days=self.config.token_rotation_days)

        for token_id in list(self.honeytokens.keys()):
            token = self.honeytokens[token_id]
            if token.created_at < cutoff and not token.triggered:
                new_token = await self._create_honeytoken(token.token_type)
                self.honeytokens[new_token.token_id] = new_token
                del self.honeytokens[token_id]
                rotated += 1

        logger.info("Rotated %d honeytokens", rotated)
        return rotated

    async def start(self) -> None:
        """Start deception engine."""
        self._running = True
        await self.initialize()
        logger.info("Deception Engine started (Phase 1: PASSIVE mode)")

    async def stop(self) -> None:
        """Stop deception engine."""
        self._running = False
        logger.info(
            "Deception Engine stopped - Total triggers: %d, Events: %d",
            self.triggers_count, len(self.events)
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get engine metrics."""
        return {
            "running": self._running,
            "honeytokens": len(self.honeytokens),
            "decoy_systems": len(self.decoy_systems),
            "trap_documents": len(self.trap_documents),
            "breadcrumbs": len(self.breadcrumbs),
            "total_triggers": self.triggers_count,
            "events_logged": len(self.events)
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"DeceptionEngine(running={self._running}, "
            f"honeytokens={len(self.honeytokens)}, "
            f"triggers={self.triggers_count})"
        )
