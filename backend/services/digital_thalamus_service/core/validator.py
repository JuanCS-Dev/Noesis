"""
Digital Thalamus Service - Request Validator
============================================

Request validation and sanitization logic.
"""

from __future__ import annotations


from typing import Any, Dict

from models.gateway import GatewayRequest
from utils.logging_config import get_logger

logger = get_logger(__name__)


class RequestValidator:
    """
    Validates and sanitizes incoming requests.

    Ensures requests meet security and format requirements.
    """

    def __init__(self) -> None:
        """Initialize Request Validator."""
        logger.info("request_validator_initialized")

    async def validate_request(self, request: GatewayRequest) -> bool:
        """
        Validate incoming request.

        Args:
            request: Gateway request to validate

        Returns:
            True if request is valid, False otherwise
        """
        # Validate HTTP method
        valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH"}
        if request.method.upper() not in valid_methods:
            logger.warning(
                "invalid_http_method",
                method=request.method
            )
            return False

        # Validate path
        if not request.path or not request.path.startswith("/"):
            logger.warning(
                "invalid_request_path",
                path=request.path
            )
            return False

        logger.debug(
            "request_validated",
            method=request.method,
            path=request.path
        )
        return True

    async def sanitize_headers(
        self,
        headers: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Sanitize request headers.

        Removes potentially dangerous headers.

        Args:
            headers: Request headers

        Returns:
            Sanitized headers
        """
        # Headers to remove for security
        dangerous_headers = {
            "X-Forwarded-For",
            "X-Real-IP"
        }

        sanitized = {
            k: v for k, v in headers.items()
            if k not in dangerous_headers
        }

        return sanitized

    async def validate_body(self, body: Dict[str, Any] | None) -> bool:
        """
        Validate request body.

        Args:
            body: Request body to validate

        Returns:
            True if body is valid
        """
        # For now, accept any valid JSON or None
        if body is None:
            return True

        # Could add more validation rules here
        return isinstance(body, dict)
