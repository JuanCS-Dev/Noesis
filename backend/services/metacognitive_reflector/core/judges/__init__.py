"""
MAXIMUS 2.0 - Tribunal Meta-Cognitivo (Os Três Juízes)
======================================================

Three philosophical judges working together as Pre-Cogs:
- VERITAS (Truth): Semantic entropy + RAG verification
- SOPHIA (Wisdom): Context depth + memory query
- DIKĒ (Justice): Role matrix + constitutional compliance

Based on:
- Nature: Detecting hallucinations using semantic entropy (2024)
- Position: Truly Self-Improving Agents Require Intrinsic Metacognitive Learning
- Voting or Consensus? Decision-Making in Multi-Agent Debate
"""

from __future__ import annotations


from .base import (
    Confidence,
    Evidence,
    JudgePlugin,
    JudgeVerdict,
    VerdictType,
)
from .veritas import VeritasJudge
from .sophia import SophiaJudge
from .dike import DikeJudge
from .roles import RoleCapability, DEFAULT_ROLE_MATRIX
from .resilience import CircuitBreaker, CircuitState, ResilientJudgeWrapper
from .arbiter import EnsembleArbiter
from .voting import TribunalDecision, TribunalVerdict, VoteResult

__all__ = [
    # Base
    "Confidence",
    "Evidence",
    "JudgePlugin",
    "JudgeVerdict",
    "VerdictType",
    # Judges
    "VeritasJudge",
    "SophiaJudge",
    "DikeJudge",
    # Roles
    "RoleCapability",
    "DEFAULT_ROLE_MATRIX",
    # Resilience
    "CircuitBreaker",
    "CircuitState",
    "ResilientJudgeWrapper",
    # Arbiter
    "EnsembleArbiter",
    "TribunalDecision",
    "TribunalVerdict",
    "VoteResult",
]
