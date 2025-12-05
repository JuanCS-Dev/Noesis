"""
Digital Thalamus (Attention Firewall)
=====================================
Acts as the cognitive gatekeeper for the Digital Daimon.
Filters incoming stimuli based on the user's current attention status and
the stimulus's urgency/dopaminergic profile.
"""

import logging
import json
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from services.maximus_core_service.utils.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class AttentionStatus(Enum):
    """Estado de atenção do usuário."""
    FOCUS = "FOCUS"       # Bloqueio total de distrações
    FLOW = "FLOW"         # Bloqueio alto, permite crítico
    RESTING = "RESTING"   # Permite social/lazer
    NEUTRAL = "NEUTRAL"   # Padrão, filtro moderado

class StimulusType(Enum):
    """Tipo do estímulo recebido."""
    NOTIFICATION = "NOTIFICATION"
    MESSAGE = "MESSAGE"
    ADVERTISEMENT = "ADVERTISEMENT"
    SYSTEM_ALERT = "SYSTEM_ALERT"
    CONTENT_SUGGESTION = "CONTENT_SUGGESTION"

@dataclass
class Stimulus:
    """Representa um estímulo externo entrando na consciência."""
    id: str
    type: StimulusType
    source: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ThalamusDecision:
    """Decisão tomada pelo Tálamo."""
    action: str  # ALLOW, BLOCK, BATCH
    reasoning: str
    dopamine_score: float # 0.0 a 1.0 (Estimativa de vício/distração)
    urgency_score: float  # 0.0 a 1.0

class DigitalThalamus:
    """
    O Porteiro da Atenção.
    Avalia se um estímulo deve chegar à consciência do usuário.
    """

    def __init__(self, gemini_client: GeminiClient, workspace: Any = None):
        self.client = gemini_client
        self.workspace = workspace

    async def ingest(self, stimulus: Stimulus, current_status: AttentionStatus) -> ThalamusDecision:
        """EntryPoint público para processar estímulo (Alias para filter)."""
        return await self.filter_stimulus(stimulus, current_status)

    async def filter_stimulus(
        self,
        stimulus: Stimulus,
        current_status: AttentionStatus
    ) -> ThalamusDecision:
        """
        Filtra um estímulo baseado no estado atual.
        Usa LLM para análise semântica de urgência e valência.
        """
        decision: Optional[ThalamusDecision] = None

        # 1. Hard Rules (Circuit Breakers)
        if current_status == AttentionStatus.FOCUS and stimulus.type == StimulusType.ADVERTISEMENT:
            decision = ThalamusDecision(
                action="BLOCK",
                reasoning="Absolute block of ads during FOCUS mode.",
                dopamine_score=0.9,
                urgency_score=0.0
            )

        # 2. If not decided by Hard Rules, proceed to Analysis
        if decision is None:
            # Semantic Analysis via Gemini
            analysis = await self._analyze_stimulus(stimulus)

            # Decision Logic based on Scores & State
            decision = await self._make_descision(analysis, current_status)

        # Logar a decisão para auditoria
        logger.info(
            "Stimulus Filtered: ID=%s, Type=%s, Source=%s, Decision=%s, "
            "Reasoning=%s, Urgency=%.2f, Dopamine=%.2f",
            stimulus.id,
            stimulus.type.value,
            stimulus.source,
            decision.action,
            decision.reasoning,
            decision.urgency_score,
            decision.dopamine_score,
        )

        # Broadcast via Global Workspace (se disponível)
        if self.workspace:
            await self._broadcast_decision(stimulus, decision)

        return decision

    async def _analyze_stimulus(self, stimulus: Stimulus) -> Dict[str, Any]:
        """Usa Gemini para pontuar o estímulo."""
        prompt = f"""
        Act as a Cognitive Filter. Analyze this incoming digital stimulus:

        Type: {stimulus.type.value}
        Source: {stimulus.source}
        Content: "{stimulus.content}"

        Evaluate strictly:
        1. Urgency (0.0 to 1.0): Does this require immediate action?
        2. Dopaminergic Valence (0.0 to 1.0): Is this designed to be addictive/distracting?
        3. Relevance (0.0 to 1.0): Is this meaningful information?

        Output JSON:
        {{
            "urgency": float,
            "dopamine": float,
            "relevance": float,
            "brief_reasoning": "string"
        }}
        """

        try:
            response = await self.client.generate_text(prompt, response_schema={
                "type": "object",
                "properties": {
                    "urgency": {"type": "number"},
                    "dopamine": {"type": "number"},
                    "relevance": {"type": "number"},
                    "brief_reasoning": {"type": "string"}
                }
            })
            return json.loads(response["text"])
        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error("Thalamus analysis failed: %s", e)
            # Fallback seguro
            return {
                "urgency": 0.5, "dopamine": 0.5,
                "relevance": 0.5, "brief_reasoning": "Analysis Failed"
            }

    async def _make_descision(
        self,
        analysis: Dict[str, Any],
        status: AttentionStatus
    ) -> ThalamusDecision:
        """Aplica a lógica de decisão baseada nos scores e estado."""
        urgency = analysis.get("urgency", 0.0)
        dopamine = analysis.get("dopamine", 0.0)

        action = "ALLOW"
        reason = analysis.get("brief_reasoning", "Passed")

        if status == AttentionStatus.FOCUS:
            if urgency < 0.8:
                action = "BATCH" if urgency > 0.4 else "BLOCK"
                reason = "Focus protection: Low urgency items blocked/batched."

        elif status == AttentionStatus.FLOW:
            if urgency < 0.6:
                action = "BATCH"
                reason = "Flow protection: Non-critical items batched."

        elif status == AttentionStatus.RESTING:
            # No resting, permitimos, mas alertamos se for muito viciante
            if dopamine > 0.8:
                reason += " (Warning: High Dopamine Content)"

        return ThalamusDecision(
            action=action,
            reasoning=reason,
            dopamine_score=dopamine,
            urgency_score=urgency
        )

    async def _broadcast_decision(self, stimulus: Stimulus, decision: ThalamusDecision) -> None:
        """Transmite evento para o Global Workspace."""
        # Avoid circular dependency if any (checking runtime)
        # But safest is top level if no cycle. keeping local for now but fixing lint
        from services.maximus_core_service.src.consciousness.exocortex.global_workspace import ( # pylint: disable=import-outside-toplevel
            ConsciousEvent, EventType
        )

        event = ConsciousEvent(
            id=f"evt_{stimulus.id}",
            type=EventType.STIMULUS_FILTERED,
            source="DigitalThalamus",
            payload={
                "stimulus_id": stimulus.id,
                # Changed from decision.action.value to decision.action
                "decision": decision.action,
                "urgency": decision.urgency_score,
                "dopamine": decision.dopamine_score
            }
        )
        print(f"DEBUG: Thalamus broadcasting event via {self.workspace}")
        await self.workspace.broadcast(event)
