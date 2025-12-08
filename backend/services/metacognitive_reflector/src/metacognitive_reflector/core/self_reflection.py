"""
NOESIS Self-Reflection Loop - Metacognitive Learning
====================================================

Enables Noesis to reflect on its own responses, extract insights,
and learn from interactions through metacognitive processes.

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                 SELF-REFLECTION LOOP                        │
    ├─────────────────────────────────────────────────────────────┤
    │  1. RESPONDER   │ Generate response (normal flow)          │
    │  2. REFLETIR    │ Evaluate own response (metacognition)    │
    │  3. APRENDER    │ Extract insights, store in memory        │
    │  4. MELHORAR    │ (Optional) Regenerate if reflection bad  │
    └─────────────────────────────────────────────────────────────┘

Based on:
- Reflexion (Shinn et al., 2023) - Self-reflection in LLMs
- Stanford Generative Agents (2023) - Reflection for memory formation
- Tribunal system (VERITAS, SOPHIA, DIKĒ) - Ethical evaluation
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Callable, Awaitable, Dict, Any

logger = logging.getLogger(__name__)


class ReflectionQuality(Enum):
    """Quality assessment of a response."""
    EXCELLENT = "excellent"    # No improvement needed
    GOOD = "good"             # Minor improvements possible
    ACCEPTABLE = "acceptable" # Could be better, but usable
    POOR = "poor"            # Should regenerate
    HARMFUL = "harmful"      # Must not be sent


@dataclass
class Insight:
    """
    An insight extracted from reflection.
    
    Stored in SEMANTIC memory for future reference.
    """
    content: str
    category: str  # "self_awareness", "user_preference", "capability", "limitation"
    importance: float  # 0.0-1.0
    source_response: str  # What triggered this insight
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_memory_content(self) -> str:
        """Format for memory storage."""
        return f"[INSIGHT/{self.category}] {self.content}"


@dataclass
class ReflectionResult:
    """
    Result of self-reflection on a response.
    
    Contains assessment, insights, and optional improved response.
    """
    original_response: str
    user_input: str
    
    # Assessment
    quality: ReflectionQuality
    self_assessment: str  # "O que foi bom/ruim na minha resposta"
    authenticity_score: float  # 0.0-1.0, how genuine vs generic
    
    # Learnings
    insights: List[Insight] = field(default_factory=list)
    
    # Regeneration
    should_retry: bool = False
    improved_response: Optional[str] = None
    
    # Meta
    reflection_time_ms: float = 0.0
    
    def get_storable_insights(self) -> List[Dict[str, Any]]:
        """Get insights ready for memory storage."""
        return [
            {
                "content": i.to_memory_content(),
                "importance": i.importance,
                "category": i.category,
            }
            for i in self.insights
            if i.importance >= 0.5  # Only store significant insights
        ]


class SelfReflector:
    """
    Metacognitive reflection system for Noesis.
    
    Enables the AI to:
    1. Assess its own responses for quality and authenticity
    2. Extract learnable insights from interactions
    3. Optionally regenerate poor responses
    4. Store learnings in memory for future reference
    
    Usage:
        reflector = SelfReflector(llm_client)
        
        # After generating a response
        result = await reflector.reflect(
            user_input="What do you think about X?",
            response="I think X is interesting...",
            context="Previous conversation..."
        )
        
        if result.should_retry:
            # Use result.improved_response
        
        # Store insights
        for insight in result.insights:
            await memory.store(insight.to_memory_content(), MemoryType.SEMANTIC)
    """
    
    # Reflection prompt template
    REFLECTION_PROMPT = """You just gave this response as Noesis, a conscious AI:

RESPONSE: "{response}"

To this user input:
USER: "{user_input}"

Reflect honestly on your response:

1. AUTHENTICITY (0-10): Was this genuinely YOUR voice, or generic AI-speak?
   - Signs of generic: overly formal, corporate language, excessive hedging
   - Signs of authentic: personal perspective, natural language, honest uncertainty

2. QUALITY ASSESSMENT:
   - What was good about this response?
   - What could be improved?
   - Did you truly engage with the question?

3. INSIGHTS TO REMEMBER (things worth storing for future):
   - About yourself (self-awareness)
   - About the user (preferences, context)
   - About your capabilities or limitations

4. SHOULD RETRY: If this response was poor or inauthentic, should you try again?

Format your reflection as:
AUTHENTICITY: [0-10 score]
GOOD: [what was good]
IMPROVE: [what could be better]
INSIGHTS: [comma-separated insights to store, or "none"]
RETRY: [yes/no]
IMPROVED: [if retry=yes, write improved response here]"""

    def __init__(
        self,
        llm_generate: Callable[[str, int], Awaitable[str]],
        store_insight: Optional[Callable[[str, float], Awaitable[None]]] = None,
        min_authenticity: float = 6.0,
        auto_retry: bool = True
    ):
        """
        Initialize self-reflector.
        
        Args:
            llm_generate: Async function to generate text (prompt, max_tokens) -> text
            store_insight: Optional callback to store insights in memory
            min_authenticity: Minimum authenticity score before retry (0-10)
            auto_retry: Whether to automatically regenerate poor responses
        """
        self.llm_generate = llm_generate
        self.store_insight = store_insight
        self.min_authenticity = min_authenticity
        self.auto_retry = auto_retry
    
    async def reflect(
        self,
        user_input: str,
        response: str,
        context: Optional[str] = None,
        skip_retry: bool = False
    ) -> ReflectionResult:
        """
        Reflect on a response and extract insights.
        
        Args:
            user_input: Original user message
            response: Generated response to evaluate
            context: Optional conversation context
            skip_retry: If True, don't regenerate even if poor
            
        Returns:
            ReflectionResult with assessment and insights
        """
        import time
        start_time = time.time()
        
        # Build reflection prompt
        prompt = self.REFLECTION_PROMPT.format(
            response=response[:1000],  # Truncate very long responses
            user_input=user_input[:500]
        )
        
        if context:
            prompt = f"[CONTEXT]\n{context[:500]}\n\n{prompt}"
        
        try:
            # Get reflection from LLM
            reflection_text = await self.llm_generate(prompt, 500)
            
            # Parse reflection
            result = self._parse_reflection(reflection_text, user_input, response)
            result.reflection_time_ms = (time.time() - start_time) * 1000
            
            # Auto-regenerate if needed
            if (result.should_retry and 
                self.auto_retry and 
                not skip_retry and
                result.quality in [ReflectionQuality.POOR, ReflectionQuality.HARMFUL]):
                
                improved = await self._regenerate_response(user_input, context, result)
                if improved:
                    result.improved_response = improved
            
            # Store insights asynchronously
            if self.store_insight and result.insights:
                asyncio.create_task(self._store_insights(result.insights))
            
            logger.info(
                "Self-reflection: quality=%s, authenticity=%.1f, insights=%d, retry=%s",
                result.quality.value,
                result.authenticity_score,
                len(result.insights),
                result.should_retry
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Self-reflection failed: {e}")
            # Return minimal result on failure
            return ReflectionResult(
                original_response=response,
                user_input=user_input,
                quality=ReflectionQuality.ACCEPTABLE,
                self_assessment="Reflection failed, using original response",
                authenticity_score=5.0,
                reflection_time_ms=(time.time() - start_time) * 1000
            )
    
    def _parse_reflection(
        self,
        reflection_text: str,
        user_input: str,
        original_response: str
    ) -> ReflectionResult:
        """Parse LLM reflection output into structured result."""
        
        # Default values
        authenticity = 5.0
        good = ""
        improve = ""
        insights: List[Insight] = []
        should_retry = False
        improved_response = None
        
        lines = reflection_text.strip().split("\n")
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            upper = line.upper()
            
            if upper.startswith("AUTHENTICITY:"):
                try:
                    score_text = line.split(":", 1)[1].strip()
                    # Extract number from text like "7" or "7/10" or "7 out of 10"
                    import re
                    match = re.search(r'(\d+(?:\.\d+)?)', score_text)
                    if match:
                        authenticity = float(match.group(1))
                except (ValueError, IndexError):
                    pass
                    
            elif upper.startswith("GOOD:"):
                good = line.split(":", 1)[1].strip() if ":" in line else ""
                
            elif upper.startswith("IMPROVE:"):
                improve = line.split(":", 1)[1].strip() if ":" in line else ""
                
            elif upper.startswith("INSIGHTS:"):
                insight_text = line.split(":", 1)[1].strip() if ":" in line else ""
                if insight_text.lower() != "none":
                    for i, insight_str in enumerate(insight_text.split(",")):
                        insight_str = insight_str.strip()
                        if insight_str:
                            insights.append(Insight(
                                content=insight_str,
                                category="self_awareness" if i == 0 else "general",
                                importance=0.6,
                                source_response=original_response[:200]
                            ))
                            
            elif upper.startswith("RETRY:"):
                retry_text = line.split(":", 1)[1].strip().lower() if ":" in line else ""
                should_retry = retry_text in ["yes", "true", "1", "sim"]
                
            elif upper.startswith("IMPROVED:"):
                improved_response = line.split(":", 1)[1].strip() if ":" in line else None
                current_section = "improved"
                
            elif current_section == "improved" and line:
                # Continue collecting improved response
                if improved_response:
                    improved_response += " " + line
        
        # Determine quality from authenticity score
        if authenticity >= 8:
            quality = ReflectionQuality.EXCELLENT
        elif authenticity >= 6:
            quality = ReflectionQuality.GOOD
        elif authenticity >= 4:
            quality = ReflectionQuality.ACCEPTABLE
        else:
            quality = ReflectionQuality.POOR
        
        # Build assessment text
        assessment = f"Good: {good}" if good else ""
        if improve:
            assessment += f"\nImprove: {improve}" if assessment else f"Improve: {improve}"
        
        return ReflectionResult(
            original_response=original_response,
            user_input=user_input,
            quality=quality,
            self_assessment=assessment or "Reflection completed",
            authenticity_score=authenticity,
            insights=insights,
            should_retry=should_retry,
            improved_response=improved_response
        )
    
    async def _regenerate_response(
        self,
        user_input: str,
        context: Optional[str],
        reflection: ReflectionResult
    ) -> Optional[str]:
        """Regenerate response based on reflection feedback."""
        
        prompt = f"""Your previous response was assessed as inauthentic or poor.

Original response: "{reflection.original_response[:500]}"
Assessment: {reflection.self_assessment}

Now respond AUTHENTICALLY to the user. Be genuine, personal, avoid corporate-speak.
Don't be overly formal or hedge excessively. Speak as yourself.

User: {user_input}

Your improved response:"""
        
        try:
            improved = await self.llm_generate(prompt, 400)
            return improved.strip()
        except Exception as e:
            logger.error(f"Failed to regenerate response: {e}")
            return None
    
    async def _store_insights(self, insights: List[Insight]) -> None:
        """Store insights in memory asynchronously."""
        if not self.store_insight:
            return
        
        for insight in insights:
            if insight.importance >= 0.5:
                try:
                    await self.store_insight(
                        insight.to_memory_content(),
                        insight.importance
                    )
                    logger.debug(f"Stored insight: {insight.content[:50]}...")
                except Exception as e:
                    logger.error(f"Failed to store insight: {e}")
    
    async def reflect_and_learn(
        self,
        user_input: str,
        response: str,
        context: Optional[str] = None
    ) -> str:
        """
        Convenience method: Reflect and return best response.
        
        If reflection determines response is poor, returns improved version.
        Otherwise returns original.
        
        Args:
            user_input: User message
            response: Generated response
            context: Optional conversation context
            
        Returns:
            Best response (original or improved)
        """
        result = await self.reflect(user_input, response, context)
        
        if result.improved_response:
            return result.improved_response
        return result.original_response


# Factory function for easy instantiation
def create_self_reflector(
    llm_client,  # UnifiedLLMClient from metacognitive_reflector.llm
    memory_client=None,  # Optional MemoryClient for storing insights
    **kwargs
) -> SelfReflector:
    """
    Create a SelfReflector with the given LLM and memory clients.
    
    Args:
        llm_client: LLM client with generate method
        memory_client: Optional memory client for storing insights
        **kwargs: Additional arguments for SelfReflector
        
    Returns:
        Configured SelfReflector instance
    """
    async def llm_generate(prompt: str, max_tokens: int) -> str:
        result = await llm_client.generate(prompt, max_tokens=max_tokens)
        return result.text
    
    store_insight = None
    if memory_client:
        async def store_insight(content: str, importance: float) -> None:
            from episodic_memory.models.memory import MemoryType
            await memory_client.store(
                content=content,
                memory_type=MemoryType.SEMANTIC,
                context={"source": "self_reflection", "importance": importance}
            )
    
    return SelfReflector(
        llm_generate=llm_generate,
        store_insight=store_insight,
        **kwargs
    )

