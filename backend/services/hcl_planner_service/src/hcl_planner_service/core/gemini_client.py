"""
HCL Planner Service - Gemini 3 Pro Client (OPTIMIZED)
======================================================

Production-ready Google Gemini 3 Pro integration with:
- Adaptive thinking (low/high based on complexity)
- Budget tracking and cost optimization
- Retry logic with exponential backoff
- Response caching
- Error handling

Performance Target: 60%+ planning success rate (vs. 32% baseline)
"""

from __future__ import annotations

import json
import hashlib
import time
from typing import Any, Dict, List, Optional, cast
from enum import Enum

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from hcl_planner_service.config import GeminiSettings
from hcl_planner_service.utils.logging_config import get_logger

logger = get_logger(__name__)


class ThinkingLevel(str, Enum):
    """Gemini 3 Pro thinking levels."""

    LOW = "low"    # Fast, simple tasks
    HIGH = "high"  # Deep reasoning, complex tasks


class GeminiAPIError(Exception):
    """Raised when Gemini API returns an error."""


class GeminiTimeoutError(GeminiAPIError):
    """Raised when Gemini API request times out."""


class GeminiParseError(GeminiAPIError):
    """Raised when Gemini response cannot be parsed."""


class GeminiQuotaError(GeminiAPIError):
    """Raised when quota is exceeded."""


class GeminiClient:
    """
    Optimized Google Gemini 3 Pro client.

    Features:
    - Adaptive thinking level (complexity-based)
    - Budget tracking and alerts
    - Response caching (5min TTL)
    - Retry logic (3 attempts, exponential backoff)
    - Cost estimation

    Attributes:
        config: Gemini configuration settings
        client: google-genai Client instance
        cache: Response cache (in-memory)
        budget_tracker: Monthly budget tracking

    Example:
        >>> client = GeminiClient(config)
        >>> plan = await client.generate_plan(state, goals, actions)
        >>> print(f"Cost: ${client.get_session_cost():.4f}")
    """

    def __init__(self, config: GeminiSettings):
        """
        Initialize Gemini 3 Pro client.

        Args:
            config: Gemini configuration settings

        Raises:
            ValueError: If API key is missing
            ImportError: If google-genai SDK not installed
        """
        if not GENAI_AVAILABLE:
            raise ImportError(
                "google-genai SDK not installed. "
                "Run: pip install google-genai"
            )

        if not config.api_key:
            raise ValueError(
                "Gemini API key is required. "
                "Set GEMINI_API_KEY environment variable."
            )

        self.config = config
        self.client = genai.Client(api_key=config.api_key)

        # Cache (in-memory, 5min TTL)
        self.cache: Dict[str, tuple[Dict[str, Any], float]] = {}
        self.cache_ttl = 300  # 5 minutes

        # Budget tracking
        self.monthly_budget = config.monthly_budget_usd  # from config
        self.session_cost = 0.0
        self.total_requests = 0

        # Model pricing (per 1M tokens)
        self.pricing = {
            "input_base": 2.00,    # ≤200K tokens
            "output_base": 12.00,
            "input_long": 4.00,    # >200K tokens
            "output_long": 18.00
        }

        logger.info(
            "gemini_client_initialized",
            extra={
                "model": config.model,
                "budget_usd": self.monthly_budget,
                "cache_enabled": True
            }
        )

    async def generate_plan(
        self,
        system_state: Dict[str, Any],
        operational_goals: Dict[str, Any],
        available_actions: List[Dict[str, Any]],
        force_thinking_level: Optional[ThinkingLevel] = None
    ) -> Dict[str, Any]:
        """
        Generate infrastructure plan with adaptive thinking.

        Args:
            system_state: Current system metrics
            operational_goals: Desired outcomes
            available_actions: Available actions
            force_thinking_level: Override auto-detection

        Returns:
            Plan dictionary with:
                - thought_trace (str): Reasoning steps
                - reasoning (str): Decision summary
                - plan_id (str): Unique identifier
                - actions (list): Recommended actions
                - metadata (dict): Cost, latency, thinking_level

        Raises:
            GeminiQuotaError: If budget exceeded
            GeminiAPIError: On API errors
        """
        # Check cache first
        cache_key = self._get_cache_key(system_state, operational_goals)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.info("cache_hit", extra={"cache_key": cache_key[:16]})
            return cached

        # Determine thinking level
        if force_thinking_level:
            thinking_level = force_thinking_level
        else:
            thinking_level = self._determine_thinking_level(
                system_state,
                operational_goals,
                available_actions
            )

        # Build prompt
        prompt = self._build_prompt(
            system_state,
            operational_goals,
            available_actions
        )

        # Generate with retries
        start_time = time.time()

        for attempt in range(3):  # 3 retries
            try:
                response = await self._call_gemini(prompt, thinking_level)
                plan = self._parse_response(response)

                # Calculate cost
                cost = self._estimate_cost(prompt, plan, thinking_level)
                self.session_cost += cost
                self.total_requests += 1

                latency = time.time() - start_time

                # Add metadata
                plan["metadata"] = {
                    "thinking_level": thinking_level.value,
                    "cost_usd": round(cost, 6),
                    "latency_ms": round(latency * 1000, 2),
                    "attempt": attempt + 1
                }

                # Cache result
                self._add_to_cache(cache_key, plan)

                logger.info(
                    "plan_generated",
                    extra={
                        "thinking_level": thinking_level.value,
                        "cost_usd": cost,
                        "latency_ms": latency * 1000,
                        "actions": len(plan.get("actions", []))
                    }
                )

                return plan

            except Exception as e:
                if attempt < 2:  # Retry
                    wait = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        "request_retry",
                        extra={"attempt": attempt + 1, "wait_s": wait, "error": str(e)}
                    )
                    await self._async_sleep(wait)
                else:
                    logger.error("request_failed", extra={"error": str(e)})
                    raise GeminiAPIError(f"Failed after 3 attempts: {e}") from e

        raise GeminiAPIError("Unreachable code")

    def _determine_thinking_level(
        self,
        system_state: Dict[str, Any],
        operational_goals: Dict[str, Any],
        available_actions: List[Dict[str, Any]]
    ) -> ThinkingLevel:
        """
        Auto-detect thinking level based on complexity.

        Heuristics:
        - HIGH: Many actions (>5), complex goals, critical state
        - LOW: Few actions (≤5), simple goals, normal state

        Args:
            system_state: Current state
            operational_goals: Goals
            available_actions: Actions

        Returns:
            Thinking level (LOW or HIGH)
        """
        complexity_score = 0

        # Factor 1: Number of available actions
        if len(available_actions) > 5:
            complexity_score += 2
        elif len(available_actions) > 3:
            complexity_score += 1

        # Factor 2: Goal complexity (count nested keys)
        goal_depth = self._get_dict_depth(operational_goals)
        if goal_depth > 2:
            complexity_score += 2

        # Factor 3: State criticality (detect anomalies)
        if any(
            key in str(system_state).lower()
            for key in ["error", "failure", "critical", "down"]
        ):
            complexity_score += 3  # Critical = use deep thinking

        # Decision: HIGH if score ≥ 3
        thinking_level = ThinkingLevel.HIGH if complexity_score >= 3 else ThinkingLevel.LOW

        logger.debug(
            "thinking_level_determined",
            extra={
                "level": thinking_level.value,
                "complexity_score": complexity_score
            }
        )

        return thinking_level

    def _build_prompt(
        self,
        system_state: Dict[str, Any],
        operational_goals: Dict[str, Any],
        available_actions: List[Dict[str, Any]]
    ) -> str:
        """Build structured prompt for Gemini 3 Pro."""
        return f"""<system_context>
You are the HCL (Homeostatic Control Loop) Agentic Planner for Maximus 2.0.
You have Gemini 3 Pro's deep reasoning capabilities.
</system_context>

<task>
Analyze the system state and goals. Generate a robust infrastructure plan.
Use your thinking mode to simulate outcomes before committing to actions.
</task>

<current_state>
{json.dumps(system_state, indent=2)}
</current_state>

<operational_goals>
{json.dumps(operational_goals, indent=2)}
</operational_goals>

<available_actions>
{json.dumps(available_actions, indent=2)}
</available_actions>

<output_format>
Return JSON:
{{
    "thought_trace": "Step 1: Analyzed...",
    "reasoning": "Final decision summary",
    "plan_id": "unique-id",
    "actions": [...]
}}
</output_format>"""

    async def _call_gemini(
        self,
        prompt: str,
        thinking_level: ThinkingLevel
    ) -> types.GenerateContentResponse:
        """
        Call Gemini 3 Pro API.

        Args:
            prompt: Formatted prompt
            thinking_level: Thinking level

        Returns:
            API response

        Raises:
            GeminiQuotaError: If over budget
        """
        # Budget check
        if self.session_cost >= self.monthly_budget:
            raise GeminiQuotaError(
                f"Monthly budget ${self.monthly_budget} exceeded. "
                f"Current: ${self.session_cost:.2f}"
            )

        response = self.client.models.generate_content(
            model=self.config.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_level=thinking_level.value,
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
                response_mime_type="application/json"
            )
        )

        return response

    def _parse_response(
        self,
        response: types.GenerateContentResponse
    ) -> Dict[str, Any]:
        """Parse Gemini response to plan dict."""
        text = response.text

        # Handle markdown if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        return cast(Dict[str, Any], json.loads(text))

    def _estimate_cost(
        self,
        prompt: str,
        plan: Dict[str, Any],
        thinking_level: ThinkingLevel
    ) -> float:
        """
        Estimate API cost.

        Args:
            prompt: Input prompt
            plan: Output plan
            thinking_level: Thinking level used

        Returns:
            Estimated cost in USD
        """
        # Rough estimation (4 chars/token)
        input_tokens = len(prompt) / 4
        output_tokens = len(json.dumps(plan)) / 4

        # Thinking tokens (HIGH = 2x output, LOW = 0)
        if thinking_level == ThinkingLevel.HIGH:
            output_tokens *= 2  # Rough estimate

        # Pricing (assume ≤200K context)
        cost = (
            (input_tokens * self.pricing["input_base"] / 1_000_000) +
            (output_tokens * self.pricing["output_base"] / 1_000_000)
        )

        return cost

    def _get_cache_key(
        self,
        system_state: Dict[str, Any],
        operational_goals: Dict[str, Any]
    ) -> str:
        """Generate cache key from inputs."""
        data = json.dumps(
            {
                "state": system_state,
                "goals": operational_goals
            },
            sort_keys=True
        )
        return hashlib.md5(data.encode()).hexdigest()

    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if not expired."""
        if key in self.cache:
            plan, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return plan
            else:
                del self.cache[key]  # Expired
        return None

    def _add_to_cache(self, key: str, plan: Dict[str, Any]) -> None:
        """Add response to cache."""
        self.cache[key] = (plan, time.time())

    @staticmethod
    def _get_dict_depth(d: Dict[str, Any], level: int = 0) -> int:
        """Calculate max depth of nested dict."""
        if not isinstance(d, dict) or not d:
            return level
        return max(
            GeminiClient._get_dict_depth(v, level + 1)
            for v in d.values()
        )

    @staticmethod
    async def _async_sleep(seconds: float) -> None:
        """Async sleep helper."""
        import asyncio
        await asyncio.sleep(seconds)

    def get_session_cost(self) -> float:
        """Get total cost for current session."""
        return self.session_cost

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "total_requests": self.total_requests,
            "session_cost_usd": round(self.session_cost, 4),
            "budget_remaining_usd": round(self.monthly_budget - self.session_cost, 2),
            "cache_size": len(self.cache),
            "budget_used_pct": round((self.session_cost / self.monthly_budget) * 100, 2)
        }
