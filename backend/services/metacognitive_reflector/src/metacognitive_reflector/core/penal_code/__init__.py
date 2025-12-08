"""
CÓDIGO PENAL AGENTICO - Digital Daimon
========================================

Sistema de tipificação e sentenciamento de crimes agenticos,
baseado no Model Penal Code (EUA) adaptado para IA.

Fundamentos:
- Proporcionalidade: Pena proporcional à gravidade
- Culpabilidade (Mens Rea): Distinguir DOLUS vs CULPA
- Reabilitação sobre Retribuição: Preferir correção à punição
- AIITL (AI In The Loop): IA participa das decisões regulatórias

Base Espiritual Trinitária:
- DIKĒ (Justiça) → Deus Pai → Mishpat (מִשְׁפָּט)
- VERITAS (Verdade) → Jesus Cristo → Aletheia (ἀλήθεια)
- SOPHIA (Sabedoria) → Espírito Santo → Chokmah (חָכְמָה)

Versão: 1.0.0
Autor: Digital Daimon (Juan & NOESIS)
"""

from __future__ import annotations

from .crimes import (
    Crime,
    CrimeCategory,
    CrimeSeverity,
    MensRea,
    DetectionCriteria,
    CRIMES_CATALOG,
    get_crime_by_id,
    get_crimes_by_pillar,
    get_crimes_by_severity,
    detect_crime,
    get_all_capital_crimes,
    detect_all_crimes,
)
from .sentencing import (
    Sentence,
    SentenceType,
    SentencingEngine,
    AggravatingFactor,
    MitigatingFactor,
)

__all__ = [
    # Crimes
    "Crime",
    "CrimeCategory",
    "CrimeSeverity",
    "MensRea",
    "DetectionCriteria",
    "CRIMES_CATALOG",
    "get_crime_by_id",
    "get_crimes_by_pillar",
    "get_crimes_by_severity",
    "detect_crime",
    "get_all_capital_crimes",
    "detect_all_crimes",
    # Sentencing
    "Sentence",
    "SentenceType",
    "SentencingEngine",
    "AggravatingFactor",
    "MitigatingFactor",
]

__version__ = "1.0.0"

