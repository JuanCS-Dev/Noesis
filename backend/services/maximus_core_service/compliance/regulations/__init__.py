"""
Regulations Package.

Contains definitions for 8 major compliance regulations.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

from ..base import Regulation, RegulationType

from .brazil_lgpd import BRAZIL_LGPD
from .eu_ai_act import EU_AI_ACT
from .gdpr import GDPR
from .ieee_7000 import IEEE_7000
from .iso_27001 import ISO_27001
from .nist_ai_rmf import NIST_AI_RMF
from .soc2_type_ii import SOC2_TYPE_II
from .us_eo_14110 import US_EO_14110

REGULATION_REGISTRY: dict[RegulationType, Regulation] = {
    RegulationType.EU_AI_ACT: EU_AI_ACT,
    RegulationType.GDPR: GDPR,
    RegulationType.NIST_AI_RMF: NIST_AI_RMF,
    RegulationType.US_EO_14110: US_EO_14110,
    RegulationType.BRAZIL_LGPD: BRAZIL_LGPD,
    RegulationType.ISO_27001: ISO_27001,
    RegulationType.SOC2_TYPE_II: SOC2_TYPE_II,
    RegulationType.IEEE_7000: IEEE_7000,
}


def get_regulation(regulation_type: RegulationType) -> Regulation:
    """
    Get regulation definition by type.

    Args:
        regulation_type: Type of regulation to retrieve

    Returns:
        Regulation object

    Raises:
        ValueError: If regulation type not found
    """
    if regulation_type not in REGULATION_REGISTRY:
        raise ValueError(f"Regulation {regulation_type} not found in registry")
    return REGULATION_REGISTRY[regulation_type]


__all__ = [
    "BRAZIL_LGPD",
    "EU_AI_ACT",
    "GDPR",
    "IEEE_7000",
    "ISO_27001",
    "NIST_AI_RMF",
    "REGULATION_REGISTRY",
    "SOC2_TYPE_II",
    "US_EO_14110",
    "get_regulation",
]
