"""
Comprehensive Tests for Validation - Coherence and Metacognition
=================================================================

Tests for ESGT coherence validation and metacognitive monitoring.
"""

import time

import pytest

from consciousness.validation.coherence import (
    CoherenceValidator,
    CoherenceQuality,
    ESGTCoherenceMetrics,
    GWDCompliance,
)
from consciousness.validation.metacognition import MetacognitionValidator


# =============================================================================
# COHERENCE QUALITY TESTS
# =============================================================================


class TestCoherenceQuality:
    """Test CoherenceQuality enum."""

    def test_quality_levels(self):
        """All quality levels should exist."""
        assert CoherenceQuality.POOR
        assert CoherenceQuality.MODERATE
        assert CoherenceQuality.GOOD
        assert CoherenceQuality.EXCELLENT


# =============================================================================
# ESGT COHERENCE METRICS TESTS
# =============================================================================


class TestESGTCoherenceMetrics:
    """Test ESGTCoherenceMetrics data structure."""

    def test_default_values(self):
        """Default values should be sensible."""
        metrics = ESGTCoherenceMetrics()
        
        assert metrics.quality == CoherenceQuality.POOR
        assert metrics.is_conscious_level is False
        assert metrics.passes_gwd_criteria is False

    def test_creation_with_values(self):
        """Metrics should accept custom values."""
        metrics = ESGTCoherenceMetrics(
            mean_coherence=0.85,
            broadcast_latency_ms=10.0,
            broadcast_coverage=0.75,
            total_duration_ms=150.0,
        )
        
        assert metrics.mean_coherence == 0.85
        assert metrics.broadcast_coverage == 0.75


# =============================================================================
# GWD COMPLIANCE TESTS
# =============================================================================


class TestGWDCompliance:
    """Test GWDCompliance data structure."""

    def test_default_not_compliant(self):
        """Default should be non-compliant."""
        compliance = GWDCompliance()
        
        assert compliance.is_compliant is False
        assert compliance.compliance_score == 0.0

    def test_get_summary(self):
        """Summary should be generated."""
        compliance = GWDCompliance(
            is_compliant=True,
            compliance_score=95.0,
            coherence_pass=True,
            latency_pass=True,
            coverage_pass=True,
            duration_pass=True,
            stability_pass=True,
        )
        
        summary = compliance.get_summary()
        
        assert isinstance(summary, str)
        assert len(summary) > 0


# =============================================================================
# COHERENCE VALIDATOR TESTS
# =============================================================================


class TestCoherenceValidatorInit:
    """Test CoherenceValidator initialization."""

    def test_default_thresholds(self):
        """Default thresholds should be sensible."""
        validator = CoherenceValidator()
        
        assert validator.coherence_threshold > 0
        assert validator.latency_threshold > 0  # This is the correct attribute name
        assert validator.coverage_threshold > 0

    def test_custom_thresholds(self):
        """Custom thresholds should be accepted."""
        validator = CoherenceValidator(
            coherence_threshold=0.80,
            latency_threshold_ms=20.0,  # Constructor uses _ms suffix
        )
        
        assert validator.coherence_threshold == 0.80
        assert validator.latency_threshold == 20.0  # Stored without _ms suffix


class TestCoherenceValidatorClassify:
    """Test quality classification."""

    def test_classify_poor(self):
        """Very low coherence should be POOR (< 0.30)."""
        validator = CoherenceValidator()
        
        quality = validator._classify_quality(0.2)
        
        assert quality == CoherenceQuality.POOR

    def test_classify_moderate(self):
        """Medium coherence should be MODERATE (0.30 - 0.70)."""
        validator = CoherenceValidator()
        
        quality = validator._classify_quality(0.5)
        
        assert quality == CoherenceQuality.MODERATE

    def test_classify_good(self):
        """High coherence should be GOOD (0.70 - 0.90)."""
        validator = CoherenceValidator()
        
        quality = validator._classify_quality(0.8)
        
        assert quality == CoherenceQuality.GOOD

    def test_classify_excellent(self):
        """Very high coherence should be EXCELLENT (>= 0.90)."""
        validator = CoherenceValidator()
        
        quality = validator._classify_quality(0.95)
        
        assert quality == CoherenceQuality.EXCELLENT


class TestCoherenceValidatorValidation:
    """Test GWD validation."""

    def test_validate_gwd_with_metrics(self):
        """validate_gwd should return compliance."""
        validator = CoherenceValidator()
        
        metrics = ESGTCoherenceMetrics(
            mean_coherence=0.85,
            broadcast_latency_ms=10.0,
            broadcast_coverage=0.75,
            total_duration_ms=150.0,
            coherence_cv=0.1,
        )
        
        compliance = validator.validate_gwd(metrics)
        
        assert isinstance(compliance, GWDCompliance)

    def test_validate_gwd_all_passing(self):
        """All passing criteria should be compliant."""
        validator = CoherenceValidator()
        
        metrics = ESGTCoherenceMetrics(
            mean_coherence=0.90,
            prepare_latency_ms=2.0,
            sync_latency_ms=3.0,
            broadcast_latency_ms=5.0,
            broadcast_coverage=0.80,
            total_duration_ms=150.0,
            coherence_cv=0.1,
        )
        
        compliance = validator.validate_gwd(metrics)
        
        # High scores should be compliant
        assert compliance.compliance_score > 50


# =============================================================================
# METACOGNITION VALIDATOR TESTS
# =============================================================================


class TestMetacognitionValidatorInit:
    """Test MetacognitionValidator initialization."""

    def test_default_config(self):
        """Default config should be sensible."""
        validator = MetacognitionValidator()
        
        assert validator is not None
