"""CyberSecLIME - LIME adapted for cybersecurity threat classification.

This module implements LIME (Local Interpretable Model-agnostic Explanations)
specifically adapted for cybersecurity use cases, handling network features,
threat scores, behavioral indicators, and text-based threat intelligence.

Key Adaptations:
    - Network feature perturbation (IPs, ports, protocols)
    - Threat score perturbation with domain constraints
    - Text-based perturbation for narrative analysis
    - Cybersecurity-specific feature descriptions
"""

from __future__ import annotations

from .config import PerturbationConfig
from .lime import CyberSecLIME

__all__ = ["CyberSecLIME", "PerturbationConfig"]
