"""
Digital Thalamus Service - Request Router
=========================================

Core routing logic for directing requests to services.
"""

from __future__ import annotations


from typing import Dict

from digital_thalamus_service.config import GatewaySettings
from digital_thalamus_service.models.gateway import RouteConfig
from digital_thalamus_service.utils.logging_config import get_logger

logger = get_logger(__name__)


class RequestRouter:
    """
    Routes requests to appropriate backend services.

    Manages service discovery and request forwarding.

    Attributes:
        settings: Gateway settings
        routes: Mapping of path prefixes to service configurations
    """

    def __init__(self, settings: GatewaySettings):
        """
        Initialize Request Router.

        Args:
            settings: Gateway settings
        """
        self.settings = settings
        self.routes: Dict[str, RouteConfig] = {}
        self._initialize_routes()
        logger.info(
            "request_router_initialized",
            num_routes=len(self.routes)
        )

    def _initialize_routes(self) -> None:
        """Initialize default routes to internal services."""
        # Define routes to other Maximus services
        default_routes = {
            "/v1/core": RouteConfig(
                service_name="maximus-core-service",
                base_url="http://maximus-core-service:8000",
                timeout=self.settings.request_timeout
            ),
            "/v1/hcl/planner": RouteConfig(
                service_name="hcl-planner-service",
                base_url="http://hcl-planner-service:8000",
                timeout=self.settings.request_timeout
            ),
            "/v1/hcl/executor": RouteConfig(
                service_name="hcl-executor-service",
                base_url="http://hcl-executor-service:8000",
                timeout=self.settings.request_timeout
            ),
            "/v1/hcl/analyzer": RouteConfig(
                service_name="hcl-analyzer-service",
                base_url="http://hcl-analyzer-service:8000",
                timeout=self.settings.request_timeout
            ),
            "/v1/hcl/monitor": RouteConfig(
                service_name="hcl-monitor-service",
                base_url="http://hcl-monitor-service:8000",
                timeout=self.settings.request_timeout
            )
        }
        self.routes.update(default_routes)

    async def find_route(self, path: str) -> RouteConfig | None:
        """
        Find route configuration for a given path.

        Args:
            path: Request path

        Returns:
            Route configuration if found, None otherwise
        """
        # Try exact match first
        if path in self.routes:
            return self.routes[path]

        # Try prefix matching (find longest matching prefix)
        matching_routes = [
            (prefix, config)
            for prefix, config in self.routes.items()
            if path.startswith(prefix)
        ]

        if matching_routes:
            # Return route with longest matching prefix
            _, config = max(matching_routes, key=lambda x: len(x[0]))
            logger.debug(
                "route_found",
                path=path,
                service=config.service_name
            )
            return config

        logger.warning("no_route_found", path=path)
        return None

    async def register_route(
        self,
        prefix: str,
        config: RouteConfig
    ) -> None:
        """
        Register a new route.

        Args:
            prefix: Path prefix for the route
            config: Route configuration
        """
        self.routes[prefix] = config
        logger.info(
            "route_registered",
            prefix=prefix,
            service=config.service_name
        )
