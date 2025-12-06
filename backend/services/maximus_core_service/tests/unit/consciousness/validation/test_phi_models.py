"""Tests for validation/phi_models.py"""

from consciousness.validation.phi_models import PhiProxyMetrics, StructuralCompliance


class TestPhiProxyMetrics:
    """Test PhiProxyMetrics dataclass."""

    def test_creation_defaults(self):
        """Test creating metrics with defaults."""
        metrics = PhiProxyMetrics()

        assert metrics.effective_connectivity_index == 0.0
        assert metrics.clustering_coefficient == 0.0
        assert metrics.avg_path_length == 0.0
        assert metrics.has_bottlenecks is True
        assert metrics.bottleneck_count == 0
        assert metrics.node_count == 0

    def test_creation_complete(self):
        """Test creating metrics with all fields."""
        metrics = PhiProxyMetrics(
            effective_connectivity_index=0.90,
            clustering_coefficient=0.80,
            avg_path_length=2.5,
            algebraic_connectivity=0.45,
            has_bottlenecks=False,
            bottleneck_count=0,
            bottleneck_locations=[],
            min_path_redundancy=5,
            small_world_sigma=1.2,
            integration_differentiation_balance=0.85,
            phi_proxy_estimate=0.88,
            iit_compliance_score=92.0,
            node_count=100,
            edge_count=450,
        )

        assert metrics.effective_connectivity_index == 0.90
        assert metrics.clustering_coefficient == 0.80
        assert metrics.iit_compliance_score == 92.0
        assert metrics.node_count == 100


class TestStructuralCompliance:
    """Test StructuralCompliance dataclass."""

    def test_creation_defaults(self):
        """Test creating compliance with defaults."""
        compliance = StructuralCompliance()

        assert compliance.is_compliant is False
        assert compliance.compliance_score == 0.0
        assert compliance.violations == []
        assert compliance.warnings == []
        assert compliance.eci_pass is False

    def test_creation_compliant(self):
        """Test creating compliant structure."""
        compliance = StructuralCompliance(
            is_compliant=True,
            compliance_score=95.0,
            eci_pass=True,
            clustering_pass=True,
            path_length_pass=True,
            algebraic_connectivity_pass=True,
            bottleneck_pass=True,
            redundancy_pass=True,
        )

        assert compliance.is_compliant is True
        assert compliance.compliance_score == 95.0
        assert compliance.eci_pass is True
        assert compliance.clustering_pass is True

    def test_creation_with_violations(self):
        """Test creating compliance with violations."""
        compliance = StructuralCompliance(
            is_compliant=False,
            compliance_score=45.0,
            violations=["Low ECI", "Bottleneck detected"],
            warnings=["High drift"],
            eci_pass=False,
            bottleneck_pass=False,
        )

        assert len(compliance.violations) == 2
        assert "Low ECI" in compliance.violations
        assert len(compliance.warnings) == 1

    def test_get_summary_compliant(self):
        """Test summary for compliant structure."""
        compliance = StructuralCompliance(
            is_compliant=True,
            compliance_score=98.5,
            eci_pass=True,
            clustering_pass=True,
            path_length_pass=True,
            algebraic_connectivity_pass=True,
            bottleneck_pass=True,
            redundancy_pass=True,
        )

        summary = compliance.get_summary()

        assert "✅ COMPLIANT" in summary
        assert "98.5/100" in summary
        assert "✓" in summary

    def test_get_summary_non_compliant(self):
        """Test summary for non-compliant structure."""
        compliance = StructuralCompliance(
            is_compliant=False,
            compliance_score=40.0,
            violations=["Low clustering", "Bottleneck at layer 3"],
            warnings=["High path length"],
            eci_pass=True,
            clustering_pass=False,
            path_length_pass=False,
            algebraic_connectivity_pass=True,
            bottleneck_pass=False,
            redundancy_pass=True,
        )

        summary = compliance.get_summary()

        assert "❌ NON-COMPLIANT" in summary
        assert "40.0/100" in summary
        assert "Low clustering" in summary
        assert "Bottleneck at layer 3" in summary
        assert "High path length" in summary
        assert "✗" in summary

    def test_get_summary_with_warnings_only(self):
        """Test summary with warnings but no violations."""
        compliance = StructuralCompliance(
            is_compliant=True,
            compliance_score=85.0,
            warnings=["Near threshold for ECI"],
            eci_pass=True,
            clustering_pass=True,
            path_length_pass=True,
            algebraic_connectivity_pass=True,
            bottleneck_pass=True,
            redundancy_pass=True,
        )

        summary = compliance.get_summary()

        assert "✅ COMPLIANT" in summary
        assert "⚠️" in summary
        assert "Near threshold" in summary
