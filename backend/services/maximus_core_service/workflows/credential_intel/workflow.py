"""Credential Intelligence Workflow Orchestrator.

Main workflow class orchestrating credential exposure analysis.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import asdict
from datetime import datetime
from typing import Any
from uuid import uuid4

from ..ai_analyzer import AIAnalyzer
from .analysis import AnalysisMixin
from .enumeration import EnumerationMixin
from .models import (
    CredentialIntelReport,
    CredentialTarget,
    WorkflowStatus,
)
from .searches import SearchesMixin

logger = logging.getLogger(__name__)

_ACTIVE_WORKFLOWS: dict[str, Any] = {}


class CredentialIntelWorkflow(SearchesMixin, EnumerationMixin, AnalysisMixin):
    """Credential Intelligence AI-Driven Workflow.

    Orchestrates multiple OSINT services to discover credential exposure and risk.

    Attributes:
        osint_url: OSINT Service endpoint URL.
        active_workflows: Dictionary of active workflow reports.
        ai_analyzer: AI analyzer instance for credential analysis.
    """

    def __init__(
        self,
        osint_service_url: str = "http://localhost:8036",
    ) -> None:
        """Initialize credential intelligence workflow.

        Args:
            osint_service_url: OSINT Service endpoint.
        """
        self.osint_url = (
            osint_service_url
            if osint_service_url != "http://localhost:8036"
            else os.getenv("OSINT_SERVICE_URL", "http://localhost:8036")
        )
        self.active_workflows = _ACTIVE_WORKFLOWS
        self.ai_analyzer = AIAnalyzer()
        logger.info("CredentialIntelWorkflow initialized with AI analyzer")

    async def execute(self, target: CredentialTarget) -> CredentialIntelReport:
        """Execute credential intelligence workflow.

        Args:
            target: Target configuration.

        Returns:
            CredentialIntelReport with complete findings.
        """
        workflow_id = str(uuid4())
        started_at = datetime.utcnow().isoformat()

        report = CredentialIntelReport(
            workflow_id=workflow_id,
            target_email=target.email,
            target_username=target.username,
            status=WorkflowStatus.RUNNING,
            started_at=started_at,
            completed_at=None,
        )
        self.active_workflows[workflow_id] = report

        try:
            async with asyncio.timeout(120):
                logger.info(
                    f"Starting credential intelligence for "
                    f"{target.email or target.username} (workflow_id={workflow_id})"
                )

                await self._run_phases(target, report)

                report.status = WorkflowStatus.COMPLETED
                report.completed_at = datetime.utcnow().isoformat()

                logger.info(
                    f"Credential intelligence completed: {len(report.findings)} "
                    f"findings, exposure_score={report.exposure_score:.2f}"
                )

        except asyncio.TimeoutError:
            logger.error("Credential intelligence workflow timeout after 120s")
            report.status = WorkflowStatus.FAILED
            report.error = (
                "Workflow execution timeout (120s) - "
                "external services may be unreachable"
            )
            report.completed_at = datetime.utcnow().isoformat()
        except Exception as e:
            logger.error(f"Credential intelligence workflow failed: {e}")
            report.status = WorkflowStatus.FAILED
            report.error = str(e)
            report.completed_at = datetime.utcnow().isoformat()

        return report

    async def _run_phases(
        self, target: CredentialTarget, report: CredentialIntelReport
    ) -> None:
        """Run all workflow phases.

        Args:
            target: Target configuration.
            report: Report to populate.
        """
        # Phase 1: HIBP breach data search
        if target.email or target.username:
            breach_findings = await self._search_breaches(
                target.email, target.username
            )
            report.findings.extend(breach_findings)
            report.breach_count = len(breach_findings)
            logger.info(f"Phase 1: Found {len(breach_findings)} breaches")

        # Phase 2: Google dorking
        if target.include_dorking and (target.email or target.username):
            dork_findings = await self._google_dork_search(
                target.email, target.username
            )
            report.findings.extend(dork_findings)
            logger.info(f"Phase 2: Found {len(dork_findings)} dorking results")

        # Phase 3: Dark web monitoring
        if target.include_darkweb and (target.email or target.username):
            darkweb_findings = await self._monitor_darkweb(
                target.email, target.username
            )
            report.findings.extend(darkweb_findings)
            logger.info(f"Phase 3: Found {len(darkweb_findings)} dark web mentions")

        # Phase 4: Username enumeration
        if target.username:
            username_findings = await self._enumerate_username(target.username)
            report.findings.extend(username_findings)
            report.platform_presence = [
                f.details["platform"]
                for f in username_findings
                if f.details.get("found")
            ]
            logger.info(
                f"Phase 4: Found {len(report.platform_presence)} platform presences"
            )

        # Phase 5: Social media discovery
        if target.include_social and target.username:
            social_findings = await self._discover_social_profiles(target.username)
            report.findings.extend(social_findings)
            logger.info(f"Phase 5: Found {len(social_findings)} social profiles")

        # Phase 6: Calculate exposure score
        report.exposure_score = self._calculate_exposure_score(
            report.findings, report.breach_count
        )

        # Phase 7: Generate statistics
        report.statistics = self._generate_statistics(
            report.findings, report.breach_count
        )

        # Phase 8: AI Analysis
        await self._run_ai_analysis(target, report)

        # Phase 9: Generate recommendations
        report.recommendations = self._generate_recommendations(
            report.findings, report.exposure_score
        )

    async def _run_ai_analysis(
        self, target: CredentialTarget, report: CredentialIntelReport
    ) -> None:
        """Run AI analysis on findings.

        Args:
            target: Target configuration.
            report: Report to populate with AI analysis.
        """
        logger.info("Starting AI analysis for credential exposure...")
        try:
            findings_dict = [asdict(f) for f in report.findings]
            ai_analysis = self.ai_analyzer.analyze_credential_exposure(
                findings=findings_dict,
                target_email=target.email,
                target_username=target.username,
            )
            report.ai_analysis = ai_analysis
            logger.info(
                f"AI analysis completed (urgency: {ai_analysis.get('urgency_score', 'N/A')})"
            )
        except Exception as ai_error:
            logger.error(f"AI analysis failed: {ai_error}")
            report.ai_analysis = {
                "error": str(ai_error),
                "fallback": "AI analysis unavailable - using rule-based recommendations",
            }

    def get_workflow_status(self, workflow_id: str) -> dict[str, Any] | None:
        """Get workflow status.

        Args:
            workflow_id: Workflow identifier.

        Returns:
            Workflow status dictionary or None if not found.
        """
        report = self.active_workflows.get(workflow_id)
        if not report:
            return None

        return {
            "workflow_id": workflow_id,
            "status": report.status.value,
            "target_email": report.target_email,
            "target_username": report.target_username,
            "findings_count": len(report.findings),
            "breach_count": report.breach_count,
            "exposure_score": report.exposure_score,
            "started_at": report.started_at,
            "completed_at": report.completed_at,
        }
