"""
HCL Executor Service - Configuration Module
===========================================

Pydantic-based configuration management.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class K8sSettings(BaseSettings):
    """
    Kubernetes configuration.

    Attributes:
        kubeconfig_path: Path to kubeconfig file
        context: Kubernetes context to use
        default_namespace: Default namespace for operations
    """

    kubeconfig_path: Optional[str] = Field(
        default=None,
        description="Path to kubeconfig file",
        alias="KUBE_CONFIG_PATH"
    )
    context: Optional[str] = Field(
        default=None,
        description="Kubernetes context",
        alias="KUBE_CONTEXT"
    )
    default_namespace: str = Field(
        default="default",
        description="Default namespace",
        alias="KUBE_DEFAULT_NAMESPACE"
    )

    class Config:  # pylint: disable=too-few-public-methods,missing-class-docstring
        env_file = ".env"
        env_file_encoding = "utf-8"


class ServiceSettings(BaseSettings):
    """
    General service configuration.

    Attributes:
        name: Service identifier
        log_level: Logging level
    """

    name: str = Field(
        default="hcl-executor",
        description="Service identifier",
        alias="SERVICE_NAME"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        alias="LOG_LEVEL"
    )

    class Config:  # pylint: disable=too-few-public-methods,missing-class-docstring
        env_file = ".env"
        env_file_encoding = "utf-8"


class Settings(BaseSettings):
    """
    Complete application settings.
    """

    service: ServiceSettings = Field(default_factory=ServiceSettings)
    k8s: K8sSettings = Field(default_factory=K8sSettings)

    class Config:  # pylint: disable=too-few-public-methods,missing-class-docstring
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """
    Get application settings.

    Returns:
        Settings: Application configuration
    """
    return Settings()
