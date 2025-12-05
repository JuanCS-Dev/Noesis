"""
Deception Checkers for Deception Engine.

Methods for checking interactions with deception elements.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import (
    BreadcrumbTrail,
    DeceptionEvent,
    DeceptionType,
    DecoySystem,
    Honeytoken,
    TrapDocument,
)

logger = logging.getLogger(__name__)


class DeceptionCheckerMixin:
    """Mixin providing deception checking capabilities."""

    honeytokens: Dict[str, Honeytoken]
    decoy_systems: Dict[str, DecoySystem]
    trap_documents: Dict[str, TrapDocument]
    breadcrumbs: Dict[str, BreadcrumbTrail]
    events: List[DeceptionEvent]
    triggers_count: int

    async def check_honeytoken(
        self,
        token_value: str,
        source_ip: str = None
    ) -> Optional[DeceptionEvent]:
        """
        Check if accessed token is a honeytoken.

        Phase 1: PASSIVE - only logs and returns event, no active response.
        """
        for token_id, token in self.honeytokens.items():
            if token.token_value == token_value or token_value in token.token_value:
                token.triggered = True
                token.access_count += 1
                token.last_accessed = datetime.utcnow()

                event = DeceptionEvent(
                    deception_type=DeceptionType.HONEYTOKEN,
                    element_id=token_id,
                    source_ip=source_ip,
                    action="accessed",
                    severity="high",
                    details={
                        "token_type": token.token_type.value,
                        "metadata": token.metadata,
                        "access_count": token.access_count
                    }
                )

                self.events.append(event)
                self.triggers_count += 1

                logger.warning(
                    "HONEYTOKEN TRIGGERED - Type: %s, Source: %s, Count: %d",
                    token.token_type.value, source_ip, token.access_count
                )

                return event

        return None

    async def check_decoy_interaction(
        self,
        target_ip: str,
        source_ip: str,
        action: str = "connection"
    ) -> Optional[DeceptionEvent]:
        """
        Check if interaction is with a decoy system.

        Phase 1: PASSIVE - only logs interaction, doesn't engage.
        """
        for decoy_id, decoy in self.decoy_systems.items():
            if decoy.ip_address == target_ip or decoy.hostname == target_ip:
                decoy.triggered = True
                decoy.interaction_count += 1
                decoy.last_interaction = datetime.utcnow()

                event = DeceptionEvent(
                    deception_type=DeceptionType.DECOY_SYSTEM,
                    element_id=decoy_id,
                    source_ip=source_ip,
                    action=action,
                    severity="high" if decoy.interaction_count > 3 else "medium",
                    details={
                        "hostname": decoy.hostname,
                        "services": decoy.services,
                        "interaction_count": decoy.interaction_count
                    }
                )

                self.events.append(event)
                self.triggers_count += 1

                logger.warning(
                    "DECOY TRIGGERED - System: %s, Source: %s, Action: %s",
                    decoy.hostname, source_ip, action
                )

                return event

        return None

    async def check_trap_document(
        self,
        filename: str,
        action: str,
        source_ip: str = None,
        source_user: str = None
    ) -> Optional[DeceptionEvent]:
        """
        Check if accessed document is a trap.

        Phase 1: PASSIVE - only logs access, doesn't modify or block.
        """
        for doc_id, trap in self.trap_documents.items():
            if trap.filename == filename or filename in trap.deployed_paths:
                trap.triggered = True
                trap.access_log.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": action,
                    "source_ip": source_ip,
                    "source_user": source_user
                })

                event = DeceptionEvent(
                    deception_type=DeceptionType.TRAP_DOCUMENT,
                    element_id=doc_id,
                    source_ip=source_ip,
                    source_user=source_user,
                    action=action,
                    severity="critical" if action in ["copied", "exfiltrated"] else "high",
                    details={
                        "filename": trap.filename,
                        "document_type": trap.document_type,
                        "access_count": len(trap.access_log)
                    }
                )

                self.events.append(event)
                self.triggers_count += 1

                logger.warning(
                    "TRAP DOCUMENT TRIGGERED - File: %s, Action: %s, Source: %s",
                    trap.filename, action, source_ip or source_user
                )

                return event

        return None

    async def check_breadcrumb(
        self,
        path: str,
        source_ip: str = None
    ) -> Optional[DeceptionEvent]:
        """
        Check if path matches a breadcrumb trail.

        Phase 1: PASSIVE - only tracks following, doesn't redirect.
        """
        for trail_id, trail in self.breadcrumbs.items():
            if trail.false_path == path or path in trail.false_path:
                trail.followed = True
                trail.follow_count += 1

                event = DeceptionEvent(
                    deception_type=DeceptionType.BREADCRUMB,
                    element_id=trail_id,
                    source_ip=source_ip,
                    action="followed",
                    severity="medium",
                    details={
                        "trail_type": trail.trail_type,
                        "false_path": trail.false_path,
                        "follow_count": trail.follow_count
                    }
                )

                self.events.append(event)
                self.triggers_count += 1

                logger.info(
                    "BREADCRUMB FOLLOWED - Type: %s, Path: %s, Source: %s",
                    trail.trail_type, trail.false_path, source_ip
                )

                return event

        return None
