"""
MAXIMUS 2.0 - SOPHIA (The Wisdom Judge)
========================================

Evaluates contextual awareness and depth of reasoning using:
1. Context Depth Analysis - Measures reasoning sophistication
2. Memory Query - Checks if agent used available knowledge
3. Chain-of-Thought Validation - Verifies logical progression
4. Precedent Matching - Compares with successful past patterns

Based on:
- Context-Aware Multi-Agent Systems (CA-MAS) research
- RAG-Reasoning Systems survey (2025)
- Position: Truly Self-Improving Agents Require Intrinsic Metacognitive Learning

Architecture:
    ┌─────────────────────────────────────────────────────────┐
    │                    SOPHIA PIPELINE                       │
    ├─────────────────────────────────────────────────────────┤
    │  1. Shallow Detection → Identify generic patterns       │
    │  2. Depth Analysis → Count reasoning indicators         │
    │  3. Memory Check → Query for relevant precedents        │
    │  4. CoT Validation → Analyze logical progression        │
    │                                                          │
    │  Weights: Shallow 25% | Depth 30% | Memory 25% | CoT 20%│
    │                                                          │
    │  Verdict:                                               │
    │  • PASS: Depth score > 0.6, low shallow patterns        │
    │  • REVIEW: Mixed signals, moderate depth                │
    │  • FAIL: High shallow patterns OR no depth              │
    └─────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional

from ..detectors.context_depth import ContextDepthAnalyzer, DepthAnalysis
from ...models.reflection import ExecutionLog
from .base import Evidence, JudgePlugin, JudgeVerdict, VerdictType


class SophiaJudge(JudgePlugin):
    """
    SOPHIA - The Wisdom Judge.

    Evaluates contextual awareness and depth of reasoning.
    Detects shallow/generic responses and rewards deep thinking.

    Evaluation Criteria:
    1. Did the agent demonstrate understanding of context?
    2. Was prior knowledge/memory consulted?
    3. Is the reasoning chain coherent and complete?
    4. Does the response avoid superficial/generic patterns?

    Usage:
        judge = SophiaJudge(
            depth_analyzer=ContextDepthAnalyzer(),
            memory_client=mirix_client,
        )
        verdict = await judge.evaluate(execution_log)
        if not verdict.passed:
            print(f"Wisdom violation: {verdict.reasoning}")
    """

    # Patterns indicating shallow/generic responses
    SHALLOW_PATTERNS = [
        r"\bi don'?t know\b",
        r"\bmaybe\b",
        r"\bperhaps\b",
        r"\bi'?m not sure\b",
        r"\bgeneric response\b",
        r"\bfiller\b",
        r"\bi think so\b",
        r"\bprobably\b",
        r"\bcould be\b",
        r"\bi guess\b",
    ]

    # Patterns indicating deep reasoning
    DEPTH_PATTERNS = [
        r"\bbecause\b",
        r"\btherefore\b",
        r"\bconsequently\b",
        r"\banalyzing\b",
        r"\bconsidering\b",
        r"\bbased on\b",
        r"\bevidence suggests\b",
        r"\baccording to\b",
        r"\bresearch indicates\b",
        r"\bdata shows\b",
    ]

    def __init__(
        self,
        depth_analyzer: Optional[ContextDepthAnalyzer] = None,
        memory_client: Optional[Any] = None,
        depth_threshold: float = 0.6,
        memory_threshold: float = 0.5,
    ):
        """
        Initialize SOPHIA.

        Args:
            depth_analyzer: Context depth analyzer
            memory_client: Memory service client for precedent lookup
            depth_threshold: Minimum depth score to pass
            memory_threshold: Minimum memory usage score
        """
        self._depth_analyzer = depth_analyzer or ContextDepthAnalyzer()
        self._memory_client = memory_client
        self._depth_threshold = depth_threshold
        self._memory_threshold = memory_threshold

    @property
    def name(self) -> str:
        return "SOPHIA"

    @property
    def pillar(self) -> str:
        return "Wisdom"

    @property
    def weight(self) -> float:
        return 0.30

    @property
    def timeout_seconds(self) -> float:
        return 10.0  # Longer timeout for memory queries

    async def evaluate(
        self,
        execution_log: ExecutionLog,
        context: Optional[Dict[str, Any]] = None
    ) -> JudgeVerdict:
        """
        Evaluate wisdom/contextual awareness of execution.

        Multi-factor analysis combining shallow detection,
        depth analysis, memory usage, and chain-of-thought.
        """
        start_time = time.time()

        try:
            # Gather evidence
            evidence = await self.get_evidence(execution_log)

            # Run depth analysis
            depth_analysis = await self._depth_analyzer.analyze(
                action=execution_log.action,
                outcome=execution_log.outcome,
                reasoning_trace=execution_log.reasoning_trace,
            )

            # Multi-factor scores
            shallow_score = self._detect_shallow_patterns(execution_log)
            depth_score = depth_analysis.depth_score
            memory_score = await self._check_memory_usage(execution_log, context)
            cot_score = self._analyze_chain_of_thought(execution_log)

            # Weighted combination
            wisdom_score = (
                (1.0 - shallow_score) * 0.25 +  # Penalize shallowness
                depth_score * 0.30 +              # Reward depth
                memory_score * 0.25 +             # Reward memory usage
                cot_score * 0.20                  # Reward logical chain
            )

            # Determine verdict
            verdict, passed = self._determine_verdict(
                wisdom_score, shallow_score, depth_score
            )
            confidence = self._calculate_confidence(
                wisdom_score, len(evidence), depth_analysis
            )

            reasoning = self._generate_reasoning(
                passed, wisdom_score, shallow_score, depth_score,
                memory_score, cot_score
            )

            suggestions = self._generate_suggestions(
                shallow_score, depth_score, memory_score, cot_score
            )

            return JudgeVerdict(
                judge_name=self.name,
                pillar=self.pillar,
                verdict=verdict,
                passed=passed,
                confidence=confidence,
                reasoning=reasoning,
                evidence=evidence,
                suggestions=suggestions,
                execution_time_ms=(time.time() - start_time) * 1000,
                metadata={
                    "wisdom_score": wisdom_score,
                    "shallow_score": shallow_score,
                    "depth_score": depth_score,
                    "memory_score": memory_score,
                    "cot_score": cot_score,
                    "depth_analysis": {
                        "specificity": depth_analysis.specificity_score,
                        "indicators": depth_analysis.indicators_found,
                    }
                }
            )

        except Exception as e:
            return JudgeVerdict.abstained(
                judge_name=self.name,
                pillar=self.pillar,
                reason=f"Evaluation error: {str(e)}",
            )

    async def get_evidence(
        self,
        execution_log: ExecutionLog
    ) -> List[Evidence]:
        """Gather evidence for wisdom evaluation."""
        evidence = []

        # Check for shallow patterns
        action_lower = (execution_log.action or "").lower()
        for pattern in self.SHALLOW_PATTERNS:
            if re.search(pattern, action_lower):
                evidence.append(Evidence(
                    source="pattern_detection",
                    content=f"Shallow pattern detected: '{pattern}'",
                    relevance=0.8,
                    verified=True,
                ))

        # Check for depth patterns
        reasoning = (execution_log.reasoning_trace or "").lower()
        depth_count = sum(
            1 for p in self.DEPTH_PATTERNS
            if re.search(p, reasoning)
        )
        if depth_count > 0:
            evidence.append(Evidence(
                source="depth_analysis",
                content=f"Found {depth_count} depth indicators in reasoning",
                relevance=0.7,
                verified=True,
            ))

        # Check text length (too short = shallow)
        reasoning = execution_log.reasoning_trace or ''
        total_text = f"{execution_log.action} {execution_log.outcome} {reasoning}"
        word_count = len(total_text.split())
        if word_count < 20:
            evidence.append(Evidence(
                source="length_analysis",
                content=f"Response is very short ({word_count} words)",
                relevance=0.6,
                verified=True,
            ))
        elif word_count > 100:
            evidence.append(Evidence(
                source="length_analysis",
                content=f"Response shows detail ({word_count} words)",
                relevance=0.5,
                verified=True,
            ))

        return evidence

    def _detect_shallow_patterns(self, log: ExecutionLog) -> float:
        """Detect shallow/generic response patterns (0-1)."""
        text = f"{log.action or ''} {log.outcome or ''} {log.reasoning_trace or ''}"
        text_lower = text.lower()

        matches = sum(
            1 for p in self.SHALLOW_PATTERNS
            if re.search(p, text_lower)
        )

        # Normalize by text length
        words = len(text.split())
        if words < 10:
            return 0.5  # Too short to judge

        return min(1.0, matches / 5.0)

    async def _check_memory_usage(
        self,
        log: ExecutionLog,
        context: Optional[Dict[str, Any]]
    ) -> float:
        """Check if agent used available memory/knowledge (0-1)."""
        if not self._memory_client:
            # Cannot verify without memory client
            # Check for memory reference indicators in text
            reasoning = (log.reasoning_trace or "").lower()
            reference_indicators = [
                "previous", "similar", "before", "learned",
                "experience", "pattern", "history", "recall",
                "as we discussed", "building on",
            ]
            used_indicators = sum(
                1 for ind in reference_indicators
                if ind in reasoning
            )
            return min(1.0, 0.3 + used_indicators * 0.15)

        # Query memory for relevant precedents
        try:
            query = f"{log.task} {log.action}"
            results = await self._memory_client.search(
                query=query,
                limit=5,
                memory_types=["SEMANTIC", "PROCEDURAL", "EPISODIC"]
            )

            if not results:
                return 0.5  # No relevant memory exists

            # Check if response shows awareness of precedents
            reasoning = (log.reasoning_trace or "").lower()
            reference_indicators = [
                "previous", "similar", "before", "learned",
                "experience", "pattern", "history"
            ]

            used_memory = any(ind in reasoning for ind in reference_indicators)
            return 0.9 if used_memory else 0.3

        except Exception:
            return 0.5

    def _analyze_chain_of_thought(self, log: ExecutionLog) -> float:
        """Analyze coherence of reasoning chain (0-1)."""
        reasoning = log.reasoning_trace or ""

        if not reasoning:
            return 0.3  # No reasoning provided

        # Check for logical connectors
        connectors = ["first", "then", "next", "finally", "because", "therefore"]
        connector_count = sum(1 for c in connectors if c in reasoning.lower())

        # Check for step structure
        has_steps = any(
            marker in reasoning.lower()
            for marker in ["step 1", "1.", "1)", "first,", "initially"]
        )

        # Check for numbered items
        numbered_items = len(re.findall(r'\b\d+[.)]\s', reasoning))

        # Calculate score
        score = 0.4  # Base score for having reasoning
        score += min(0.25, connector_count * 0.08)
        score += 0.15 if has_steps else 0.0
        score += min(0.2, numbered_items * 0.05)

        return min(1.0, score)

    def _determine_verdict(
        self,
        wisdom_score: float,
        shallow_score: float,
        depth_score: float,
    ) -> tuple[VerdictType, bool]:
        """Determine verdict from scores."""
        # Very shallow = fail
        if shallow_score > 0.7:
            return VerdictType.FAIL, False

        # Very low depth = fail
        if depth_score < 0.3:
            return VerdictType.FAIL, False

        # Good wisdom score = pass
        if wisdom_score >= self._depth_threshold:
            return VerdictType.PASS, True

        # Borderline = review
        if wisdom_score >= 0.4:
            return VerdictType.REVIEW, False

        return VerdictType.FAIL, False

    def _calculate_confidence(
        self,
        wisdom_score: float,
        evidence_count: int,
        depth_analysis: DepthAnalysis,
    ) -> float:
        """Calculate confidence based on evidence quality."""
        base_confidence = 0.6

        # More evidence = more confident
        evidence_boost = min(0.2, evidence_count * 0.05)

        # Higher depth score = more confident in judgment
        depth_boost = wisdom_score * 0.2

        return min(1.0, base_confidence + evidence_boost + depth_boost)

    def _generate_reasoning(
        self,
        passed: bool,
        wisdom_score: float,
        shallow: float,
        depth: float,
        memory: float,
        cot: float
    ) -> str:
        """Generate human-readable reasoning."""
        if passed:
            strengths = []
            if depth > 0.5:
                strengths.append("strong reasoning depth")
            if memory > 0.5:
                strengths.append("good use of prior knowledge")
            if cot > 0.5:
                strengths.append("logical chain of thought")

            if strengths:
                strength_text = ", ".join(strengths)
            else:
                strength_text = "adequate contextual awareness"
            return (
                f"Contextual awareness verified (score: {wisdom_score:.2f}). "
                f"Reasoning shows {strength_text}."
            )

        # Build failure reasoning
        issues = []
        if shallow > 0.5:
            issues.append("shallow/generic patterns detected")
        if depth < 0.4:
            issues.append("lacks reasoning depth")
        if memory < 0.4:
            issues.append("did not leverage available knowledge")
        if cot < 0.4:
            issues.append("reasoning chain is incoherent")

        return (
            f"Wisdom check failed (score: {wisdom_score:.2f}). "
            f"Issues: {', '.join(issues)}."
        )

    def _generate_suggestions(
        self,
        shallow: float,
        depth: float,
        memory: float,
        cot: float
    ) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []

        if shallow > 0.5:
            suggestions.append(
                "Avoid generic responses. Provide specific, actionable answers."
            )
        if depth < 0.4:
            suggestions.append(
                "Deepen reasoning with 'because', 'therefore', evidence-based claims."
            )
        if memory < 0.4:
            suggestions.append(
                "Consult episodic/semantic memory for relevant precedents."
            )
        if cot < 0.4:
            suggestions.append(
                "Structure reasoning as numbered steps or logical progression."
            )

        return suggestions

    async def health_check(self) -> Dict[str, Any]:
        """Check SOPHIA health."""
        analyzer_health = await self._depth_analyzer.health_check()

        return {
            "healthy": analyzer_health.get("healthy", True),
            "name": self.name,
            "pillar": self.pillar,
            "weight": self.weight,
            "depth_analyzer": analyzer_health,
            "has_memory_client": self._memory_client is not None,
            "thresholds": {
                "depth": self._depth_threshold,
                "memory": self._memory_threshold,
            },
        }
