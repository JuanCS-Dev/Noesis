"""Core Article II Guardian Implementation."""

from __future__ import annotations

from ..base import ConstitutionalArticle, GuardianAgent
from .analyzer import AnalyzerMixin
from .file_checker import FileCheckerMixin
from .git_checker import GitCheckerMixin
from .helpers import HelperMethodsMixin
from .intervener import IntervenerMixin
from .monitor import MonitorMixin
from .patterns import GuardianPatterns
from .pr_scanner import PRScannerMixin
from .test_checker import TestCheckerMixin


class ArticleIIGuardian(
    GuardianPatterns,
    MonitorMixin,
    FileCheckerMixin,
    TestCheckerMixin,
    GitCheckerMixin,
    HelperMethodsMixin,
    AnalyzerMixin,
    IntervenerMixin,
    PRScannerMixin,
    GuardianAgent,
):
    """
    Guardian that enforces Article II: The Sovereign Quality Standard.

    Monitors codebase for:
    - Mock implementations
    - Placeholder code
    - TODO/FIXME comments
    - Skipped tests
    - Technical debt markers
    - Incomplete implementations

    Inherits from:
        - GuardianPatterns: Detection patterns
        - MonitorMixin: Main monitoring loop
        - FileCheckerMixin: File checking logic
        - TestCheckerMixin: Test health checks
        - GitCheckerMixin: Git status checks
        - HelperMethodsMixin: Utility methods
        - AnalyzerMixin: Violation analysis
        - IntervenerMixin: Intervention actions
        - PRScannerMixin: Pull request scanning
    """

    def __init__(self) -> None:
        """Initialize Article II Guardian."""
        GuardianAgent.__init__(
            self,
            guardian_id="guardian-article-ii",
            article=ConstitutionalArticle.ARTICLE_II,
            name="Sovereign Quality Guardian",
            description=(
                "Enforces the Sovereign Quality Standard (Padrão Pagani), "
                "ensuring all code is production-ready without mocks, "
                "placeholders, or technical debt."
            ),
        )
