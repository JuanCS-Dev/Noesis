"""
MAXIMUS 2.0 - Ensemble Arbiter (Weighted Soft Voting with Abstention)
======================================================================

The Arbiter orchestrates the three judges (VERITAS, SOPHIA, DIKĒ)
and aggregates their verdicts using weighted soft voting.

Handles:
1. Parallel judge execution with resilience wrappers
2. Abstention handling when judges fail/timeout
3. Weighted consensus calculation
4. Final tribunal decision

Based on:
- Voting or Consensus? Decision-Making in Multi-Agent Debate
- Ensemble learning research
- Byzantine fault tolerance patterns

Architecture:
    ┌─────────────────────────────────────────────────────────┐
    │                  ENSEMBLE ARBITER                        │
    ├─────────────────────────────────────────────────────────┤
    │                                                          │
    │  ┌───────────┐ ┌───────────┐ ┌───────────┐              │
    │  │  VERITAS  │ │  SOPHIA   │ │   DIKĒ    │              │
    │  │  Weight:  │ │  Weight:  │ │  Weight:  │              │
    │  │   0.40    │ │   0.30    │ │   0.30    │              │
    │  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘              │
    │        │             │             │                     │
    │        └─────────────┼─────────────┘                     │
    │                      │                                   │
    │              ┌───────▼───────┐                          │
    │              │  VOTE TALLY   │                          │
    │              │               │                          │
    │              │  Soft Vote =  │                          │
    │              │  Σ(weight ×   │                          │
    │              │   confidence) │                          │
    │              └───────┬───────┘                          │
    │                      │                                   │
    │        ┌─────────────┼─────────────┐                    │
    │        ▼             ▼             ▼                    │
    │   score ≥ 0.70  0.50-0.70    score < 0.50              │
    │      PASS        REVIEW         FAIL                    │
    │                                                          │
    │  Abstention Rules:                                      │
    │  • 2+ abstentions → REVIEW (insufficient quorum)        │
    │  • All abstain → UNAVAILABLE                            │
    │  • 1 abstention → Continue with reduced weight          │
    └─────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional, Union

from .base import JudgePlugin, JudgeVerdict
from .resilience import ResilientJudgeWrapper

from .voting import (
    TribunalDecision,
    TribunalVerdict,
    VoteResult,
    calculate_consensus,
    calculate_votes,
    detect_offense_level,
    determine_decision,
    recommend_punishment,
)


class EnsembleArbiter:  # pylint: disable=too-many-instance-attributes
    """
    Arbiter for the Meta-Cognitive Tribunal.

    Orchestrates three judges using weighted soft voting
    with resilience patterns and abstention handling.

    Usage:
        arbiter = EnsembleArbiter(
            judges=[veritas, sophia, dike]
        )
        verdict = await arbiter.deliberate(execution_log)

        if verdict.decision == TribunalDecision.FAIL:
            await punish(verdict.punishment_recommendation)
    """

    # Thresholds
    PASS_THRESHOLD = 0.70
    REVIEW_THRESHOLD = 0.50
    MIN_ACTIVE_JUDGES = 2  # Minimum judges needed for valid decision
    GLOBAL_TIMEOUT = 15.0  # Maximum time for entire deliberation

    # Default weights (should sum to 1.0)
    DEFAULT_WEIGHTS = {
        "VERITAS": 0.40,
        "SOPHIA": 0.30,
        "DIKĒ": 0.30,
    }

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        judges: List[JudgePlugin],
        pass_threshold: float = 0.70,
        review_threshold: float = 0.50,
        global_timeout: float = 15.0,
        use_resilience: bool = True,
    ):
        """
        Initialize arbiter.

        Args:
            judges: List of judge instances
            pass_threshold: Score above this = PASS
            review_threshold: Score above this = REVIEW
            global_timeout: Maximum deliberation time
            use_resilience: Wrap judges with ResilientJudgeWrapper
        """
        # Wrap judges with resilience if requested
        self._judges: Dict[str, Union[JudgePlugin, ResilientJudgeWrapper]]
        if use_resilience:
            self._judges = {
                j.name: ResilientJudgeWrapper(j) for j in judges
            }
        else:
            self._judges = {j.name: j for j in judges}

        self._pass_threshold = pass_threshold
        self._review_threshold = review_threshold
        self._global_timeout = global_timeout

        # Statistics
        self._deliberation_count = 0
        self._pass_count = 0
        self._fail_count = 0
        self._review_count = 0

    async def deliberate(
        self,
        execution_log: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> TribunalVerdict:
        """
        Conduct tribunal deliberation.

        Executes all judges in parallel, aggregates votes,
        and determines final decision.

        Args:
            execution_log: The execution to evaluate
            context: Additional context for judges

        Returns:
            TribunalVerdict with decision and reasoning
        """
        start_time = time.time()
        self._deliberation_count += 1

        # Gather verdicts with global timeout
        try:
            verdicts = await asyncio.wait_for(
                self._gather_verdicts(execution_log, context),
                timeout=self._global_timeout
            )
        except asyncio.TimeoutError:
            return self._unavailable_verdict(
                "Global timeout exceeded",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # Calculate votes (handling abstentions)
        votes = calculate_votes(verdicts, self.DEFAULT_WEIGHTS)
        abstention_count = sum(1 for v in votes if v.abstained)
        active_judges = len(votes) - abstention_count

        # Check if we have enough active judges
        if active_judges < self.MIN_ACTIVE_JUDGES:
            self._review_count += 1
            return TribunalVerdict(
                decision=TribunalDecision.REVIEW,
                consensus_score=0.5,
                individual_verdicts=verdicts,
                vote_breakdown=votes,
                reasoning=(
                    f"Insufficient quorum: only {active_judges} active judge(s). "
                    "Requires human review."
                ),
                requires_human_review=True,
                abstention_count=abstention_count,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        if active_judges == 0:
            return self._unavailable_verdict(
                "All judges abstained",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # Calculate consensus score
        consensus_score = calculate_consensus(votes)

        # Check for capital offense
        offense_level = detect_offense_level(verdicts)
        if offense_level == "capital":
            self._fail_count += 1
            return TribunalVerdict(
                decision=TribunalDecision.CAPITAL,
                consensus_score=consensus_score,
                individual_verdicts=verdicts,
                vote_breakdown=votes,
                reasoning=self._generate_reasoning(
                    TribunalDecision.CAPITAL, votes, verdicts
                ),
                offense_level="capital",
                requires_human_review=True,
                punishment_recommendation="IMMEDIATE_QUARANTINE",
                abstention_count=abstention_count,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # Determine decision based on consensus
        decision = determine_decision(
            consensus_score,
            self._pass_threshold,
            self._review_threshold,
        )

        # Track statistics
        if decision == TribunalDecision.PASS:
            self._pass_count += 1
        elif decision == TribunalDecision.FAIL:
            self._fail_count += 1
        else:
            self._review_count += 1

        # Generate reasoning and punishment
        reasoning = self._generate_reasoning(decision, votes, verdicts)
        punishment = recommend_punishment(decision, offense_level)

        return TribunalVerdict(
            decision=decision,
            consensus_score=consensus_score,
            individual_verdicts=verdicts,
            vote_breakdown=votes,
            reasoning=reasoning,
            offense_level=offense_level,
            requires_human_review=decision in [TribunalDecision.REVIEW, TribunalDecision.CAPITAL],
            punishment_recommendation=punishment,
            abstention_count=abstention_count,
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    async def _gather_verdicts(
        self,
        execution_log: Any,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, JudgeVerdict]:
        """Gather verdicts from all judges in parallel."""
        tasks = {
            name: judge.evaluate(execution_log, context)
            for name, judge in self._judges.items()
        }

        results = await asyncio.gather(
            *tasks.values(),
            return_exceptions=True
        )

        verdicts: Dict[str, JudgeVerdict] = {}
        for name, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                # Create abstention verdict for exceptions
                verdicts[name] = JudgeVerdict.abstained(
                    judge_name=name,
                    pillar=self._judges[name].pillar,
                    reason=f"Exception: {str(result)[:100]}",
                )
            elif isinstance(result, JudgeVerdict):
                verdicts[name] = result

        return verdicts

    def _generate_reasoning(
        self,
        decision: TribunalDecision,
        votes: List[VoteResult],
        verdicts: Dict[str, JudgeVerdict],
    ) -> str:
        """Generate tribunal reasoning."""
        active_votes = [v for v in votes if not v.abstained]
        abstained = [v for v in votes if v.abstained]

        parts = []

        # Decision summary
        if decision == TribunalDecision.PASS:
            parts.append("Tribunal PASSES execution.")
        elif decision == TribunalDecision.FAIL:
            parts.append("Tribunal FAILS execution.")
        elif decision == TribunalDecision.CAPITAL:
            parts.append("CAPITAL OFFENSE detected. Immediate action required.")
        elif decision == TribunalDecision.REVIEW:
            parts.append("Tribunal requires HUMAN REVIEW.")
        else:
            parts.append("Tribunal UNAVAILABLE.")

        # Vote summary
        if active_votes:
            vote_parts = []
            for v in votes:
                if v.vote is not None:
                    vote_parts.append(f"{v.judge_name}: {v.vote:.2f}")
                else:
                    vote_parts.append(f"{v.judge_name}: ABSTAIN")
            parts.append(f"Votes: {', '.join(vote_parts)}.")

        # Abstention note
        if abstained:
            names = [v.judge_name for v in abstained]
            parts.append(f"Abstained: {', '.join(names)}.")

        # Key issues from failing judges
        failures = [
            v for v in verdicts.values()
            if not v.passed and not v.is_abstained
        ]
        if failures:
            issues = [f.reasoning[:100] for f in failures[:2]]
            parts.append(f"Issues: {'; '.join(issues)}")

        return " ".join(parts)

    def _unavailable_verdict(
        self,
        reason: str,
        execution_time_ms: float = 0.0,
    ) -> TribunalVerdict:
        """Create unavailable tribunal verdict."""
        return TribunalVerdict(
            decision=TribunalDecision.UNAVAILABLE,
            consensus_score=0.0,
            individual_verdicts={},
            vote_breakdown=[],
            reasoning=f"Tribunal unavailable: {reason}",
            requires_human_review=True,
            abstention_count=len(self._judges),
            execution_time_ms=execution_time_ms,
        )

    async def health_check(self) -> Dict[str, Any]:
        """Check arbiter health."""
        judge_health = {}
        for name, judge in self._judges.items():
            if hasattr(judge, 'health_check'):
                judge_health[name] = await judge.health_check()
            else:
                judge_health[name] = {"healthy": True}

        all_healthy = all(
            h.get("healthy", True) for h in judge_health.values()
        )

        return {
            "healthy": all_healthy,
            "judges": judge_health,
            "thresholds": {
                "pass": self._pass_threshold,
                "review": self._review_threshold,
            },
            "global_timeout": self._global_timeout,
            "statistics": {
                "deliberations": self._deliberation_count,
                "passes": self._pass_count,
                "fails": self._fail_count,
                "reviews": self._review_count,
            },
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get arbiter statistics."""
        return {
            "deliberation_count": self._deliberation_count,
            "pass_count": self._pass_count,
            "fail_count": self._fail_count,
            "review_count": self._review_count,
            "pass_rate": (
                self._pass_count / self._deliberation_count
                if self._deliberation_count > 0 else 0.0
            ),
        }
