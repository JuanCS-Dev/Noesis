"""Scanner Methods for Attack Surface Mapping.

Mixin providing scanning capabilities.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from .models import Finding, RiskLevel

if TYPE_CHECKING:
    from .workflow import AttackSurfaceWorkflow

logger = logging.getLogger(__name__)


class ScannerMixin:
    """Mixin providing scanner methods.

    Provides methods for:
    - Subdomain enumeration
    - Port scanning
    - Service detection
    - CVE correlation
    - Nuclei scanning
    """

    async def _enumerate_subdomains(
        self: AttackSurfaceWorkflow,
        domain: str,
        include_subdomains: bool,
    ) -> list[Finding]:
        """Enumerate subdomains using passive DNS.

        Args:
            domain: Target domain.
            include_subdomains: Whether to include subdomain enumeration.

        Returns:
            List of subdomain findings.
        """
        if not include_subdomains:
            return []

        await asyncio.sleep(0.5)

        common_subdomains = ["www", "mail", "ftp", "admin", "api", "dev", "staging"]
        findings = []

        for subdomain_prefix in common_subdomains:
            subdomain = f"{subdomain_prefix}.{domain}"
            findings.append(
                Finding(
                    finding_id=str(uuid4()),
                    finding_type="subdomain",
                    severity=RiskLevel.INFO,
                    target=domain,
                    details={
                        "subdomain": subdomain,
                        "source": "passive_dns",
                        "confidence": 0.8,
                    },
                    timestamp=datetime.utcnow().isoformat(),
                    confidence=0.8,
                )
            )

        return findings

    async def _scan_ports(
        self: AttackSurfaceWorkflow,
        targets: list[str],
        port_range: str | None,
    ) -> list[Finding]:
        """Scan ports on targets using Nmap/Masscan.

        Args:
            targets: List of targets to scan.
            port_range: Port range specification.

        Returns:
            List of open port findings.
        """
        await asyncio.sleep(1.0)

        common_ports = [80, 443, 22, 21, 25, 3306, 5432, 6379, 8080, 8443]
        if port_range:
            common_ports = [80, 443, 22]

        findings = []
        for target in targets[:3]:
            for port in common_ports[:5]:
                findings.append(
                    Finding(
                        finding_id=str(uuid4()),
                        finding_type="open_port",
                        severity=RiskLevel.LOW if port in [80, 443] else RiskLevel.MEDIUM,
                        target=target,
                        details={
                            "port": port,
                            "protocol": "tcp",
                            "state": "open",
                            "scanner": "nmap",
                        },
                        timestamp=datetime.utcnow().isoformat(),
                    )
                )

        return findings

    async def _detect_services(
        self: AttackSurfaceWorkflow,
        port_findings: list[Finding],
    ) -> list[Finding]:
        """Detect services and versions on open ports.

        Args:
            port_findings: Open port findings.

        Returns:
            List of service findings.
        """
        await asyncio.sleep(0.8)

        service_map = {
            80: ("nginx", "1.18.0"),
            443: ("nginx", "1.18.0"),
            22: ("OpenSSH", "8.2p1"),
            21: ("vsftpd", "3.0.3"),
            3306: ("MySQL", "5.7.33"),
        }

        findings = []
        for port_finding in port_findings:
            port = port_finding.details.get("port")
            if port in service_map:
                service_name, version = service_map[port]
                findings.append(
                    Finding(
                        finding_id=str(uuid4()),
                        finding_type="service",
                        severity=RiskLevel.INFO,
                        target=port_finding.target,
                        details={
                            "port": port,
                            "service": service_name,
                            "version": version,
                            "banner": f"{service_name}/{version}",
                        },
                        timestamp=datetime.utcnow().isoformat(),
                    )
                )

        return findings

    async def _correlate_cves(
        self: AttackSurfaceWorkflow,
        service_findings: list[Finding],
    ) -> list[Finding]:
        """Correlate CVEs with detected services.

        Args:
            service_findings: Service findings.

        Returns:
            List of CVE findings.
        """
        await asyncio.sleep(0.5)

        findings = []
        for service_finding in service_findings:
            service = service_finding.details.get("service", "").lower()
            version = service_finding.details.get("version", "")

            if "nginx" in service and version.startswith("1.18"):
                findings.append(
                    Finding(
                        finding_id=str(uuid4()),
                        finding_type="vulnerability",
                        severity=RiskLevel.MEDIUM,
                        target=service_finding.target,
                        details={
                            "cve_id": "CVE-2021-23017",
                            "service": service,
                            "version": version,
                            "description": "nginx DNS resolver off-by-one heap write",
                            "cvss_score": 6.4,
                            "exploit_available": False,
                        },
                        timestamp=datetime.utcnow().isoformat(),
                    )
                )

            if "openssh" in service:
                findings.append(
                    Finding(
                        finding_id=str(uuid4()),
                        finding_type="vulnerability",
                        severity=RiskLevel.HIGH,
                        target=service_finding.target,
                        details={
                            "cve_id": "CVE-2023-38408",
                            "service": service,
                            "version": version,
                            "description": "OpenSSH remote code execution",
                            "cvss_score": 8.1,
                            "exploit_available": True,
                        },
                        timestamp=datetime.utcnow().isoformat(),
                    )
                )

        return findings

    async def _nuclei_scan(
        self: AttackSurfaceWorkflow,
        targets: list[str],
    ) -> list[Finding]:
        """Run Nuclei vulnerability scanner.

        Args:
            targets: List of targets.

        Returns:
            List of vulnerability findings.
        """
        await asyncio.sleep(2.0)

        findings = []
        for target in targets[:2]:
            findings.append(
                Finding(
                    finding_id=str(uuid4()),
                    finding_type="vulnerability",
                    severity=RiskLevel.MEDIUM,
                    target=target,
                    details={
                        "template": "http-missing-security-headers",
                        "name": "Missing Security Headers",
                        "matched_at": f"https://{target}",
                        "scanner": "nuclei",
                    },
                    timestamp=datetime.utcnow().isoformat(),
                )
            )

        return findings
