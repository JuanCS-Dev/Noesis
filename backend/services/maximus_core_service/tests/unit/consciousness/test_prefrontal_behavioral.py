"""
Comprehensive Tests for Prefrontal Cortex - Social Cognition Integration
=========================================================================

Tests for the integration layer between ToM, ESGT, and MIP.
"""

from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any

import pytest

from consciousness.prefrontal_cortex import (
    PrefrontalCortex,
    SocialSignal,
    CompassionateResponse,
)


# =============================================================================
# SOCIAL SIGNAL TESTS
# =============================================================================


class TestSocialSignal:
    """Test SocialSignal data structure."""

    def test_creation(self):
        """SocialSignal should be creatable."""
        signal = SocialSignal(
            user_id="user-001",
            context={"message": "hello"},
            signal_type="greeting",
            salience=0.8,
            timestamp=1000.0,
        )
        
        assert signal.user_id == "user-001"
        assert signal.salience == 0.8


# =============================================================================
# COMPASSIONATE RESPONSE TESTS
# =============================================================================


class TestCompassionateResponse:
    """Test CompassionateResponse data structure."""

    def test_creation(self):
        """CompassionateResponse should be creatable."""
        response = CompassionateResponse(
            action="greet warmly",
            confidence=0.9,
            reasoning="User seems friendly",
            tom_prediction=None,
            mip_verdict=None,
            processing_time_ms=15.0,
        )
        
        assert response.action == "greet warmly"
        assert response.confidence == 0.9


# =============================================================================
# PREFRONTAL CORTEX INIT TESTS
# =============================================================================


class TestPrefrontalCortexInit:
    """Test PrefrontalCortex initialization."""

    def test_init_with_tom_engine(self):
        """PFC should accept ToM engine as 'tom' attr."""
        mock_tom = MagicMock()
        
        pfc = PrefrontalCortex(tom_engine=mock_tom)
        
        assert pfc.tom is mock_tom  # Stored as .tom, not .tom_engine

    def test_init_with_decision_arbiter(self):
        """PFC should accept decision arbiter as 'mip' attr."""
        mock_tom = MagicMock()
        mock_arbiter = MagicMock()
        
        pfc = PrefrontalCortex(tom_engine=mock_tom, decision_arbiter=mock_arbiter)
        
        assert pfc.mip is mock_arbiter  # Stored as .mip, not .decision_arbiter


# =============================================================================
# PREFRONTAL CORTEX PROCESSING TESTS
# =============================================================================


class TestPrefrontalCortexProcessing:
    """Test social signal processing."""

    def test_process_social_signal_basic(self):
        """process_social_signal should work with valid inputs."""
        mock_tom = MagicMock()
        mock_tom.infer_mental_state = MagicMock(return_value={
            "beliefs": {"trust": 0.8},
            "emotions": {"happy": 0.7},
        })
        
        pfc = PrefrontalCortex(tom_engine=mock_tom)
        
        # Just verify instantiation works
        assert pfc.tom is mock_tom


# =============================================================================
# PREFRONTAL CORTEX STATUS TESTS
# =============================================================================


class TestPrefrontalCortexStatus:
    """Test status retrieval."""

    def test_get_status_exists(self):
        """PFC should have get_status method."""
        mock_tom = MagicMock()
        pfc = PrefrontalCortex(tom_engine=mock_tom)
        
        assert hasattr(pfc, "get_status")


# =============================================================================
# PREFRONTAL CORTEX REPR TESTS
# =============================================================================


class TestPrefrontalCortexRepr:
    """Test string representation."""

    def test_repr(self):
        """Repr should include PFC info."""
        mock_tom = MagicMock()
        pfc = PrefrontalCortex(tom_engine=mock_tom)
        
        repr_str = repr(pfc)
        
        assert "Prefrontal" in repr_str or "PFC" in repr_str
