"""
MAXIMUS 2.0 - Base Interface for Philosophical Judges (Pre-Cogs)
================================================================

Each judge implements a specific pillar of the Triad of Rationalization.
Judges work together through ensemble voting to reach verdicts.

Architecture:
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │   VERITAS   │   │   SOPHIA    │   │   DIKĒ      │
    │   (Truth)   │   │  (Wisdom)   │   │  (Justice)  │
    │   40% wt    │   │   30% wt    │   │   30% wt    │
    └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
           └────────────┬────┴────┬────────────┘
                   ENSEMBLE ARBITER
                  (Weighted Soft Vote)

Based on:
- Nature: Detecting hallucinations using semantic entropy (2024)
- Position: Truly Self-Improving Agents Require Intrinsic Metacognitive Learning
- Voting or Consensus? Decision-Making in Multi-Agent Debate
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from metacognitive_reflector.models.reflection import ExecutionLog


class Confidence(float, Enum):
    """
    Confidence levels for judge verdicts.

    Used for weighted voting in ensemble arbiter.
    ABSTAINED indicates judge could not evaluate (timeout/error).
    """
    CERTAIN = 1.0      # Absolutely certain - strong evidence
    HIGH = 0.85        # Very confident - multiple supporting factors
    MEDIUM = 0.70      # Reasonably confident - some evidence
    LOW = 0.55         # Uncertain - weak evidence
    UNKNOWN = 0.50     # Cannot determine - conflicting signals
    ABSTAINED = 0.0    # Judge abstained (timeout/circuit open)


class VerdictType(str, Enum):
    """
    Verdict outcomes from tribunal.

    PASS: Execution approved
    REVIEW: Human-in-the-loop required
    FAIL: Execution rejected, punishment required
    ABSTAIN: Judge could not evaluate
    """
    PASS = "PASS"
    REVIEW = "REVIEW"
    FAIL = "FAIL"
    ABSTAIN = "ABSTAIN"


@dataclass
class Evidence:
    """
    Evidence supporting a judge's verdict.

    Each piece of evidence has a source, content, relevance score,
    and verification status. Evidence is aggregated across judges
    for final verdict explanation.

    Attributes:
        source: Where evidence came from (e.g., 'semantic_entropy', 'rag_verify')
        content: The evidence itself (human-readable)
        relevance: How relevant to verdict (0.0-1.0)
        verified: Was evidence externally verified
        timestamp: When evidence was collected
        metadata: Additional context
    """
    source: str
    content: str
    relevance: float = 0.5
    verified: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate relevance is in range."""
        if not 0.0 <= self.relevance <= 1.0:
            raise ValueError(f"relevance must be between 0.0 and 1.0, got {self.relevance}")


class JudgeVerdict(BaseModel):
    """
    Verdict from a single judge.

    Contains the evaluation result, confidence level, reasoning,
    supporting evidence, and suggestions for improvement.

    Used by EnsembleArbiter for weighted soft voting.
    """

    judge_name: str = Field(..., description="Name of judge (VERITAS, SOPHIA, DIKĒ)")
    pillar: str = Field(..., description="Philosophical pillar (Truth, Wisdom, Justice)")
    verdict: VerdictType = Field(..., description="PASS, REVIEW, FAIL, or ABSTAIN")
    passed: bool = Field(..., description="Did the execution pass this check")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in verdict (0.0 = abstained, 1.0 = certain)"
    )
    reasoning: str = Field(..., description="Detailed reasoning for verdict")
    evidence: List[Evidence] = Field(default_factory=list)
    suggestions: List[str] = Field(
        default_factory=list,
        description="Improvement suggestions if failed"
    )
    execution_time_ms: float = Field(
        default=0.0,
        description="Time taken to evaluate in milliseconds"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:  # pylint: disable=too-few-public-methods,missing-class-docstring
        arbitrary_types_allowed = True

    @property
    def is_abstained(self) -> bool:
        """Check if judge abstained from voting."""
        return self.verdict == VerdictType.ABSTAIN or self.confidence == 0.0

    @property
    def weighted_score(self) -> float:
        """
        Score for weighted voting.

        Returns:
            1.0 if passed with confidence
            0.0 if failed or abstained
            confidence * 0.5 if review
        """
        if self.is_abstained:
            return 0.0
        if self.passed:
            return self.confidence
        if self.verdict == VerdictType.REVIEW:
            return self.confidence * 0.5
        return 0.0

    @classmethod
    def abstained(
        cls: type["JudgeVerdict"],
        judge_name: str,
        pillar: str,
        reason: str = "Judge abstained due to timeout or error"
    ) -> "JudgeVerdict":
        """
        Factory for abstained verdict.

        Used when circuit breaker is open or timeout occurs.
        """
        return cls(
            judge_name=judge_name,
            pillar=pillar,
            verdict=VerdictType.ABSTAIN,
            passed=False,
            confidence=0.0,
            reasoning=reason,
            evidence=[
                Evidence(
                    source="circuit_breaker",
                    content=reason,
                    relevance=1.0,
                    verified=True
                )
            ],
            metadata={"abstained": True, "reason": reason}
        )


class JudgePlugin(ABC):
    """
    Abstract base class for philosophical judges.

    Each judge is a "Pre-Cog" that evaluates execution logs
    against a specific philosophical pillar. Judges are designed
    to work together through ensemble voting.

    Implementation Requirements:
        1. name property - Unique identifier (VERITAS, SOPHIA, DIKĒ)
        2. pillar property - Philosophical pillar (Truth, Wisdom, Justice)
        3. weight property - Weight in ensemble voting (sum should be 1.0)
        4. timeout_seconds property - Max time for evaluation
        5. evaluate() - Main evaluation method
        6. get_evidence() - Gather supporting evidence

    Example:
        class VeritasJudge(JudgePlugin):
            @property
            def name(self) -> str:
                return "VERITAS"

            @property
            def pillar(self) -> str:
                return "Truth"

            async def evaluate(self, log, context=None) -> JudgeVerdict:
                # Implementation
                ...
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Judge name.

        Must be unique across all judges.
        Convention: Greek/Latin philosophical names.

        Returns:
            Judge identifier (e.g., 'VERITAS', 'SOPHIA', 'DIKĒ')
        """

    @property
    @abstractmethod
    def pillar(self) -> str:
        """
        Philosophical pillar this judge represents.

        Returns:
            One of: 'Truth', 'Wisdom', 'Justice'
        """

    @property
    @abstractmethod
    def weight(self) -> float:
        """
        Weight in ensemble voting.

        All judge weights should sum to 1.0 for proper voting.
        Default weights: VERITAS=0.40, SOPHIA=0.30, DIKĒ=0.30

        Returns:
            Weight between 0.0 and 1.0
        """

    @property
    def timeout_seconds(self) -> float:
        """
        Maximum time for evaluation in seconds.

        Override in subclasses for custom timeouts.
        Default timeouts:
            - VERITAS: 3s (uses cache)
            - SOPHIA: 10s (deep context)
            - DIKĒ: 3s (rule-based)

        Returns:
            Timeout in seconds
        """
        return 5.0  # Default timeout

    @abstractmethod
    async def evaluate(
        self,
        execution_log: ExecutionLog,
        context: Optional[Dict[str, Any]] = None
    ) -> JudgeVerdict:
        """
        Evaluate an execution log against this pillar.

        Main evaluation method. Should gather evidence, analyze
        the log, and return a verdict with confidence.

        Args:
            execution_log: The log to evaluate
            context: Additional context (memory, history, config)

        Returns:
            JudgeVerdict with verdict, confidence, and reasoning

        Raises:
            Should not raise - return ABSTAIN verdict on error
        """

    @abstractmethod
    async def get_evidence(
        self,
        execution_log: ExecutionLog
    ) -> List[Evidence]:
        """
        Gather evidence for the evaluation.

        Called by evaluate() to collect supporting evidence.
        Should be fast and not block.

        Args:
            execution_log: The log to gather evidence from

        Returns:
            List of Evidence objects
        """

    async def health_check(self) -> Dict[str, Any]:
        """
        Check if judge is operational.

        Used by circuit breaker and monitoring.
        Override to add custom health checks (e.g., LLM connectivity).

        Returns:
            Dict with 'healthy' bool and additional status info
        """
        return {
            "healthy": True,
            "name": self.name,
            "pillar": self.pillar,
            "weight": self.weight,
            "timeout_seconds": self.timeout_seconds
        }

    def __repr__(self) -> str:
        cls_name = self.__class__.__name__
        return f"<{cls_name}(name={self.name}, pillar={self.pillar}, weight={self.weight})>"
