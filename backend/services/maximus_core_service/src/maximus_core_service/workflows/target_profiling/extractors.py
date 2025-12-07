"""ADW #3: Target Profiling Extractors.

Data extraction functions for profiling results.

Authors: MAXIMUS Team
Date: 2025-10-15
"""

from __future__ import annotations

from typing import Any

from .models import ProfileFinding


def extract_contact_summary(contact_findings: list[ProfileFinding]) -> dict[str, Any]:
    """Extract contact information summary.

    Args:
        contact_findings: Contact findings

    Returns:
        Contact summary dictionary
    """
    summary: dict[str, Any] = {
        "emails": [],
        "phones": [],
        "validated": False,
    }

    for finding in contact_findings:
        if finding.category == "email":
            summary["emails"].append(finding.details)
            if finding.details.get("valid"):
                summary["validated"] = True
        elif finding.category == "phone":
            summary["phones"].append(finding.details)

    return summary


def extract_social_profiles(
    social_findings: list[ProfileFinding],
) -> list[dict[str, Any]]:
    """Extract social profile summaries.

    Args:
        social_findings: Social findings

    Returns:
        List of social profile dictionaries
    """
    profiles = []

    for finding in social_findings:
        if finding.category in ["twitter", "linkedin", "facebook"]:
            profiles.append(
                {
                    "platform": finding.details.get("platform"),
                    "username": finding.details.get("username"),
                    "display_name": finding.details.get("display_name"),
                    "url": finding.details.get("profile_url"),
                    "followers": finding.details.get("followers"),
                    "bio": finding.details.get("bio"),
                }
            )

    return profiles


def extract_locations(image_findings: list[ProfileFinding]) -> list[dict[str, Any]]:
    """Extract location information from images.

    Args:
        image_findings: Image findings

    Returns:
        List of location dictionaries
    """
    locations = []

    for finding in image_findings:
        if finding.category == "exif" and "gps_location" in finding.details:
            locations.append(
                {
                    "location": finding.details["gps_location"],
                    "latitude": finding.details.get("gps_latitude"),
                    "longitude": finding.details.get("gps_longitude"),
                    "source": "image_exif",
                    "timestamp": finding.details.get("datetime"),
                }
            )

    return locations


def extract_patterns(pattern_findings: list[ProfileFinding]) -> list[dict[str, Any]]:
    """Extract behavioral patterns.

    Args:
        pattern_findings: Pattern findings

    Returns:
        List of pattern dictionaries
    """
    patterns = []

    for finding in pattern_findings:
        if finding.finding_type == "pattern":
            patterns.append(
                {
                    "type": finding.category,
                    "description": finding.details.get("description"),
                    "confidence": finding.confidence,
                }
            )

    return patterns
