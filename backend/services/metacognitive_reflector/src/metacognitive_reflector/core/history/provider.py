"""
NOESIS Memory Fortress - Criminal History Provider
===================================================

Provider for persistent criminal history storage.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING

from .models import Conviction, CriminalHistory

if TYPE_CHECKING:
    from metacognitive_reflector.config import RedisSettings

logger = logging.getLogger(__name__)


class CriminalHistoryProvider:
    """
    Provider for persistent criminal history.

    Storage Strategy:
    - L2 (Redis): Fast access with list structure
    - L4 (JSON): Complete record with checksums
    - In-Memory Cache: Hot access
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        backup_path: str = "data/criminal_history.json",
        redis_prefix: str = "noesis:history:",
    ) -> None:
        """
        Initialize provider.

        Args:
            redis_url: Redis connection URL (optional)
            backup_path: Path for JSON backup
            redis_prefix: Prefix for Redis keys
        """
        self._redis_url = redis_url
        self._redis_prefix = redis_prefix
        self._backup_path = Path(backup_path)
        self._backup_path.parent.mkdir(parents=True, exist_ok=True)
        self._redis_client: Optional[Any] = None
        self._cache: Dict[str, CriminalHistory] = {}
        self._load_backup()

    @classmethod
    def create_with_settings(
        cls,
        redis_settings: Optional["RedisSettings"] = None,
        backup_path: str = "data/criminal_history.json",
    ) -> "CriminalHistoryProvider":
        """Factory method with settings."""
        return cls(
            redis_url=redis_settings.url if redis_settings else None,
            backup_path=backup_path,
            redis_prefix=redis_settings.history_prefix if redis_settings else "noesis:history:",
        )

    async def _get_redis_client(self) -> Any:
        """Lazy initialize Redis client."""
        if self._redis_client is None and self._redis_url:
            try:
                import redis.asyncio as aioredis
                self._redis_client = await aioredis.from_url(
                    self._redis_url, encoding="utf-8", decode_responses=True,
                )
            except ImportError:
                logger.warning("redis package not available")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
        return self._redis_client

    def _load_backup(self) -> None:
        """Load data from JSON backup."""
        if not self._backup_path.exists():
            return

        try:
            with open(self._backup_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            stored_checksum = data.get("_checksum")
            if stored_checksum:
                records = data.get("records", {})
                calculated = self._calculate_checksum(records)
                if calculated != stored_checksum:
                    logger.error("Criminal history backup checksum mismatch!")
                    return

            for agent_id, history_data in data.get("records", {}).items():
                self._cache[agent_id] = CriminalHistory.from_dict(history_data)

            logger.info(f"Loaded {len(self._cache)} criminal histories from backup")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load criminal history backup: {e}")

    def _save_backup(self) -> None:
        """Save data to JSON backup with checksum."""
        records = {agent_id: history.to_dict() for agent_id, history in self._cache.items()}

        data = {
            "records": records,
            "_checksum": self._calculate_checksum(records),
            "_updated_at": datetime.now().isoformat(),
            "_version": "1.0",
        }

        temp_path = self._backup_path.with_suffix(".json.tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        temp_path.rename(self._backup_path)

    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 checksum."""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    async def record_conviction(
        self,
        agent_id: str,
        crime_id: str,
        sentence_type: str,
        severity: str,
        crime_name: Optional[str] = None,
        pillar: str = "UNKNOWN",
        context: Optional[Dict[str, Any]] = None,
    ) -> Conviction:
        """Record a new conviction."""
        conviction = Conviction(
            crime_id=crime_id,
            crime_name=crime_name or crime_id,
            sentence_type=sentence_type,
            severity=severity,
            pillar=pillar,
            timestamp=datetime.now(),
            context=context or {},
        )

        history = await self.get_history(agent_id)
        if history is None:
            history = CriminalHistory(agent_id=agent_id)

        history.convictions.append(conviction)

        if history.first_offense_date is None:
            history.first_offense_date = conviction.timestamp
        history.last_offense_date = conviction.timestamp

        self._cache[agent_id] = history

        try:
            client = await self._get_redis_client()
            if client:
                key = f"{self._redis_prefix}{agent_id}"
                await client.lpush(key, json.dumps(conviction.to_dict()))
                await client.ltrim(key, 0, 99)
        except Exception as e:
            logger.warning(f"Failed to write conviction to Redis: {e}")

        self._save_backup()
        logger.info(f"Conviction recorded: {agent_id} -> {crime_id}")

        return conviction

    async def get_history(self, agent_id: str) -> Optional[CriminalHistory]:
        """Get criminal history for an agent."""
        if agent_id in self._cache:
            return self._cache[agent_id]

        try:
            client = await self._get_redis_client()
            if client:
                key = f"{self._redis_prefix}{agent_id}"
                records = await client.lrange(key, 0, -1)
                if records:
                    convictions = [Conviction.from_dict(json.loads(r)) for r in records]
                    convictions.sort(key=lambda c: c.timestamp)

                    history = CriminalHistory(
                        agent_id=agent_id,
                        convictions=convictions,
                        first_offense_date=convictions[0].timestamp if convictions else None,
                        last_offense_date=convictions[-1].timestamp if convictions else None,
                    )

                    self._cache[agent_id] = history
                    return history
        except Exception as e:
            logger.warning(f"Failed to read history from Redis: {e}")

        return None

    async def get_recidivism_factor(self, agent_id: str) -> float:
        """Get recidivism aggravating factor for sentencing."""
        history = await self.get_history(agent_id)
        if history is None:
            return 1.0
        return history.calculate_recidivism_factor()

    async def get_prior_offense_count(self, agent_id: str) -> int:
        """Get total prior offense count."""
        history = await self.get_history(agent_id)
        if history is None:
            return 0
        return history.prior_offenses

    async def get_pillar_violation_count(self, agent_id: str, pillar: str) -> int:
        """Get violation count for a specific pillar."""
        history = await self.get_history(agent_id)
        if history is None:
            return 0
        return history.get_pillar_violations(pillar)

    async def is_repeat_offender(self, agent_id: str, crime_id: str) -> bool:
        """Check if agent is a repeat offender for a specific crime."""
        history = await self.get_history(agent_id)
        if history is None:
            return False
        return history.get_crime_count(crime_id) > 0

    async def clear_history(self, agent_id: str) -> bool:
        """Clear criminal history for an agent."""
        if agent_id not in self._cache:
            return False

        del self._cache[agent_id]

        try:
            client = await self._get_redis_client()
            if client:
                key = f"{self._redis_prefix}{agent_id}"
                await client.delete(key)
        except Exception as e:
            logger.warning(f"Failed to clear history from Redis: {e}")

        self._save_backup()
        logger.info(f"Criminal history cleared: {agent_id}")
        return True

    async def health_check(self) -> Dict[str, Any]:
        """Check provider health."""
        redis_healthy = False

        try:
            client = await self._get_redis_client()
            if client:
                await client.ping()
                redis_healthy = True
        except Exception:
            pass

        return {
            "healthy": True,
            "redis_available": redis_healthy,
            "redis_url": self._redis_url,
            "backup_path": str(self._backup_path),
            "cached_agents": len(self._cache),
            "total_convictions": sum(h.prior_offenses for h in self._cache.values()),
        }

    async def close(self) -> None:
        """Close connections."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None

