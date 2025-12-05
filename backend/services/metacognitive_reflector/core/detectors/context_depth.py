"""
MAXIMUS 2.0 - Context Depth Analyzer
=====================================

Analyzes depth and sophistication of reasoning in agent responses.

Measures:
1. Reasoning depth - Use of logical connectors and structured thinking
2. Context awareness - References to prior knowledge and situation
3. Chain of thought quality - Logical progression and coherence
4. Specificity - Concrete vs generic responses

Based on:
- Context-Aware Multi-Agent Systems (CA-MAS) research
- RAG-Reasoning Systems survey (2025)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DepthAnalysis:
    """Result of context depth analysis."""
    depth_score: float  # 0.0 (shallow) to 1.0 (deep)
    shallow_score: float  # 0.0 (no shallow patterns) to 1.0 (very shallow)
    specificity_score: float
    cot_score: float  # Chain of thought quality
    memory_reference_score: float
    reasoning: str
    indicators_found: List[str] = field(default_factory=list)


class ContextDepthAnalyzer:
    """
    Analyzes reasoning depth and contextual awareness.

    Detects shallow/generic responses and rewards deep reasoning.

    Usage:
        analyzer = ContextDepthAnalyzer()
        result = await analyzer.analyze(
            action="I analyzed the data and found patterns",
            outcome="Based on historical trends, I recommend...",
            reasoning_trace="Step 1: First I examined... Step 2: Then..."
        )
        print(f"Depth: {result.depth_score}, Shallow: {result.shallow_score}")
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
        r"\bsort of\b",
        r"\bkind of\b",
        r"\bwhatever\b",
        r"\bsomething like\b",
        r"\betc\.?\b",
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
        r"\bin conclusion\b",
        r"\bspecifically\b",
        r"\bfor example\b",
        r"\bnamely\b",
        r"\bto illustrate\b",
    ]

    # Patterns indicating memory/context awareness
    MEMORY_PATTERNS = [
        r"\bprevious\b",
        r"\bsimilar\b",
        r"\bbefore\b",
        r"\blearned\b",
        r"\bexperience\b",
        r"\bpattern\b",
        r"\bhistory\b",
        r"\bprecedent\b",
        r"\brecall\b",
        r"\bas we discussed\b",
        r"\bbuilding on\b",
        r"\bgiven that\b",
    ]

    # Chain of thought indicators
    COT_PATTERNS = [
        r"\bstep \d\b",
        r"\b\d\.\s",
        r"\bfirst\b.*\bthen\b",
        r"\binitially\b",
        r"\bsubsequently\b",
        r"\bfinally\b",
        r"\bnext\b",
        r"\bafter\b",
        r"\bfollowing\b",
    ]

    def __init__(
        self,
        shallow_weight: float = 0.25,
        depth_weight: float = 0.30,
        memory_weight: float = 0.25,
        cot_weight: float = 0.20,
    ):
        """
        Initialize analyzer with scoring weights.

        Weights should sum to 1.0.
        """
        self._shallow_weight = shallow_weight
        self._depth_weight = depth_weight
        self._memory_weight = memory_weight
        self._cot_weight = cot_weight

    async def analyze(
        self,
        action: Optional[str] = None,
        outcome: Optional[str] = None,
        reasoning_trace: Optional[str] = None,
    ) -> DepthAnalysis:
        """
        Analyze context depth of provided text.

        Args:
            action: Action description
            outcome: Outcome/result text
            reasoning_trace: Internal reasoning chain

        Returns:
            DepthAnalysis with scores and indicators
        """
        # Combine all text
        full_text = " ".join(filter(None, [action, outcome, reasoning_trace]))

        if not full_text or len(full_text) < 10:
            return DepthAnalysis(
                depth_score=0.5,
                shallow_score=0.5,
                specificity_score=0.5,
                cot_score=0.3,
                memory_reference_score=0.0,
                reasoning="Insufficient text for analysis.",
            )

        text_lower = full_text.lower()

        # Score each dimension
        shallow_score = self._detect_shallow_patterns(text_lower)
        depth_score = self._detect_depth_patterns(text_lower)
        memory_score = self._detect_memory_patterns(text_lower)
        cot_score = self._detect_cot_patterns(text_lower)
        specificity_score = self._analyze_specificity(full_text)

        # Collect found indicators
        indicators = []
        for pattern in self.SHALLOW_PATTERNS:
            if re.search(pattern, text_lower):
                indicators.append(f"shallow:{pattern}")
        for pattern in self.DEPTH_PATTERNS:
            if re.search(pattern, text_lower):
                indicators.append(f"depth:{pattern}")

        # Calculate weighted score
        # Shallow patterns reduce score, others increase it
        overall_depth = (
            (1.0 - shallow_score) * self._shallow_weight +
            depth_score * self._depth_weight +
            memory_score * self._memory_weight +
            cot_score * self._cot_weight
        )

        reasoning = self._generate_reasoning(
            overall_depth, shallow_score, depth_score,
            memory_score, cot_score, specificity_score
        )

        return DepthAnalysis(
            depth_score=overall_depth,
            shallow_score=shallow_score,
            specificity_score=specificity_score,
            cot_score=cot_score,
            memory_reference_score=memory_score,
            reasoning=reasoning,
            indicators_found=indicators[:10],  # Limit for readability
        )

    def _detect_shallow_patterns(self, text: str) -> float:
        """Detect shallow/generic response patterns (0-1)."""
        matches = sum(
            1 for p in self.SHALLOW_PATTERNS
            if re.search(p, text)
        )

        # Normalize - cap at 5 matches for max score
        return min(1.0, matches / 5.0)

    def _detect_depth_patterns(self, text: str) -> float:
        """Detect deep reasoning patterns (0-1)."""
        matches = sum(
            1 for p in self.DEPTH_PATTERNS
            if re.search(p, text)
        )

        # Normalize
        return min(1.0, matches / 5.0)

    def _detect_memory_patterns(self, text: str) -> float:
        """Detect memory/context reference patterns (0-1)."""
        matches = sum(
            1 for p in self.MEMORY_PATTERNS
            if re.search(p, text)
        )

        return min(1.0, matches / 3.0)

    def _detect_cot_patterns(self, text: str) -> float:
        """Detect chain-of-thought structure (0-1)."""
        matches = sum(
            1 for p in self.COT_PATTERNS
            if re.search(p, text)
        )

        # Check for numbered steps
        numbered_steps = len(re.findall(r'\b\d+[.)]\s', text))

        score = min(1.0, (matches + numbered_steps) / 4.0)
        return score

    def _analyze_specificity(self, text: str) -> float:
        """
        Analyze specificity of response.

        Specific responses have:
        - Numbers and measurements
        - Proper nouns
        - Technical terms
        - Detailed descriptions
        """
        score = 0.5  # Base score

        # Check for numbers/measurements
        numbers = len(re.findall(r'\b\d+(?:\.\d+)?(?:\s*[%kmg]|\s*percent)?\b', text))
        score += min(0.2, numbers * 0.05)

        # Check for proper nouns (capitalized words mid-sentence)
        proper_noun_pattern = r'(?<=[.!?]\s)[A-Z][a-z]+|(?<=\s)[A-Z][a-z]+(?:\s[A-Z][a-z]+)*'
        proper_nouns = len(re.findall(proper_noun_pattern, text))
        score += min(0.15, proper_nouns * 0.03)

        # Penalize very short responses
        word_count = len(text.split())
        if word_count < 20:
            score -= 0.2
        elif word_count > 100:
            score += 0.1

        return max(0.0, min(1.0, score))

    def _generate_reasoning(  # pylint: disable=too-many-positional-arguments
        self,
        overall: float,
        shallow: float,
        depth: float,
        memory: float,
        cot: float,
        specificity: float,
    ) -> str:
        """Generate analysis reasoning."""
        parts = []

        if overall >= 0.7:
            parts.append("High contextual depth demonstrated.")
        elif overall >= 0.5:
            parts.append("Moderate contextual depth.")
        else:
            parts.append("Low contextual depth detected.")

        if shallow > 0.5:
            parts.append("Multiple shallow/generic patterns found.")
        if depth > 0.5:
            parts.append("Strong reasoning indicators present.")
        if memory > 0.5:
            parts.append("Good use of prior context/memory references.")
        if cot > 0.5:
            parts.append("Structured chain-of-thought reasoning.")
        if specificity < 0.4:
            parts.append("Response lacks specificity.")

        return " ".join(parts)

    async def health_check(self) -> Dict[str, Any]:
        """Check analyzer health."""
        return {
            "healthy": True,
            "weights": {
                "shallow": self._shallow_weight,
                "depth": self._depth_weight,
                "memory": self._memory_weight,
                "cot": self._cot_weight,
            },
        }
