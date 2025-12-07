"""ADW #3: Deep Target Profiling Workflow.

Main workflow orchestrator for target profiling.

Authors: MAXIMUS Team
Date: 2025-10-15
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
from .analyzers import (
    analyze_contact_info,
    analyze_images,
    detect_patterns,
    enumerate_platforms,
    scrape_social_media,
)
from .assessment import (
    calculate_se_vulnerability,
    generate_recommendations,
    generate_statistics,
)
from .extractors import (
    extract_contact_summary,
    extract_locations,
    extract_patterns,
    extract_social_profiles,
)
from .models import ProfileTarget, TargetProfileReport, WorkflowStatus

logger = logging.getLogger(__name__)

# Global workflow storage (shared across instances)
_ACTIVE_WORKFLOWS: dict[str, Any] = {}


class TargetProfilingWorkflow:
    """Deep Target Profiling AI-Driven Workflow.

    Orchestrates multiple OSINT services to build comprehensive target
    profile for security assessment.
    """

    def __init__(
        self,
        osint_service_url: str = "http://localhost:8036",
    ):
        """Initialize target profiling workflow.

        Args:
            osint_service_url: OSINT Service endpoint
        """
        self.osint_url = (
            osint_service_url
            if osint_service_url != "http://localhost:8036"
            else os.getenv("OSINT_SERVICE_URL", "http://localhost:8036")
        )

        self.active_workflows = _ACTIVE_WORKFLOWS
        self.ai_analyzer = AIAnalyzer()
        logger.info("TargetProfilingWorkflow initialized with AI analyzer")

    async def execute(self, target: ProfileTarget) -> TargetProfileReport:
        """Execute deep target profiling workflow.

        Args:
            target: Target configuration

        Returns:
            TargetProfileReport with complete profile
        """
        workflow_id = str(uuid4())
        started_at = datetime.utcnow().isoformat()

        report = TargetProfileReport(
            workflow_id=workflow_id,
            target_username=target.username,
            target_email=target.email,
            target_name=target.name,
            status=WorkflowStatus.RUNNING,
            started_at=started_at,
            completed_at=None,
        )

        self.active_workflows[workflow_id] = report

        try:
            async with asyncio.timeout(150):  # 2.5 minutes max
                logger.info(
                    f"Starting deep profiling for "
                    f"{target.username or target.email or target.name} "
                    f"(workflow_id={workflow_id})"
                )

                # Phase 1: Email/phone extraction and validation
                contact_findings = await analyze_contact_info(
                    target.email, target.phone
                )
                report.findings.extend(contact_findings)
                report.contact_info = extract_contact_summary(contact_findings)
                logger.info(
                    f"Phase 1: Analyzed contact info - {len(contact_findings)} findings"
                )

                # Phase 2: Social media scraping
                if target.include_social and target.username:
                    social_findings = await scrape_social_media(target.username)
                    report.findings.extend(social_findings)
                    report.social_profiles = extract_social_profiles(social_findings)
                    logger.info(
                        f"Phase 2: Found {len(report.social_profiles)} social profiles"
                    )

                # Phase 3: Username platform enumeration
                if target.username:
                    platform_findings = await enumerate_platforms(target.username)
                    report.findings.extend(platform_findings)
                    report.platform_presence = [
                        f.details["platform"]
                        for f in platform_findings
                        if f.details.get("found")
                    ]
                    logger.info(
                        f"Phase 3: Found presence on "
                        f"{len(report.platform_presence)} platforms"
                    )

                # Phase 4: Image metadata extraction
                if target.include_images and target.image_url:
                    image_findings = await analyze_images(target.image_url)
                    report.findings.extend(image_findings)
                    report.locations.extend(extract_locations(image_findings))
                    logger.info(
                        f"Phase 4: Analyzed images - {len(image_findings)} findings"
                    )

                # Phase 5: Pattern detection
                pattern_findings = await detect_patterns(report.findings)
                report.findings.extend(pattern_findings)
                report.behavioral_patterns = extract_patterns(pattern_findings)
                logger.info(
                    f"Phase 5: Detected {len(report.behavioral_patterns)} "
                    "behavioral patterns"
                )

                # Phase 6: Calculate SE vulnerability score
                report.se_score, report.se_vulnerability = calculate_se_vulnerability(
                    report.findings, report
                )

                # Phase 7: Generate statistics
                report.statistics = generate_statistics(report.findings, report)

                # Phase 8: AI Analysis
                logger.info("Starting AI analysis for target profile...")
                try:
                    findings_dict = [asdict(f) for f in report.findings]
                    ai_analysis = self.ai_analyzer.analyze_target_profile(
                        findings=findings_dict,
                        target_username=target.username,
                        target_email=target.email,
                    )
                    report.ai_analysis = ai_analysis
                    logger.info("AI analysis completed")
                except Exception as ai_error:
                    logger.error(f"AI analysis failed: {ai_error}")
                    report.ai_analysis = {
                        "error": str(ai_error),
                        "fallback": "AI analysis unavailable - using rule-based",
                    }

                # Phase 9: Generate recommendations (enhanced by AI)
                report.recommendations = generate_recommendations(report)

                # Mark complete
                report.status = WorkflowStatus.COMPLETED
                report.completed_at = datetime.utcnow().isoformat()

                logger.info(
                    f"Target profiling completed: {len(report.findings)} findings, "
                    f"SE_score={report.se_score:.2f}"
                )

        except asyncio.TimeoutError:
            logger.error("Target profiling workflow timeout after 150s")
            report.status = WorkflowStatus.FAILED
            report.error = (
                "Workflow execution timeout (150s) - "
                "external services may be unreachable"
            )
            report.completed_at = datetime.utcnow().isoformat()
        except Exception as e:
            logger.error(f"Target profiling workflow failed: {e}")
            report.status = WorkflowStatus.FAILED
            report.error = str(e)
            report.completed_at = datetime.utcnow().isoformat()

        return report

    def get_workflow_status(self, workflow_id: str) -> dict[str, Any] | None:
        """Get workflow status.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow status dictionary or None
        """
        report = self.active_workflows.get(workflow_id)
        if not report:
            return None

        return {
            "workflow_id": workflow_id,
            "status": report.status.value,
            "target_username": report.target_username,
            "target_email": report.target_email,
            "findings_count": len(report.findings),
            "se_score": report.se_score,
            "se_vulnerability": report.se_vulnerability.value,
            "started_at": report.started_at,
            "completed_at": report.completed_at,
        }
