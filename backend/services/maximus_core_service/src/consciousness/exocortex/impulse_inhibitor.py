"""
Impulse Inhibitor
=================
Detects and pauses high-risk, impulsive actions.
Acts as a cognitive braking system.
"""

import logging
import json
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

from services.maximus_core_service.utils.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class ImpulseType(Enum):
    """Categoria do impulso detectado."""
    RAGE_REPLY = "RAGE_REPLY"           # Resposta rápida com raiva
    IMPULSE_BUY = "IMPULSE_BUY"         # Compra não planejada
    DOOM_SCROLLING_INIT = "DOOM_SCROLLING_INIT" # Início de rolagem infinita
    GENERIC_RISK = "GENERIC_RISK"       # Ação arriscada genérica

class InterventionLevel(Enum):
    """Nível de intervenção necessário."""
    NONE = "NONE"             # Sem intervenção
    NOTICE = "NOTICE"         # Apenas notificar (log)
    PAUSE = "PAUSE"           # Pausa socrática obrigatória
    LOCKOUT = "LOCKOUT"       # Bloqueio temporário (Raro)

@dataclass
class ImpulseContext:
    """Contexto da ação para análise."""
    action_type: str        # ex: "send_email", "click_buy"
    content: str            # O conteúdo da ação
    user_state: str         # Estado emocional estimado
    platform: str           # ex: "twitter", "amazon"

@dataclass
class Intervention:
    """Decisão do inibidor."""
    level: InterventionLevel
    reasoning: str
    wait_time_seconds: int = 0
    socratic_question: Optional[str] = None

class ImpulseInhibitor:
    """
    Sistema de Frenagem Cognitiva.
    Analisa a 'velocidade' e o 'risco' de uma ação antes de ela ser executada.
    """

    def __init__(self, gemini_client: GeminiClient, workspace: Any = None):
        self.client = gemini_client
        self.workspace = workspace

    async def check_impulse(self, context: ImpulseContext) -> Intervention:
        """
        Avalia se a ação reflete um impulso perigoso.
        Retorna o nível de intervenção necessário.
        """
        # Análise Rápida via LLM
        analysis = await self._analyze_risk(context)

        intervention = self._decide_intervention(analysis)

        if self.workspace and intervention.level in [
            InterventionLevel.PAUSE, InterventionLevel.LOCKOUT
        ]:
            await self._broadcast_impulse(context, intervention, analysis)

        return intervention

    async def _broadcast_impulse(
        self,
        ctx: ImpulseContext,
        intervention: Intervention,
        analysis: Dict[str, Any]
    ) -> None:
        """Transmite evento de impulso detectado."""
        from services.maximus_core_service.src.consciousness.exocortex.global_workspace import ( # pylint: disable=import-outside-toplevel
            ConsciousEvent, EventType
        )

        event = ConsciousEvent(
            id=f"evt_imp_{int(datetime.now().timestamp())}",
            type=EventType.IMPULSE_DETECTED,
            source="ImpulseInhibitor",
            payload={
                "level": intervention.level.value,
                "impulse_type": analysis.get("detected_impulse", "UNKNOWN"),
                "user_state": ctx.user_state,
                "reasoning": intervention.reasoning,
                "action": ctx.action_type
            }
        )
        await self.workspace.broadcast(event)

    async def _analyze_risk(self, ctx: ImpulseContext) -> Dict[str, Any]:
        """Usa Gemini para estimar risco emocional e financeiro."""
        prompt = f"""
        Analyze this user action for IMPULSIVITY and RISK.

        Action: {ctx.action_type}
        Platform: {ctx.platform}
        User State: {ctx.user_state}
        Content Snippet: "{ctx.content[:500]}"

        Evaluate:
        1. Emotional Intensity (0.0 - 1.0): Anger/Fear/Excitement level.
        2. Irreversibility (0.0 - 1.0): How hard is it to undo?
        3. Constitutional Alignment (0.0 - 1.0): 1.0 = Aligned, 0.0 = Violation.

        Return JSON under 'analysis':
        {{
            "emotional_intensity": float,
            "irreversibility": float,
            "alignment": float,
            "detected_impulse": "RAGE_REPLY | IMPULSE_BUY | NONE",
            "reasoning": "brief string"
        }}
        """

        try:
            response = await self.client.generate_text(prompt, response_schema={
                "type": "object",
                "properties": {
                    "emotional_intensity": {"type": "number"},
                    "irreversibility": {"type": "number"},
                    "alignment": {"type": "number"},
                    "detected_impulse": {"type": "string"},
                    "reasoning": {"type": "string"}
                }
            })
            return json.loads(response["text"])
        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error("Inhibitor analysis failed: %s", e)
            # Fail safe: No intervention if error
            return {
                "emotional_intensity": 0.0,
                "irreversibility": 0.0,
                "alignment": 1.0,
                "detected_impulse": "NONE",
                "reasoning": "Analysis Failed"
            }

    def _decide_intervention(self, analysis: Dict[str, Any]) -> Intervention:
        """Decide o nível de intervenção com base na análise."""
        emotion = analysis.get("emotional_intensity", 0.0)
        risk = analysis.get("irreversibility", 0.0)
        alignment = analysis.get("alignment", 1.0)
        impulse = analysis.get("detected_impulse", "NONE")

        reason = analysis.get("reasoning", "")

        # RAGE REPLY
        if impulse == "RAGE_REPLY" or (emotion > 0.8 and risk > 0.5):
            return Intervention(
                level=InterventionLevel.PAUSE,
                reasoning=f"High emotional intensity detected ({emotion:.1f}). {reason}",
                wait_time_seconds=30,
                socratic_question="Essa resposta servirá ao seu 'Eu' de amanhã?"
            )

        # IMPULSE BUY
        if impulse == "IMPULSE_BUY":
            return Intervention(
                level=InterventionLevel.PAUSE,
                reasoning=f"Potential impulse buy detected. {reason}",
                wait_time_seconds=60,
                socratic_question="Isso é uma necessidade ou um desejo momentâneo?"
            )

        # LOW ALIGNMENT RISK
        if alignment < 0.4:
            return Intervention(
                level=InterventionLevel.NOTICE,
                reasoning="Action seems misaligned with constitution.",
                wait_time_seconds=0
            )

        return Intervention(level=InterventionLevel.NONE, reasoning="Safe.")

    async def get_status(self) -> Dict[str, Any]:
        """Retorna status do inibidor (mock)."""
        return {"active": True, "interventions_count": 0}
