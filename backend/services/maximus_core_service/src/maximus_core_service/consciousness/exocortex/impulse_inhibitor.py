"""
Impulse Inhibitor
=================
Detects and pauses high-risk, impulsive actions.
Acts as a cognitive braking system.

NOESIS Soul Integration:
- Receives bias catalog from ExocortexFactory
- Uses biases in detection prompts
- Provides bias-aware socratic questions
"""

import logging
import json
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime

from maximus_core_service.utils.gemini_client import GeminiClient

if TYPE_CHECKING:
    from maximus_core_service.consciousness.exocortex.soul.models import BiasEntry

logger = logging.getLogger(__name__)

class ImpulseType(Enum):
    """Categoria do impulso detectado."""
    RAGE_REPLY = "RAGE_REPLY"           # Resposta rápida com raiva
    IMPULSE_BUY = "IMPULSE_BUY"         # Compra não planejada
    DOOM_SCROLLING_INIT = "DOOM_SCROLLING_INIT" # Início de rolagem infinita
    GENERIC_RISK = "GENERIC_RISK"       # Ação arriscada genérica
    COGNITIVE_BIAS = "COGNITIVE_BIAS"   # Bias detected (NOESIS)

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
    
    NOESIS Integration:
    - Uses bias catalog for enhanced detection
    - Provides bias-specific socratic questions
    """

    def __init__(self, gemini_client: GeminiClient, workspace: Any = None):
        self.client = gemini_client
        self.workspace = workspace
        # NOESIS: Bias catalog (injected via inject_biases)
        self.bias_catalog: Dict[str, "BiasEntry"] = {}
        self._biases_injected: bool = False

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
        from maximus_core_service.consciousness.exocortex.global_workspace import ( # pylint: disable=import-outside-toplevel
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
        # Build bias catalog section for prompt
        bias_section = self._build_bias_prompt_section()
        
        prompt = f"""
        Analyze this user action for IMPULSIVITY, RISK, and COGNITIVE BIASES.

        Action: {ctx.action_type}
        Platform: {ctx.platform}
        User State: {ctx.user_state}
        Content Snippet: "{ctx.content[:500]}"

        {bias_section}

        Evaluate:
        1. Emotional Intensity (0.0 - 1.0): Anger/Fear/Excitement level.
        2. Irreversibility (0.0 - 1.0): How hard is it to undo?
        3. Constitutional Alignment (0.0 - 1.0): 1.0 = Aligned, 0.0 = Violation.
        4. Detected Biases: Check against the bias catalog above.

        Return JSON:
        {{
            "emotional_intensity": float,
            "irreversibility": float,
            "alignment": float,
            "detected_impulse": "RAGE_REPLY | IMPULSE_BUY | COGNITIVE_BIAS | NONE",
            "detected_bias_ids": ["bias_id1", "bias_id2"],
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
                    "detected_bias_ids": {"type": "array", "items": {"type": "string"}},
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
                "detected_bias_ids": [],
                "reasoning": "Analysis Failed"
            }

    def _build_bias_prompt_section(self) -> str:
        """Build the bias catalog section for the analysis prompt."""
        if not self.bias_catalog:
            return "[No bias catalog loaded]"
        
        lines = ["[COGNITIVE BIAS CATALOG - Detect if any apply]"]
        for bias_id, bias in self.bias_catalog.items():
            triggers_str = ", ".join(bias.triggers) if bias.triggers else "various"
            lines.append(f"  - {bias_id}: {bias.name} - Triggers: {triggers_str}")
        
        return "\n".join(lines)

    def _decide_intervention(self, analysis: Dict[str, Any]) -> Intervention:
        """Decide o nível de intervenção com base na análise."""
        emotion = analysis.get("emotional_intensity", 0.0)
        risk = analysis.get("irreversibility", 0.0)
        alignment = analysis.get("alignment", 1.0)
        impulse = analysis.get("detected_impulse", "NONE")
        detected_biases = analysis.get("detected_bias_ids", [])

        reason = analysis.get("reasoning", "")

        # COGNITIVE BIAS DETECTED (NOESIS)
        if impulse == "COGNITIVE_BIAS" or detected_biases:
            question = self._get_bias_intervention_question(detected_biases)
            bias_names = ", ".join(
                self.bias_catalog[b].name 
                for b in detected_biases 
                if b in self.bias_catalog
            ) or "viés não catalogado"
            
            return Intervention(
                level=InterventionLevel.PAUSE,
                reasoning=f"Viés cognitivo detectado: {bias_names}. {reason}",
                wait_time_seconds=15,
                socratic_question=question
            )

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

    def _get_bias_intervention_question(self, bias_ids: List[str]) -> str:
        """Get the socratic intervention question for detected biases."""
        if not bias_ids:
            return "Você está certo dessa análise?"
        
        # Use the first detected bias's intervention
        first_bias_id = bias_ids[0]
        if first_bias_id in self.bias_catalog:
            return self.bias_catalog[first_bias_id].intervention
        
        return "Você considerou todas as perspectivas?"

    async def get_status(self) -> Dict[str, Any]:
        """Retorna status do inibidor."""
        return {
            "active": True, 
            "interventions_count": 0,
            "biases_loaded": len(self.bias_catalog),
            "biases_injected": self._biases_injected
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # NOESIS SOUL INTEGRATION
    # ═══════════════════════════════════════════════════════════════════════════

    def inject_biases(self, biases: List["BiasEntry"]) -> None:
        """
        Inject NOESIS bias catalog into the impulse inhibitor.
        
        Enables bias-aware detection and intervention using the
        catalog from soul_config.yaml.
        
        Args:
            biases: List of BiasEntry from soul configuration
        """
        logger.info("🧠 Injecting NOESIS bias catalog into ImpulseInhibitor...")
        
        self.bias_catalog = {bias.id: bias for bias in biases}
        self._biases_injected = True
        
        # Log summary by category
        categories = {}
        for bias in biases:
            cat = bias.category.value if hasattr(bias.category, 'value') else str(bias.category)
            categories[cat] = categories.get(cat, 0) + 1
        
        logger.info(
            "✅ Bias catalog loaded: %d biases (%s)",
            len(self.bias_catalog),
            ", ".join(f"{k}:{v}" for k, v in categories.items())
        )

    def get_bias_for_prompt(self) -> str:
        """
        Generate a formatted bias catalog for LLM prompts.
        
        Returns:
            Formatted bias catalog string for context injection.
        """
        if not self.bias_catalog:
            return "[No bias catalog]"
        
        lines = ["[NOESIS COGNITIVE BIAS CATALOG]"]
        for bias_id, bias in self.bias_catalog.items():
            lines.append(
                f"  {bias.name} ({bias_id}): {bias.description}\n"
                f"    → Intervention: {bias.intervention}"
            )
        
        return "\n".join(lines)
