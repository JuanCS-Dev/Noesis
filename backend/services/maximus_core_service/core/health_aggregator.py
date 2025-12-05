"""
Maximus Core Service - Health Aggregator
========================================

Aggregates health status from all Maximus services.
"""

from __future__ import annotations


from datetime import datetime
from typing import Dict

from ..models.system import ServiceHealth, SystemStatus
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class HealthAggregator:
    """
    Aggregates health status from multiple services.

    Attributes:
        service_healths: Cache of service health statuses
    """

    def __init__(self) -> None:
        """Initialize Health Aggregator."""
        self.service_healths: Dict[str, ServiceHealth] = {}
        logger.info("health_aggregator_initialized")

    async def update_service_health(
        self,
        service_name: str,
        status: str,
        details: Dict[str, str] | None = None
    ) -> None:
        """
        Update health status for a service.

        Args:
            service_name: Name of the service
            status: Health status (healthy, degraded, unhealthy)
            details: Optional additional details
        """
        health = ServiceHealth(
            service_name=service_name,
            status=status,
            timestamp=datetime.now(),
            details=details or {}
        )
        self.service_healths[service_name] = health
        logger.debug(
            "service_health_updated",
            service=service_name,
            status=status
        )

    async def get_system_status(self) -> SystemStatus:
        """
        Get aggregated system health status.

        Returns:
            System status with all service healths
        """
        total = len(self.service_healths)
        healthy = sum(
            1 for h in self.service_healths.values()
            if h.status == "healthy"
        )

        overall_status = "healthy" if healthy == total else (
            "degraded" if healthy > 0 else "unhealthy"
        )

        return SystemStatus(
            status=overall_status,
            timestamp=datetime.now(),
            services=self.service_healths.copy(),
            total_services=total,
            healthy_services=healthy
        )
