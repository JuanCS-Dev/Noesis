"""
HCL Planner Service - Constants Module
======================================

All magic numbers and configuration constants.
Each constant includes rationale for its value.
"""

from __future__ import annotations

# Gemini API Configuration
GEMINI_MAX_TOKENS = 8192
"""Maximum output tokens for Gemini responses.
Rationale: Sufficient for deep reasoning traces in thinking mode."""

GEMINI_TIMEOUT_SECONDS = 120
"""Request timeout for Gemini API calls.
Rationale: Allows for thinking mode processing which can take 30-60s."""

GEMINI_DEFAULT_TEMPERATURE = 0.7
"""Default sampling temperature for Gemini.
Rationale: Balanced between creativity (1.0) and determinism (0.0)."""

# Service Configuration
DEFAULT_SERVICE_NAME = "hcl-planner"
"""Default service identifier."""

DEFAULT_LOG_LEVEL = "INFO"
"""Default logging level."""

# HTTP Status Codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_ERROR = 500
HTTP_SERVICE_UNAVAILABLE = 503
