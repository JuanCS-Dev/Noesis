"""
MCP Server Configuration
========================

Pydantic-based configuration following 12-factor app principles.

Follows CODE_CONSTITUTION: Safety First, Clarity Over Cleverness.
"""

from __future__ import annotations


from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPServerConfig(BaseSettings):
    """Configuration for MCP Server.

    All settings can be overridden via environment variables.
    Follows 12-factor app configuration principles.

    Attributes:
        service_name: Service identifier
        service_port: Port to run the service on
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

        tribunal_url: URL for metacognitive_reflector service
        factory_url: URL for tool_factory_service
        memory_url: URL for episodic_memory service
        executor_url: URL for hcl_executor_service

        rate_limit_per_tool: Max calls per tool per window
        rate_limit_window: Time window in seconds for rate limiting

        circuit_breaker_threshold: Failures before opening circuit
        circuit_breaker_timeout: Seconds before attempting reset
        circuit_breaker_expected_exception: Exception type to track

        otel_enabled: Enable OpenTelemetry tracing
        otel_endpoint: OpenTelemetry collector endpoint
        otel_service_name: Service name for tracing

        http_timeout: Default HTTP client timeout
        http_max_connections: Max connections per host
        http_max_keepalive: Max keepalive connections
    """

    # Service configuration
    service_name: str = Field(default="mcp-server")
    service_port: int = Field(default=8106)
    log_level: str = Field(default="INFO")

    # Downstream service URLs (12-factor: config via env)
    tribunal_url: str = Field(
        default="http://localhost:8101",
        description="metacognitive_reflector service URL"
    )
    factory_url: str = Field(
        default="http://localhost:8105",
        description="tool_factory_service URL"
    )
    memory_url: str = Field(
        default="http://localhost:8103",
        description="episodic_memory service URL"
    )
    executor_url: str = Field(
        default="http://localhost:8104",
        description="hcl_executor_service URL"
    )

    # Rate limiting configuration
    rate_limit_per_tool: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Max calls per tool per window"
    )
    rate_limit_window: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Time window in seconds"
    )

    # Circuit breaker configuration
    circuit_breaker_threshold: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Failures before opening circuit"
    )
    circuit_breaker_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Seconds before reset attempt"
    )
    circuit_breaker_expected_exception: str = Field(
        default="Exception",
        description="Exception class name to track"
    )

    # OpenTelemetry configuration
    otel_enabled: bool = Field(
        default=False,
        description="Enable OpenTelemetry tracing"
    )
    otel_endpoint: str = Field(
        default="http://localhost:4318",
        description="OTLP collector endpoint"
    )
    otel_service_name: str = Field(
        default="maximus-mcp-server",
        description="Service name for tracing"
    )

    # MCP server configuration
    mcp_request_timeout: float = Field(
        default=120.0,
        ge=10.0,
        le=600.0,
        description="MCP request timeout for long operations (seconds)"
    )
    mcp_stateless_http: bool = Field(
        default=False,
        description="Use stateless HTTP for MCP (for load balancing)"
    )

    # HTTP client configuration
    http_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Default HTTP timeout in seconds"
    )
    http_max_connections: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Max connections per host"
    )
    http_max_keepalive: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Max keepalive connections"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v_upper

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="MCP_",
    )


def get_config() -> MCPServerConfig:
    """Get singleton configuration instance.

    Returns:
        MCPServerConfig instance

    Example:
        >>> config = get_config()
        >>> print(config.service_name)
        mcp-server
    """
    return MCPServerConfig()
