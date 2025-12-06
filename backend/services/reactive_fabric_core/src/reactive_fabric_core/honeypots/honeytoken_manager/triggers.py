"""
Trigger Management for Honeytoken Manager.

Token trigger detection and callbacks.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from .models import Honeytoken, HoneytokenStatus

logger = logging.getLogger(__name__)


class TriggerMixin:
    """Mixin providing trigger management capabilities."""

    redis: Optional[Any]  # redis.asyncio.Redis
    active_tokens: Dict[str, Honeytoken]
    triggered_tokens: List[Honeytoken]
    trigger_callbacks: List[Callable[..., Any]]
    stats: Dict[str, int]

    async def check_token_triggered(
        self,
        token_value: str,
    ) -> Optional[Honeytoken]:
        """
        Check if a specific token has been triggered.

        Args:
            token_value: Token value to check

        Returns:
            Honeytoken if found and triggered, None otherwise
        """
        for token in self.active_tokens.values():
            if token.value == token_value or token_value in token.value:
                if token.status == HoneytokenStatus.TRIGGERED:
                    return token

        return None

    async def trigger_token(
        self,
        token_id: str,
        source_ip: str,
        context: Dict[str, Any],
    ) -> bool:
        """
        Mark a token as triggered (used by attacker).

        Args:
            token_id: Token identifier
            source_ip: IP that used the token
            context: Additional context about trigger

        Returns:
            True if token was found and triggered
        """
        if token_id not in self.active_tokens:
            logger.warning("Token %s not found", token_id)
            return False

        token = self.active_tokens[token_id]
        token.trigger(source_ip, context)

        # Move to triggered list
        self.triggered_tokens.append(token)

        # Update stats
        self.stats["total_triggered"] += 1
        self.stats["total_active"] -= 1

        # Store in Redis
        if self.redis:
            await self.redis.hset(
                f"honeytoken_triggered:{token_id}",
                mapping={
                    "token_type": token.token_type.value,
                    "source_ip": source_ip,
                    "triggered_at": token.triggered_at.isoformat(),
                    "context": json.dumps(context),
                },
            )

        # Trigger callbacks
        for callback in self.trigger_callbacks:
            try:
                await callback(token, source_ip, context)
            except Exception as e:
                logger.error("Error in trigger callback: %s", e)

        logger.critical(
            "HONEYTOKEN TRIGGERED! Type: %s, Source: %s, Token: %s",
            token.token_type.value,
            source_ip,
            token_id[:8],
        )

        return True

    async def register_trigger_callback(self, callback: Callable[..., Any]) -> None:
        """
        Register callback for honeytoken triggers.

        Args:
            callback: Async function to call when token is triggered
        """
        self.trigger_callbacks.append(callback)

    def get_recent_triggers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent honeytoken triggers."""
        recent = sorted(
            self.triggered_tokens,
            key=lambda t: t.triggered_at or datetime.min,
            reverse=True,
        )[:limit]

        return [token.to_dict() for token in recent]

    async def cleanup_expired(self, max_age_days: int = 30) -> int:
        """Clean up old expired tokens."""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        expired = [
            token_id
            for token_id, token in self.active_tokens.items()
            if token.created_at < cutoff_date and token.trigger_count == 0
        ]

        for token_id in expired:
            token = self.active_tokens[token_id]
            token.status = HoneytokenStatus.EXPIRED
            del self.active_tokens[token_id]

            if self.redis:
                await self.redis.delete(f"honeytoken:{token_id}")

        logger.info("Cleaned up %d expired honeytokens", len(expired))
        return len(expired)
