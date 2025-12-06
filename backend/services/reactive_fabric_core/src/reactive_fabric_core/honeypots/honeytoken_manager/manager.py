"""
Main Honeytoken Manager Class.

Centralized management of honeytokens across all honeypots.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Optional

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import redis.asyncio as aioredis
else:
    try:
        import redis.asyncio as aioredis
    except ImportError:
        aioredis = None  # type: ignore[assignment]

from .generators import GeneratorMixin
from .models import Honeytoken
from .planter import PlanterMixin
from .triggers import TriggerMixin

logger = logging.getLogger(__name__)


class HoneytokenManager(GeneratorMixin, PlanterMixin, TriggerMixin):
    """
    Centralized management of honeytokens across all honeypots.

    Features:
    - Dynamic token generation
    - Real-time monitoring
    - Automatic alerting
    - Context-aware placement
    """

    def __init__(self, redis_url: str = "redis://localhost:6379") -> None:
        """
        Initialize honeytoken manager.

        Args:
            redis_url: Redis connection URL for tracking
        """
        self.redis_url = redis_url
        self.redis: Optional[Any] = None  # redis.asyncio.Redis

        # Token storage
        self.active_tokens: Dict[str, Honeytoken] = {}
        self.triggered_tokens: List[Honeytoken] = []

        # Callbacks for alerts
        self.trigger_callbacks: List[Callable[..., Any]] = []

        # Statistics
        self.stats: Dict[str, int] = {
            "total_generated": 0,
            "total_triggered": 0,
            "total_active": 0,
        }

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if aioredis is None:
            logger.warning("redis package not available. Using in-memory storage.")
            return

        try:
            self.redis = await aioredis.from_url(self.redis_url)
            logger.info("Honeytoken manager initialized with Redis")
        except Exception as e:
            logger.warning(
                "Could not connect to Redis: %s. Using in-memory storage.", e
            )

    async def _register_token(self, token: Honeytoken) -> None:
        """Register a new token."""
        self.active_tokens[token.token_id] = token
        self.stats["total_generated"] += 1
        self.stats["total_active"] += 1

        # Store in Redis for persistence
        if self.redis:
            await self.redis.hset(
                f"honeytoken:{token.token_id}",
                mapping={
                    "token_type": token.token_type.value,
                    "value": token.value,
                    "created_at": token.created_at.isoformat(),
                    "metadata": json.dumps(token.metadata),
                },
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get honeytoken statistics."""
        return {
            **self.stats,
            "active_tokens": len(self.active_tokens),
            "triggered_tokens": len(self.triggered_tokens),
            "trigger_rate": (
                self.stats["total_triggered"] / self.stats["total_generated"]
                if self.stats["total_generated"] > 0
                else 0
            ),
        }
