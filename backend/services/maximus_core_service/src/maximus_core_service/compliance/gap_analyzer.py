"""Shim for compliance.gap_analyzer."""
from .base_legacy import GapAnalysisResult as GapAnalyzer, Gap

__all__ = ["GapAnalyzer", "Gap"]
