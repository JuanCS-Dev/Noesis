"""ADW #3: Target Profiling Assessment.

Risk assessment and recommendation generation.

Authors: MAXIMUS Team
Date: 2025-10-15
"""

from __future__ import annotations

from typing import Any

from .models import ProfileFinding, SEVulnerability, TargetProfileReport


def calculate_se_vulnerability(
    findings: list[ProfileFinding],
    report: TargetProfileReport,
) -> tuple[float, SEVulnerability]:
    """Calculate social engineering vulnerability score.

    Args:
        findings: All findings
        report: Current report state

    Returns:
        Tuple of (score, vulnerability_level)
    """
    score = 0.0

    # Contact information exposure (+15 points per contact)
    if report.contact_info.get("emails"):
        score += 15.0 * len(report.contact_info["emails"])
    if report.contact_info.get("phones"):
        score += 15.0 * len(report.contact_info["phones"])

    # Social media presence (+10 points per profile)
    score += 10.0 * len(report.social_profiles)

    # Platform presence (+5 points per platform)
    score += 5.0 * len(report.platform_presence)

    # Location exposure (+20 points)
    if report.locations:
        score += 20.0

    # Behavioral patterns (+10 points per pattern)
    score += 10.0 * len(report.behavioral_patterns)

    # Public activity bonus
    twitter_profiles = [
        p for p in report.social_profiles if p.get("platform") == "twitter"
    ]
    if twitter_profiles:
        followers = twitter_profiles[0].get("followers", 0)
        if followers > 1000:
            score += 10.0  # High visibility
        elif followers > 100:
            score += 5.0  # Medium visibility

    # Normalize to 0-100
    se_score = min(100.0, score)

    # Determine vulnerability level
    if se_score >= 70:
        vulnerability = SEVulnerability.CRITICAL
    elif se_score >= 50:
        vulnerability = SEVulnerability.HIGH
    elif se_score >= 30:
        vulnerability = SEVulnerability.MEDIUM
    elif se_score >= 10:
        vulnerability = SEVulnerability.LOW
    else:
        vulnerability = SEVulnerability.INFO

    return round(se_score, 2), vulnerability


def generate_statistics(
    findings: list[ProfileFinding],
    report: TargetProfileReport,
) -> dict[str, Any]:
    """Generate statistics from findings.

    Args:
        findings: All findings
        report: Current report state

    Returns:
        Statistics dictionary
    """
    stats: dict[str, Any] = {
        "total_findings": len(findings),
        "by_type": {},
        "contact_count": len(report.contact_info.get("emails", []))
        + len(report.contact_info.get("phones", [])),
        "social_profiles_count": len(report.social_profiles),
        "platforms_present": len(report.platform_presence),
        "locations_found": len(report.locations),
        "patterns_detected": len(report.behavioral_patterns),
    }

    for finding in findings:
        ftype = finding.finding_type
        stats["by_type"][ftype] = stats["by_type"].get(ftype, 0) + 1

    return stats


def generate_recommendations(report: TargetProfileReport) -> list[str]:
    """Generate security recommendations.

    Args:
        report: Complete report

    Returns:
        List of recommendations
    """
    recommendations = []

    # High-level recommendations based on SE vulnerability
    if report.se_vulnerability == SEVulnerability.CRITICAL:
        recommendations.append(
            "CRITICAL: Target is highly susceptible to social engineering attacks"
        )
        recommendations.append("Recommend immediate security awareness training")
    elif report.se_vulnerability == SEVulnerability.HIGH:
        recommendations.append("HIGH: Significant social engineering risk detected")
        recommendations.append(
            "Implement enhanced verification procedures for this target"
        )
    elif report.se_vulnerability == SEVulnerability.MEDIUM:
        recommendations.append("MEDIUM: Moderate social engineering risk")
        recommendations.append("Standard security protocols apply")
    else:
        recommendations.append("LOW: Limited social engineering risk detected")

    # Contact exposure recommendations
    if report.contact_info.get("emails"):
        recommendations.append(
            f"{len(report.contact_info['emails'])} email(s) publicly exposed "
            "- recommend privacy review"
        )

    # Social media recommendations
    if len(report.social_profiles) > 2:
        recommendations.append(
            f"Multiple social profiles ({len(report.social_profiles)}) "
            "increase attack surface"
        )
        recommendations.append("Review privacy settings on all social platforms")

    # Location recommendations
    if report.locations:
        recommendations.append("PRIVACY: Location data found in image metadata")
        recommendations.append("Recommend disabling GPS tagging on mobile devices")

    # Platform presence recommendations
    if len(report.platform_presence) > 5:
        recommendations.append(
            f"Presence on {len(report.platform_presence)} platforms "
            "increases reconnaissance exposure"
        )
        recommendations.append("Consider using unique usernames per platform")

    # Behavioral pattern recommendations
    activity_patterns = [
        p for p in report.behavioral_patterns if p["type"] == "activity_pattern"
    ]
    if activity_patterns:
        recommendations.append(
            "Predictable activity patterns detected - vary posting times for OPSEC"
        )

    # General recommendations
    recommendations.append("Enable two-factor authentication on all accounts")
    recommendations.append("Regularly audit public information exposure")
    recommendations.append(
        "Use different usernames across platforms to reduce correlation"
    )
    recommendations.append("Disable location services for social media applications")

    return recommendations
