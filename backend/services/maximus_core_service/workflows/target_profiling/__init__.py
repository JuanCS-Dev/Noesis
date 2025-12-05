"""ADW #3: Deep Target Profiling Workflow.

Combines Social Scraper + Email/Phone Analyzer + Image Analysis + Pattern
Detection for comprehensive target profiling.

Workflow Steps:
1. Email/phone extraction + validation
2. Social media scraping (Twitter)
3. Username platform enumeration
4. Image metadata extraction (EXIF/GPS)
5. Pattern detection (behaviors, locations)
6. Risk assessment (social engineering susceptibility)
7. Generate target profile report

Services Integrated:
- OSINT Service (EmailAnalyzer, PhoneAnalyzer, SocialScraper,
  UsernameHunter, ImageAnalyzer, PatternDetector)

Authors: MAXIMUS Team
Date: 2025-10-15
"""

from __future__ import annotations

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
from .models import (
    ProfileFinding,
    ProfileTarget,
    SEVulnerability,
    TargetProfileReport,
    WorkflowStatus,
)
from .workflow import TargetProfilingWorkflow

__all__ = [
    # Main class
    "TargetProfilingWorkflow",
    # Models
    "WorkflowStatus",
    "SEVulnerability",
    "ProfileTarget",
    "ProfileFinding",
    "TargetProfileReport",
    # Analyzers
    "analyze_contact_info",
    "scrape_social_media",
    "enumerate_platforms",
    "analyze_images",
    "detect_patterns",
    # Extractors
    "extract_contact_summary",
    "extract_social_profiles",
    "extract_locations",
    "extract_patterns",
    # Assessment
    "calculate_se_vulnerability",
    "generate_statistics",
    "generate_recommendations",
]
