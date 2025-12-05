"""
MIP API State Management.

Global state and service instances for the MIP API.

Author: Juan Carlos de Souza
Date: 2025-10-06
"""

from __future__ import annotations

import logging
import os
from typing import Any

from motor_integridade_processual.frameworks.kantian import KantianDeontology
from motor_integridade_processual.frameworks.principialism import Principialism
from motor_integridade_processual.frameworks.utilitarian import UtilitarianCalculus
from motor_integridade_processual.frameworks.virtue import VirtueEthics
from motor_integridade_processual.models.verdict import FrameworkName
from motor_integridade_processual.resolution.conflict_resolver import ConflictResolver

from justice.cbr_engine import CBREngine
from justice.precedent_database import PrecedentDB
from justice.validators import create_default_validators

logger = logging.getLogger(__name__)

# Initialize frameworks
frameworks = {
    FrameworkName.KANTIAN: KantianDeontology(),
    FrameworkName.UTILITARIAN: UtilitarianCalculus(),
    FrameworkName.VIRTUE_ETHICS: VirtueEthics(),
    FrameworkName.PRINCIPIALISM: Principialism(),
}

# Initialize resolver
resolver = ConflictResolver()

# Initialize CBR Engine for precedent-based reasoning
db_url = os.getenv(
    "DATABASE_URL", "postgresql://maximus:password@localhost/maximus"
)

try:
    precedent_db = PrecedentDB(db_url)
    cbr_engine: CBREngine | None = CBREngine(precedent_db)
    cbr_validators = create_default_validators()
    logger.info("CBR Engine initialized with precedent database + validators")
except Exception as e:
    logger.warning(
        f"CBR Engine initialization failed: {e}. Continuing without precedents."
    )
    cbr_engine = None
    precedent_db = None
    cbr_validators = []

# Metrics storage (in-memory)
evaluation_count = 0
evaluation_times: list[float] = []
decision_counts: dict[str, int] = {}

# CBR Metrics
cbr_precedents_used_count = 0
cbr_shortcut_count = 0

# A/B Testing Mode
AB_TESTING_ENABLED = os.getenv("MIP_AB_TESTING", "false").lower() == "true"
ab_test_results: list[dict[str, Any]] = []


def update_metrics(elapsed_time: float, decision_type: str) -> None:
    """Update evaluation metrics."""
    global evaluation_count, evaluation_times, decision_counts

    evaluation_count += 1
    evaluation_times.append(elapsed_time)
    decision_counts[decision_type] = decision_counts.get(decision_type, 0) + 1


def update_cbr_metrics(precedent_used: bool, shortcut: bool) -> None:
    """Update CBR metrics."""
    global cbr_precedents_used_count, cbr_shortcut_count

    if precedent_used:
        cbr_precedents_used_count += 1
    if shortcut:
        cbr_shortcut_count += 1
