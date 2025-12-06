"""
Ethical Audit Service - API Dependencies
========================================

Dependency injection for FastAPI endpoints.
"""

from __future__ import annotations


from ethical_audit_service.config import Settings, get_settings
from ethical_audit_service.core.constitutional_validator import ConstitutionalValidator
from ethical_audit_service.core.violation_detector import ViolationDetector
from ethical_audit_service.utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)

# Global instances
_validator: ConstitutionalValidator | None = None
_detector: ViolationDetector | None = None


def get_cached_settings() -> Settings:
    """Dependency to get cached settings."""
    return get_settings()


def initialize_service() -> None:
    """Initialize service components."""
    settings = get_cached_settings()

    # Setup logging
    setup_logging(settings.service.log_level)  # pylint: disable=no-member

    logger.info(
        "service_initializing",
        service_name=settings.service.name,  # pylint: disable=no-member
        log_level=settings.service.log_level  # pylint: disable=no-member
    )

    # Initialize core components
    global _validator  # pylint: disable=global-statement
    global _detector  # pylint: disable=global-statement

    _validator = ConstitutionalValidator(settings.audit)
    _detector = ViolationDetector(settings.audit)


async def get_validator() -> ConstitutionalValidator:
    """Dependency to get the validator instance."""
    if _validator is None:
        raise RuntimeError(
            "Validator not initialized. Call initialize_service() first."
        )
    return _validator


async def get_detector() -> ViolationDetector:
    """Dependency to get the detector instance."""
    if _detector is None:
        raise RuntimeError(
            "Detector not initialized. Call initialize_service() first."
        )
    return _detector
