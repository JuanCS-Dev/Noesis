"""Attack Surface Workflow.

Main workflow orchestration for attack surface mapping.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict
from datetime import datetime
from typing import Any
from uuid import uuid4

from ..ai_analyzer import AIAnalyzer
from .analysis import AnalysisMixin
from .models import AttackSurfaceReport, AttackSurfaceTarget, WorkflowStatus
from .scanners import ScannerMixin

logger = logging.getLogger(__name__)

# Global workflow storage
_ACTIVE_WORKFLOWS: dict[str, Any] = {}


class AttackSurfaceWorkflow(ScannerMixin, AnalysisMixin):
    """External Attack Surface Mapping AI-Driven Workflow.

    Orchestrates multiple OSINT services to build comprehensive attack surface map.

    Attributes:
        network_recon_url: Network Recon Service endpoint.
        vuln_intel_url: Vuln Intel Service endpoint.
        vuln_scanner_url: Vuln Scanner Service endpoint.
        active_workflows: Active workflow tracking.
        ai_analyzer: AI analysis engine.
    """

    def __init__(
        self,
        network_recon_service_url: str = "http://localhost:8032",
        vuln_intel_service_url: str = "http://localhost:8045",
        vuln_scanner_service_url: str = "http://localhost:8046",
    ) -> None:
        """Initialize attack surface workflow.

        Args:
            network_recon_service_url: Network Recon Service endpoint.
            vuln_intel_service_url: Vuln Intel Service endpoint.
            vuln_scanner_service_url: Vuln Scanner Service endpoint.
        """
        self.network_recon_url = network_recon_service_url
        self.vuln_intel_url = vuln_intel_service_url
        self.vuln_scanner_url = vuln_scanner_service_url

        self.active_workflows = _ACTIVE_WORKFLOWS
        self.ai_analyzer = AIAnalyzer()

        logger.info("AttackSurfaceWorkflow initialized with AI analyzer")

    async def execute(self, target: AttackSurfaceTarget) -> AttackSurfaceReport:
        """Execute attack surface mapping workflow.

        Args:
            target: Target configuration.

        Returns:
            AttackSurfaceReport with complete findings.
        """
        workflow_id = str(uuid4())
        started_at = datetime.utcnow().isoformat()

        report = AttackSurfaceReport(
            workflow_id=workflow_id,
            target=target.domain,
            status=WorkflowStatus.RUNNING,
            started_at=started_at,
            completed_at=None,
        )

        self.active_workflows[workflow_id] = report

        try:
            async with asyncio.timeout(180):
                logger.info(
                    "Starting attack surface mapping for %s (workflow_id=%s)",
                    target.domain,
                    workflow_id,
                )

                await self._run_scan_phases(report, target)
                await self._run_analysis_phases(report, target)

                report.status = WorkflowStatus.COMPLETED
                report.completed_at = datetime.utcnow().isoformat()

                logger.info(
                    "Attack surface mapping completed: %d findings, risk_score=%.2f",
                    len(report.findings),
                    report.risk_score,
                )

        except asyncio.TimeoutError:
            logger.error("Attack surface workflow timeout after 180s")
            report.status = WorkflowStatus.FAILED
            report.error = (
                "Workflow execution timeout (180s) - external services may be unreachable"
            )
            report.completed_at = datetime.utcnow().isoformat()
        except Exception as e:
            logger.error("Attack surface workflow failed: %s", e)
            report.status = WorkflowStatus.FAILED
            report.error = str(e)
            report.completed_at = datetime.utcnow().isoformat()

        return report

    async def _run_scan_phases(
        self,
        report: AttackSurfaceReport,
        target: AttackSurfaceTarget,
    ) -> None:
        """Run all scanning phases.

        Args:
            report: Report to update with findings.
            target: Target configuration.
        """
        # Phase 1: Subdomain enumeration
        subdomains = await self._enumerate_subdomains(
            target.domain, target.include_subdomains
        )
        report.findings.extend(subdomains)
        logger.info("Phase 1: Found %d subdomains", len(subdomains))

        # Phase 2: Port scanning
        all_targets = [target.domain] + [
            f.details["subdomain"] for f in subdomains
        ]
        port_scan_findings = await self._scan_ports(all_targets, target.port_range)
        report.findings.extend(port_scan_findings)
        logger.info("Phase 2: Found %d open ports", len(port_scan_findings))

        # Phase 3: Service detection
        service_findings = await self._detect_services(port_scan_findings)
        report.findings.extend(service_findings)
        logger.info("Phase 3: Detected %d services", len(service_findings))

        # Phase 4: CVE correlation
        cve_findings = await self._correlate_cves(service_findings)
        report.findings.extend(cve_findings)
        logger.info("Phase 4: Found %d CVEs", len(cve_findings))

        # Phase 5: Nuclei scan (deep mode only)
        if target.scan_depth == "deep":
            nuclei_findings = await self._nuclei_scan(all_targets)
            report.findings.extend(nuclei_findings)
            logger.info("Phase 5: Nuclei found %d vulnerabilities", len(nuclei_findings))

    async def _run_analysis_phases(
        self,
        report: AttackSurfaceReport,
        target: AttackSurfaceTarget,
    ) -> None:
        """Run all analysis phases.

        Args:
            report: Report to update with analysis.
            target: Target configuration.
        """
        # Phase 6: Calculate risk score
        report.risk_score = self._calculate_risk_score(report.findings)

        # Phase 7: Generate statistics
        report.statistics = self._generate_statistics(report.findings)

        # Phase 8: AI Analysis
        logger.info("Starting AI analysis for attack surface...")
        try:
            findings_dict = [asdict(f) for f in report.findings]
            ai_analysis = self.ai_analyzer.analyze_attack_surface(
                findings=findings_dict, target=target.domain
            )
            report.ai_analysis = ai_analysis
            logger.info(
                "AI analysis completed (risk_score: %s)",
                ai_analysis.get("risk_score", "N/A"),
            )
        except Exception as ai_error:
            logger.error("AI analysis failed: %s", ai_error)
            report.ai_analysis = {
                "error": str(ai_error),
                "fallback": "AI analysis unavailable - using rule-based recommendations",
            }

        # Phase 9: Generate recommendations
        report.recommendations = self._generate_recommendations(
            report.findings, report.risk_score
        )

    def get_workflow_status(self, workflow_id: str) -> dict[str, Any] | None:
        """Get workflow status.

        Args:
            workflow_id: Workflow identifier.

        Returns:
            Workflow status dictionary or None.
        """
        report = self.active_workflows.get(workflow_id)
        if not report:
            return None

        return {
            "workflow_id": workflow_id,
            "status": report.status.value,
            "target": report.target,
            "findings_count": len(report.findings),
            "risk_score": report.risk_score,
            "started_at": report.started_at,
            "completed_at": report.completed_at,
        }
