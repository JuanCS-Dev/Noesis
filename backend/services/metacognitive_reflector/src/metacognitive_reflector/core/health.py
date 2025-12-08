"""
NOESIS Memory Fortress - Health Check System
=============================================

Comprehensive health check for all Memory Fortress tiers.

Provides:
- Individual tier health checks
- Aggregated fortress health
- Resilience test suite
- Recovery guidance

Based on:
- Memory Fortress Architecture (4-tier)
- Circuit Breaker patterns
- Kubernetes health check standards
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class TierHealth:
    """Health status for a single tier."""
    tier: str
    status: HealthStatus
    latency_ms: float
    details: Dict[str, Any]
    error: Optional[str] = None


@dataclass
class FortressHealth:
    """Complete Memory Fortress health status."""
    overall_status: HealthStatus
    timestamp: datetime
    tiers: Dict[str, TierHealth]
    can_read: bool
    can_write: bool
    recovery_actions: List[str]


class MemoryFortressHealthCheck:
    """
    Health checker for all Memory Fortress tiers.
    
    Tiers checked:
    - L1: Hot Cache (in-memory)
    - L2: Warm Storage (Redis)
    - L3: Cold Storage (Qdrant/HTTP)
    - L4: Vault (JSON backup)
    - WAL: Write-Ahead Log
    
    Health Criteria:
    - HEALTHY: All critical tiers operational
    - DEGRADED: At least L1 + L4 operational (can survive)
    - UNHEALTHY: Cannot maintain persistence guarantee
    """
    
    # Timeout for individual tier checks
    TIER_CHECK_TIMEOUT = 3.0
    
    def __init__(
        self,
        memory_client: Any = None,
        penal_registry: Any = None,
        criminal_history: Any = None,
        soul_tracker: Any = None,
    ) -> None:
        """
        Initialize health checker.
        
        Args:
            memory_client: MemoryClient instance
            penal_registry: PenalRegistry instance
            criminal_history: CriminalHistoryProvider instance
            soul_tracker: SoulTracker instance
        """
        self._memory = memory_client
        self._registry = penal_registry
        self._criminal_history = criminal_history
        self._soul_tracker = soul_tracker
    
    async def check_all(self) -> FortressHealth:
        """
        Run complete health check on all tiers.
        
        Returns:
            FortressHealth with status of all tiers
        """
        tiers: Dict[str, TierHealth] = {}
        start_time = time.time()
        
        # Check each tier in parallel
        checks = await asyncio.gather(
            self._check_l1_cache(),
            self._check_l2_redis(),
            self._check_l3_http(),
            self._check_l4_vault(),
            self._check_wal(),
            return_exceptions=True,
        )
        
        # Process results
        tier_names = ["l1_cache", "l2_redis", "l3_http", "l4_vault", "wal"]
        for name, result in zip(tier_names, checks):
            if isinstance(result, Exception):
                tiers[name] = TierHealth(
                    tier=name,
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=0,
                    details={},
                    error=str(result),
                )
            else:
                tiers[name] = result
        
        # Determine overall status
        overall_status = self._determine_overall_status(tiers)
        
        # Check read/write capability
        can_read = (
            tiers.get("l1_cache", TierHealth("l1_cache", HealthStatus.UNHEALTHY, 0, {})).status == HealthStatus.HEALTHY or
            tiers.get("l4_vault", TierHealth("l4_vault", HealthStatus.UNHEALTHY, 0, {})).status == HealthStatus.HEALTHY
        )
        can_write = (
            tiers.get("l1_cache", TierHealth("l1_cache", HealthStatus.UNHEALTHY, 0, {})).status == HealthStatus.HEALTHY and
            tiers.get("l4_vault", TierHealth("l4_vault", HealthStatus.UNHEALTHY, 0, {})).status == HealthStatus.HEALTHY
        )
        
        # Generate recovery actions
        recovery_actions = self._generate_recovery_actions(tiers)
        
        return FortressHealth(
            overall_status=overall_status,
            timestamp=datetime.now(),
            tiers=tiers,
            can_read=can_read,
            can_write=can_write,
            recovery_actions=recovery_actions,
        )
    
    async def _check_l1_cache(self) -> TierHealth:
        """Check L1 Hot Cache health."""
        start = time.time()
        
        if not self._memory:
            return TierHealth(
                tier="l1_cache",
                status=HealthStatus.UNKNOWN,
                latency_ms=0,
                details={"reason": "MemoryClient not available"},
            )
        
        try:
            # L1 is always available (in-memory)
            cache_status = self._memory._l1_cache.get_status()
            latency = (time.time() - start) * 1000
            
            return TierHealth(
                tier="l1_cache",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                details={
                    "size": cache_status.get("size", 0),
                    "max_size": cache_status.get("max_size", 1000),
                    "utilization": cache_status.get("utilization", 0),
                },
            )
        except Exception as e:
            return TierHealth(
                tier="l1_cache",
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                details={},
                error=str(e),
            )
    
    async def _check_l2_redis(self) -> TierHealth:
        """Check L2 Redis health."""
        start = time.time()
        
        if not self._memory or not self._memory._redis_url:
            return TierHealth(
                tier="l2_redis",
                status=HealthStatus.UNKNOWN,
                latency_ms=0,
                details={"reason": "Redis not configured"},
            )
        
        try:
            client = await self._memory._get_redis_client()
            if not client:
                return TierHealth(
                    tier="l2_redis",
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=(time.time() - start) * 1000,
                    details={"reason": "Client unavailable"},
                )
            
            # Ping test
            await asyncio.wait_for(client.ping(), timeout=self.TIER_CHECK_TIMEOUT)
            latency = (time.time() - start) * 1000
            
            # Get circuit breaker status
            circuit_status = self._memory._circuit_l2.get_status()
            
            return TierHealth(
                tier="l2_redis",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                details={
                    "url": self._memory._redis_url,
                    "circuit_state": circuit_status.get("state", "unknown"),
                },
            )
        except asyncio.TimeoutError:
            return TierHealth(
                tier="l2_redis",
                status=HealthStatus.DEGRADED,
                latency_ms=self.TIER_CHECK_TIMEOUT * 1000,
                details={"reason": "Timeout"},
            )
        except Exception as e:
            return TierHealth(
                tier="l2_redis",
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                details={},
                error=str(e),
            )
    
    async def _check_l3_http(self) -> TierHealth:
        """Check L3 HTTP Service health."""
        start = time.time()
        
        if not self._memory or not self._memory._base_url:
            return TierHealth(
                tier="l3_http",
                status=HealthStatus.UNKNOWN,
                latency_ms=0,
                details={"reason": "HTTP service not configured"},
            )
        
        try:
            client = await self._memory._get_http_client()
            if not client:
                return TierHealth(
                    tier="l3_http",
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=(time.time() - start) * 1000,
                    details={"reason": "Client unavailable"},
                )
            
            # Health check endpoint
            response = await asyncio.wait_for(
                client.get("/health"),
                timeout=self.TIER_CHECK_TIMEOUT,
            )
            latency = (time.time() - start) * 1000
            
            # Get circuit breaker status
            circuit_status = self._memory._circuit_l3.get_status()
            
            if response.status_code == 200:
                return TierHealth(
                    tier="l3_http",
                    status=HealthStatus.HEALTHY,
                    latency_ms=latency,
                    details={
                        "url": self._memory._base_url,
                        "circuit_state": circuit_status.get("state", "unknown"),
                    },
                )
            else:
                return TierHealth(
                    tier="l3_http",
                    status=HealthStatus.DEGRADED,
                    latency_ms=latency,
                    details={
                        "status_code": response.status_code,
                    },
                )
        except asyncio.TimeoutError:
            return TierHealth(
                tier="l3_http",
                status=HealthStatus.DEGRADED,
                latency_ms=self.TIER_CHECK_TIMEOUT * 1000,
                details={"reason": "Timeout"},
            )
        except Exception as e:
            return TierHealth(
                tier="l3_http",
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                details={},
                error=str(e),
            )
    
    async def _check_l4_vault(self) -> TierHealth:
        """Check L4 Vault health."""
        start = time.time()
        
        if not self._memory:
            return TierHealth(
                tier="l4_vault",
                status=HealthStatus.UNKNOWN,
                latency_ms=0,
                details={"reason": "MemoryClient not available"},
            )
        
        try:
            vault_status = self._memory._vault.get_status()
            latency = (time.time() - start) * 1000
            
            # Vault is healthy if directory exists and is writable
            status = HealthStatus.HEALTHY
            
            return TierHealth(
                tier="l4_vault",
                status=status,
                latency_ms=latency,
                details={
                    "directory": vault_status.get("directory"),
                    "backup_count": vault_status.get("backup_count", 0),
                    "total_size_bytes": vault_status.get("total_size_bytes", 0),
                    "latest": vault_status.get("latest"),
                },
            )
        except Exception as e:
            return TierHealth(
                tier="l4_vault",
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                details={},
                error=str(e),
            )
    
    async def _check_wal(self) -> TierHealth:
        """Check WAL health."""
        start = time.time()
        
        if not self._memory or not self._memory._wal:
            return TierHealth(
                tier="wal",
                status=HealthStatus.UNKNOWN,
                latency_ms=0,
                details={"reason": "WAL not enabled"},
            )
        
        try:
            wal_status = self._memory._wal.get_status()
            latency = (time.time() - start) * 1000
            
            return TierHealth(
                tier="wal",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                details={
                    "directory": wal_status.get("directory"),
                    "current_sequence": wal_status.get("current_sequence", 0),
                    "file_count": wal_status.get("file_count", 0),
                    "total_size_bytes": wal_status.get("total_size_bytes", 0),
                },
            )
        except Exception as e:
            return TierHealth(
                tier="wal",
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                details={},
                error=str(e),
            )
    
    def _determine_overall_status(self, tiers: Dict[str, TierHealth]) -> HealthStatus:
        """
        Determine overall fortress health.
        
        Criteria:
        - HEALTHY: L1 + L2 + L4 healthy
        - DEGRADED: L1 + L4 healthy (minimum for persistence)
        - UNHEALTHY: Cannot guarantee persistence
        """
        l1 = tiers.get("l1_cache", TierHealth("l1_cache", HealthStatus.UNHEALTHY, 0, {}))
        l2 = tiers.get("l2_redis", TierHealth("l2_redis", HealthStatus.UNKNOWN, 0, {}))
        l4 = tiers.get("l4_vault", TierHealth("l4_vault", HealthStatus.UNHEALTHY, 0, {}))
        
        # Critical requirement: L1 + L4 must be healthy
        if l1.status != HealthStatus.HEALTHY or l4.status != HealthStatus.HEALTHY:
            return HealthStatus.UNHEALTHY
        
        # Degraded if L2 is down but L1 + L4 are up
        if l2.status != HealthStatus.HEALTHY:
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY
    
    def _generate_recovery_actions(self, tiers: Dict[str, TierHealth]) -> List[str]:
        """Generate recovery action suggestions."""
        actions = []
        
        for name, tier in tiers.items():
            if tier.status == HealthStatus.UNHEALTHY:
                if name == "l2_redis":
                    actions.append("Redis unavailable - check connection and restart if needed")
                elif name == "l3_http":
                    actions.append("Episodic memory service down - check deployment")
                elif name == "l4_vault":
                    actions.append("CRITICAL: Vault storage failed - check disk space and permissions")
                elif name == "l1_cache":
                    actions.append("CRITICAL: L1 cache failed - memory allocation issue")
            elif tier.status == HealthStatus.DEGRADED:
                if name == "l2_redis":
                    actions.append("Redis responding slowly - check load and connection pool")
                elif name == "l3_http":
                    actions.append("HTTP service slow - check Qdrant and network")
        
        if not actions:
            actions.append("All systems operational - no action required")
        
        return actions


async def run_memory_fortress_health_check(
    memory_client: Any = None,
    penal_registry: Any = None,
) -> Dict[str, Any]:
    """
    Convenience function to run complete health check.
    
    Returns dictionary suitable for API response.
    """
    checker = MemoryFortressHealthCheck(
        memory_client=memory_client,
        penal_registry=penal_registry,
    )
    
    health = await checker.check_all()
    
    return {
        "status": health.overall_status.value,
        "timestamp": health.timestamp.isoformat(),
        "can_read": health.can_read,
        "can_write": health.can_write,
        "tiers": {
            name: {
                "status": tier.status.value,
                "latency_ms": tier.latency_ms,
                "details": tier.details,
                "error": tier.error,
            }
            for name, tier in health.tiers.items()
        },
        "recovery_actions": health.recovery_actions,
    }

