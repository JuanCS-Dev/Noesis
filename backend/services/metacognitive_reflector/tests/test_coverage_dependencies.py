"""
Tests for API dependencies to achieve 100% coverage.
"""

from __future__ import annotations


import pytest
from unittest.mock import patch, MagicMock

from metacognitive_reflector.api.dependencies import (
    get_cached_settings,
    initialize_service,
    get_reflector,
    get_memory_client,
)
from metacognitive_reflector.config import Settings


class TestDependencies:
    """Tests for API dependencies."""

    def test_get_cached_settings(self):
        """Test get_cached_settings returns Settings."""
        settings = get_cached_settings()
        assert isinstance(settings, Settings)
        assert settings.service.name == "metacognitive-reflector"

    def test_initialize_service(self):
        """Test initialize_service sets up globals."""
        import metacognitive_reflector.api.dependencies as deps

        # Reset globals
        deps._reflector = None
        deps._memory_client = None

        initialize_service()

        assert deps._reflector is not None
        assert deps._memory_client is not None

    @pytest.mark.asyncio
    async def test_get_reflector_after_init(self):
        """Test get_reflector after initialization."""
        import metacognitive_reflector.api.dependencies as deps

        # Ensure initialized
        if deps._reflector is None:
            initialize_service()

        reflector = await get_reflector()
        assert reflector is not None

    @pytest.mark.asyncio
    async def test_get_reflector_not_initialized(self):
        """Test get_reflector raises when not initialized."""
        import metacognitive_reflector.api.dependencies as deps

        # Force not initialized
        old_reflector = deps._reflector
        deps._reflector = None

        try:
            with pytest.raises(RuntimeError, match="Reflector not initialized"):
                await get_reflector()
        finally:
            deps._reflector = old_reflector

    @pytest.mark.asyncio
    async def test_get_memory_client_after_init(self):
        """Test get_memory_client after initialization."""
        import metacognitive_reflector.api.dependencies as deps

        # Ensure initialized
        if deps._memory_client is None:
            initialize_service()

        client = await get_memory_client()
        assert client is not None

    @pytest.mark.asyncio
    async def test_get_memory_client_not_initialized(self):
        """Test get_memory_client raises when not initialized."""
        import metacognitive_reflector.api.dependencies as deps

        # Force not initialized
        old_client = deps._memory_client
        deps._memory_client = None

        try:
            with pytest.raises(RuntimeError, match="Memory client not initialized"):
                await get_memory_client()
        finally:
            deps._memory_client = old_client
