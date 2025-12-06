"""
Maximus Core Service - System Coordinator
=========================================

Core coordination logic for managing Maximus subsystems.
"""

from __future__ import annotations


from typing import List

from config import CoordinationSettings
from utils.logging_config import get_logger

logger = get_logger(__name__)


class SystemCoordinator:
    """
    Coordinates Maximus subsystems.

    Manages initialization, health monitoring, and inter-service communication.

    Attributes:
        settings: Coordination settings
        registered_services: List of registered service names
    """

    def __init__(self, settings: CoordinationSettings):
        """
        Initialize System Coordinator.

        Args:
            settings: Coordination settings
        """
        self.settings = settings
        self.registered_services: List[str] = []
        logger.info(
            "coordinator_initialized",
            health_check_interval=settings.health_check_interval,
            service_timeout=settings.service_timeout
        )

    async def register_service(self, service_name: str) -> None:
        """
        Register a service with the coordinator.

        Args:
            service_name: Name of service to register
        """
        if service_name not in self.registered_services:
            self.registered_services.append(service_name)
            logger.info("service_registered", service=service_name)

    async def unregister_service(self, service_name: str) -> None:
        """
        Unregister a service from the coordinator.

        Args:
            service_name: Name of service to unregister
        """
        if service_name in self.registered_services:
            self.registered_services.remove(service_name)
            logger.info("service_unregistered", service=service_name)

    def get_registered_services(self) -> List[str]:
        """
        Get list of registered services.

        Returns:
            List of service names
        """
        return self.registered_services.copy()
