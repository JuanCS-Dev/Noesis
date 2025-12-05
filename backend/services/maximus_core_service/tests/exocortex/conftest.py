"""
Fixtures for Exocortex Tests
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from services.maximus_core_service.src.consciousness.exocortex.factory import ExocortexFactory

@pytest.fixture
def mock_gemini():
    """Mock GeminiClient within the Factory."""
    mock = MagicMock()
    mock.generate_text = AsyncMock()
    return mock

@pytest.fixture
def test_factory(mock_gemini, tmp_path):
    """Initialize a test factory with temp data dir."""
    ExocortexFactory._instance = None # Reset singleton
    factory = ExocortexFactory.initialize(data_dir=str(tmp_path))
    factory.gemini_client = mock_gemini
    
    # Inject Mock into Guardian and Engine manually since they were init'd in __init__
    factory.guardian.gemini_client = mock_gemini
    factory.confrontation_engine.gemini_client = mock_gemini
    factory.inhibitor.client = mock_gemini
    factory.thalamus.client = mock_gemini
    
    return factory
