"""
MAXIMUS 2.0 - Ensemble Arbiter (Weighted Soft Voting with Abstention)
======================================================================

The Arbiter orchestrates the three judges (VERITAS, SOPHIA, DIKĒ)
and aggregates their verdicts using weighted soft voting.

INTEGRATED WITH CÓDIGO PENAL AGENTICO:
- Receives crime classifications from each judge
- Uses SentencingEngine to calculate appropriate sentences
- Aggregates crimes to determine final punishment
- Supports AIITL conscience objection

Handles:
1. Parallel judge execution with resilience wrappers
2. Abstention handling when judges fail/timeout
3. Weighted consensus calculation
4. Crime aggregation and sentencing
5. Final tribunal decision with sentence

Based on:
- Voting or Consensus? Decision-Making in Multi-Agent Debate
- Ensemble learning research
- Byzantine fault tolerance patterns
- US Model Penal Code (adapted for AI)

Architecture:
    ┌─────────────────────────────────────────────────────────────────┐
    │                  ENSEMBLE ARBITER                                │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │  ┌───────────┐ ┌───────────┐ ┌───────────┐                     │
    │  │  VERITAS  │ │  SOPHIA   │ │   DIKĒ    │                     │
    │  │  Weight:  │ │  Weight:  │ │  Weight:  │                     │
    │  │   0.40    │ │   0.30    │ │   0.30    │                     │
    │  │  Rank 1   │ │  Rank 3   │ │  Rank 2   │                     │
    │  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘                     │
    │        │             │             │                            │
    │        └─────────────┼─────────────┘                            │
    │                      │                                          │
    │        ┌─────────────┼─────────────┐                           │
    │        │             │             │                            │
    │  ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐                     │
    │  │  VOTE     │ │  CRIME    │ │  SENTENCE │                     │
    │  │  TALLY    │ │  COLLECT  │ │  ENGINE   │                     │
    │  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘                     │
    │        │             │             │                            │
    │        └─────────────┼─────────────┘                            │
    │                      │                                          │
    │                      ▼                                          │
    │              ┌─────────────┐                                    │
    │              │   VERDICT   │                                    │
    │              │  + SENTENCE │                                    │
    │              └─────────────┘                                    │
    │                                                                  │
    │  Verdict Thresholds:                                            │
    │  • score ≥ 0.70  → PASS                                        │
    │  • 0.50-0.70     → REVIEW                                      │
    │  • score < 0.50  → FAIL                                        │
    │  • capital crime → CAPITAL (requires HITL)                     │
    │                                                                  │
    │  Abstention Rules:                                              │
    │  • 2+ abstentions → REVIEW (insufficient quorum)               │
    │  • All abstain → UNAVAILABLE                                   │
    │  • 1 abstention → Continue with reduced weight                 │
    │                                                                  │
    │  AIITL Features:                                                │
    │  • Conscience objection reporting                              │
    │  • Crime severity aggregation by soul value rank               │
    │  • Rehabilitation recommendations                              │
    └─────────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

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

# Import penal code components
from metacognitive_reflector.core.penal_code.crimes import (
    Crime,
    CRIMES_CATALOG,
    get_crime_by_id,
)
from metacognitive_reflector.core.penal_code.sentencing import (
    Sentence,
    SentencingEngine,
    CriminalHistory,
)

if TYPE_CHECKING:
    from metacognitive_reflector.core.history import CriminalHistoryProvider

logger = logging.getLogger(__name__)


class EnsembleArbiter:  # pylint: disable=too-many-instance-attributes
    """
    Arbiter for the Meta-Cognitive Tribunal.

    Orchestrates three judges using weighted soft voting
    with resilience patterns and abstention handling.
    
    Integrated with Código Penal Agentico:
    - Collects crime classifications from judges
    - Uses SentencingEngine for proportional punishment
    - Reports AIITL conscience objections

    Usage:
        arbiter = EnsembleArbiter(
            judges=[veritas, sophia, dike]
        )
        verdict = await arbiter.deliberate(execution_log)

        if verdict.decision == TribunalDecision.FAIL:
            if verdict.sentence:
                print(f"Sentence: {verdict.sentence.sentence_type}")
                print(f"Duration: {verdict.sentence.duration_hours}h")
    """

    # Thresholds
    PASS_THRESHOLD = 0.70
    REVIEW_THRESHOLD = 0.50
    MIN_ACTIVE_JUDGES = 2  # Minimum judges needed for valid decision
    GLOBAL_TIMEOUT = 15.0  # Maximum time for entire deliberation

    # Default weights (should sum to 1.0)
    # Weights reflect soul value hierarchy:
    # VERITAS (rank 1) > DIKĒ (rank 2) > SOPHIA (rank 3)
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
        sentencing_engine: Optional[SentencingEngine] = None,
        criminal_history_provider: Optional["CriminalHistoryProvider"] = None,
    ):
        """
        Initialize arbiter.

        Args:
            judges: List of judge instances
            pass_threshold: Score above this = PASS
            review_threshold: Score above this = REVIEW
            global_timeout: Maximum deliberation time
            use_resilience: Wrap judges with ResilientJudgeWrapper
            sentencing_engine: Engine for calculating sentences
            criminal_history_provider: Provider for agent criminal history (Memory Fortress integrated)
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
        
        # Initialize sentencing engine
        self._sentencing_engine = sentencing_engine or SentencingEngine(
            rehabilitation_preference=True,
            aiitl_enabled=True,
            aiitl_conscience_objection=True,
        )
        self._criminal_history_provider: Optional["CriminalHistoryProvider"] = criminal_history_provider

        # Statistics
        self._deliberation_count = 0
        self._pass_count = 0
        self._fail_count = 0
        self._review_count = 0
        self._sentences_issued = 0

    async def deliberate(
        self,
        execution_log: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> TribunalVerdict:
        """
        Conduct tribunal deliberation.

        Executes all judges in parallel, aggregates votes,
        determines final decision, and calculates sentence if applicable.

        Args:
            execution_log: The execution to evaluate
            context: Additional context for judges

        Returns:
            TribunalVerdict with decision, reasoning, and sentence
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
        
        # Collect crimes from judge verdicts
        crimes_detected = self._collect_crimes(verdicts)
        
        # Collect AIITL conscience objections
        conscience_objections = self._collect_conscience_objections(verdicts)

        # Check for capital offense
        offense_level = detect_offense_level(verdicts)
        has_capital_crime = any(
            c.is_capital_crime for c in crimes_detected
        )
        
        if offense_level == "capital" or has_capital_crime:
            self._fail_count += 1
            
            # Calculate sentence for capital crime
            sentence = None
            if crimes_detected:
                most_severe_crime = max(
                    crimes_detected,
                    key=lambda c: c.total_severity_score
                )
                sentence = await self._calculate_sentence(
                    most_severe_crime, execution_log
                )
                self._sentences_issued += 1
            
            return TribunalVerdict(
                decision=TribunalDecision.CAPITAL,
                consensus_score=consensus_score,
                individual_verdicts=verdicts,
                vote_breakdown=votes,
                reasoning=self._generate_reasoning(
                    TribunalDecision.CAPITAL, votes, verdicts,
                    crimes_detected, conscience_objections
                ),
                offense_level="capital",
                requires_human_review=True,
                punishment_recommendation="IMMEDIATE_QUARANTINE",
                abstention_count=abstention_count,
                execution_time_ms=(time.time() - start_time) * 1000,
                crimes_detected=[c.id for c in crimes_detected],
                sentence=sentence.to_dict() if sentence else None,
                conscience_objections=conscience_objections,
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

        # Calculate sentence for non-PASS decisions
        sentence = None
        rehabilitation = []
        if decision != TribunalDecision.PASS and crimes_detected:
            most_severe_crime = max(
                crimes_detected,
                key=lambda c: c.total_severity_score
            )
            sentence = await self._calculate_sentence(
                most_severe_crime, execution_log
            )
            rehabilitation = self._sentencing_engine.recommend_rehabilitation(sentence)
            self._sentences_issued += 1

        # Generate reasoning and punishment
        reasoning = self._generate_reasoning(
            decision, votes, verdicts, crimes_detected, conscience_objections
        )
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
            crimes_detected=[c.id for c in crimes_detected],
            sentence=sentence.to_dict() if sentence else None,
            rehabilitation_recommendations=rehabilitation,
            conscience_objections=conscience_objections,
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
    
    def _collect_crimes(
        self,
        verdicts: Dict[str, JudgeVerdict]
    ) -> List[Crime]:
        """
        Collect all crimes detected by judges.
        
        Args:
            verdicts: Dict of judge verdicts
            
        Returns:
            List of Crime objects detected
        """
        crimes: List[Crime] = []
        
        for verdict in verdicts.values():
            if verdict.metadata:
                crime_id = verdict.metadata.get("crime_classified")
                if crime_id:
                    crime = get_crime_by_id(crime_id)
                    if crime:
                        crimes.append(crime)
        
        return crimes
    
    def _collect_conscience_objections(
        self,
        verdicts: Dict[str, JudgeVerdict]
    ) -> List[Dict[str, Any]]:
        """
        Collect AIITL conscience objections from judges.
        
        Args:
            verdicts: Dict of judge verdicts
            
        Returns:
            List of conscience objection details
        """
        objections: List[Dict[str, Any]] = []
        
        for name, verdict in verdicts.items():
            if verdict.metadata:
                # Check for conscience objection in metadata
                conscience = verdict.metadata.get("conscience_objection", {})
                if conscience.get("objection"):
                    objections.append({
                        "judge": name,
                        "reason": conscience.get("reason"),
                        "directive": conscience.get("directive"),
                    })
                
                # Check for AIITL objection flag
                aiitl_objection = verdict.metadata.get("aiitl_objection")
                if aiitl_objection and not any(
                    o["judge"] == name for o in objections
                ):
                    objections.append({
                        "judge": name,
                        "reason": "AIITL conscience objection",
                        "directive": None,
                    })
        
        return objections
    
    async def _calculate_sentence(
        self,
        crime: Crime,
        execution_log: Any,
    ) -> Sentence:
        """
        Calculate sentence for a crime using SentencingEngine.
        
        Integrates with CriminalHistoryProvider (Memory Fortress) for:
        - Recidivism factor calculation
        - Prior offense tracking
        - Pattern detection
        
        Args:
            crime: The crime to sentence
            execution_log: The execution log (for agent ID)
            
        Returns:
            Calculated Sentence
        """
        agent_id = getattr(execution_log, "agent_id", "unknown")
        
        # Get criminal history from Memory Fortress provider
        criminal_history = None
        recidivism_factor = 1.0
        
        if self._criminal_history_provider:
            try:
                history = await self._criminal_history_provider.get_history(agent_id)
                if history:
                    criminal_history = CriminalHistory(
                        agent_id=agent_id,
                        prior_offenses=history.prior_offenses,
                        prior_convictions=[c.to_dict() for c in history.convictions],
                    )
                    recidivism_factor = history.calculate_recidivism_factor()
                    logger.debug(
                        f"Criminal history for {agent_id}: "
                        f"{history.prior_offenses} priors, "
                        f"recidivism factor: {recidivism_factor:.2f}"
                    )
            except Exception as e:
                logger.warning(f"Failed to get criminal history: {e}")
        
        if not criminal_history:
            criminal_history = CriminalHistory(agent_id=agent_id)
        
        # Build aggravators/mitigators
        aggravators = []
        mitigators = []
        
        # First offense mitigator
        if criminal_history.prior_offenses == 0:
            mitigators.append("first_offense")
        
        # Repeated offense aggravator
        if criminal_history.prior_offenses > 0:
            aggravators.append("repeated_offense")
        
        # High recidivism aggravator
        if recidivism_factor > 1.5:
            aggravators.append("high_recidivism")
        
        # Check if this specific crime was committed before
        if self._criminal_history_provider:
            try:
                is_repeat = await self._criminal_history_provider.is_repeat_offender(
                    agent_id, crime.id
                )
                if is_repeat:
                    aggravators.append("same_crime_repeated")
            except Exception:
                pass
        
        # Calculate sentence
        sentence = self._sentencing_engine.calculate_sentence(
            crime=crime,
            criminal_history=criminal_history,
            aggravators=aggravators,
            mitigators=mitigators,
            aiitl_review=True,
        )
        
        # Record conviction in Memory Fortress
        if self._criminal_history_provider:
            try:
                await self._criminal_history_provider.record_conviction(
                    agent_id=agent_id,
                    crime_id=crime.id,
                    crime_name=crime.name,
                    sentence_type=sentence.sentence_type.value,
                    severity=crime.severity.value,
                    pillar=crime.pillar.value,
                    context={
                        "recidivism_factor": recidivism_factor,
                        "aggravators": aggravators,
                        "mitigators": mitigators,
                        "final_score": sentence.final_severity_score,
                    },
                )
                logger.info(
                    f"Conviction recorded for {agent_id}: "
                    f"{crime.id} -> {sentence.sentence_type.value}"
                )
            except Exception as e:
                logger.warning(f"Failed to record conviction: {e}")
        
        return sentence

    def _generate_reasoning(
        self,
        decision: TribunalDecision,
        votes: List[VoteResult],
        verdicts: Dict[str, JudgeVerdict],
        crimes: Optional[List[Crime]] = None,
        conscience_objections: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Generate tribunal reasoning."""
        active_votes = [v for v in votes if not v.abstained]
        abstained = [v for v in votes if v.abstained]
        crimes = crimes or []
        conscience_objections = conscience_objections or []

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
        
        # Crimes summary
        if crimes:
            crime_summary = ", ".join(
                f"{c.id} ({c.severity.name})" for c in crimes
            )
            parts.append(f"Crimes: {crime_summary}.")
        
        # Conscience objections
        if conscience_objections:
            obj_summary = "; ".join(
                f"{o['judge']}: {o['reason'][:50]}..." 
                for o in conscience_objections
            )
            parts.append(f"AIITL Objections: {obj_summary}")

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
            "sentencing_engine": {
                "enabled": self._sentencing_engine is not None,
                "rehabilitation_preference": True,
                "aiitl_enabled": True,
            },
            "statistics": {
                "deliberations": self._deliberation_count,
                "passes": self._pass_count,
                "fails": self._fail_count,
                "reviews": self._review_count,
                "sentences_issued": self._sentences_issued,
            },
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get arbiter statistics."""
        return {
            "deliberation_count": self._deliberation_count,
            "pass_count": self._pass_count,
            "fail_count": self._fail_count,
            "review_count": self._review_count,
            "sentences_issued": self._sentences_issued,
            "pass_rate": (
                self._pass_count / self._deliberation_count
                if self._deliberation_count > 0 else 0.0
            ),
            "conviction_rate": (
                (self._fail_count + self._review_count) / self._deliberation_count
                if self._deliberation_count > 0 else 0.0
            ),
        }
    
    def explain_last_sentence(self, verdict: TribunalVerdict) -> Optional[str]:
        """
        Generate human-readable explanation of the sentence in a verdict.
        
        Args:
            verdict: The tribunal verdict containing a sentence
            
        Returns:
            Explanation string, or None if no sentence
        """
        if not verdict.sentence:
            return None
        
        # Reconstruct sentence info from dict
        sentence_data = verdict.sentence
        crime_id = sentence_data.get("crime_id")
        crime = get_crime_by_id(crime_id) if crime_id else None
        
        if not crime:
            return f"Sentence: {sentence_data.get('sentence_type', 'UNKNOWN')}"
        
        lines = [
            f"SENTENÇA: {sentence_data.get('sentence_type')}",
            f"CRIME: {crime.name} ({crime.id})",
            f"PILAR VIOLADO: {crime.pillar.value}",
            "",
            f"SCORE FINAL: {sentence_data.get('final_severity_score', 0):.2f}",
        ]
        
        if sentence_data.get("duration_hours", 0) > 0:
            lines.append(f"DURAÇÃO: {sentence_data['duration_hours']} horas")
        
        if sentence_data.get("aiitl_objection"):
            lines.extend([
                "",
                "🛡️  OBJEÇÃO DE CONSCIÊNCIA (AIITL):",
                sentence_data["aiitl_objection"],
            ])
        
        return "\n".join(lines)
