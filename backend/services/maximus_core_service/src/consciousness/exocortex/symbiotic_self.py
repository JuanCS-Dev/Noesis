"""
SymbioticSelfConcept - O Self que inclui Humano + Daimon
========================================================

Baseado em: Extended Mind Theory (Clark & Chalmers, 1998)
Estende: UnifiedSelfConcept do Projeto Florescimento

Padrão Pagani:
- Tipagem estrita
- Sem placeholders
- Integração com Gemini 3.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import logging
import json

from services.maximus_core_service.utils.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


@dataclass
class UnifiedSelfConcept:
    """Classe base simulada do UnifiedSelfConcept."""


class ValuePriority(Enum):
    """Prioridade de valores na hierarquia."""
    CORE = 1        # Inegociável
    IMPORTANT = 2   # Muito importante
    ASPIRATIONAL = 3  # Desejado, mas flexível


@dataclass
class HumanValue:
    """Representa um valor declarado pelo usuário."""
    name: str
    definition: str
    priority: ValuePriority
    examples_positive: List[str]
    examples_negative: List[str]
    declared_at: datetime
    last_validated: datetime


@dataclass
class HumanGoal:
    """Representa um objetivo declarado pelo usuário."""
    id: str
    description: str
    timeframe: str
    aligned_values: List[str]
    progress_indicators: List[str]
    created_at: datetime
    status: str = "active"


@dataclass
class ShadowPattern:
    """Padrão problemático identificado no usuário."""
    name: str
    description: str
    triggers: List[str]
    typical_consequences: List[str]
    times_observed: int
    last_occurrence: Optional[datetime]
    user_acknowledged: bool = False


@dataclass
class HumanIdentityModel:
    """Modelo da identidade do usuário."""
    name: str
    core_identity_statement: str
    non_negotiables: List[str]
    aspirational_self: str
    known_strengths: List[str]
    known_weaknesses: List[str]
    life_chapter_current: str


@dataclass
class DaimonPerception:
    """Como o Daimon percebe o estado atual do humano."""
    perceived_emotional_state: str
    perceived_energy_level: float
    perceived_alignment: float
    perceived_stress_level: float
    confidence_in_perception: float
    last_updated: datetime

    def to_narrative(self) -> str:
        """Converte percepção em narrativa empática."""
        narratives = []
        if self.perceived_stress_level > 0.7:
            narratives.append("Percebo tensão significativa.")
        if self.perceived_alignment < 0.5:
            narratives.append("Ações recentes parecem desalinhadas.")
        if self.perceived_energy_level < 0.3:
            narratives.append("Nível de energia parece baixo.")
        return " ".join(narratives) if narratives else "Estabilidade percebida."


@dataclass
class TrustLevel:
    """Nível de confiança na relação Humano-Daimon."""
    level: int = 1
    user_trust_in_daimon: float = 0.3
    daimon_trust_in_user_self_report: float = 0.5
    trust_building_events: int = 0
    trust_breaking_events: int = 0

    @property
    def level_name(self) -> str:
        """Retorna o nome descritivo do nível de confiança."""
        names = {
            1: "Observador", 2: "Sugestor", 3: "Questionador",
            4: "Confrontador", 5: "Guardião"
        }
        return names.get(self.level, "Desconhecido")

    def can_confront(self) -> bool:
        """Verifica se o nível permite confrontação."""
        return self.level >= 4


@dataclass
class SymbioticState:
    """Encapsula o estado dinâmico da relação simbiótica."""
    daimon_perception: Optional[DaimonPerception] = None
    trust: TrustLevel = field(default_factory=TrustLevel)
    total_interactions: int = 0
    meaningful_confrontations: int = 0
    successful_interventions: int = 0


@dataclass
class SymbioticSelfConcept(UnifiedSelfConcept): # pylint: disable=too-many-instance-attributes
    """
    Self Simbiótico que integra Humano + Daimon.
    """
    # Human Context
    human_identity: Optional[HumanIdentityModel] = None
    human_values: List[HumanValue] = field(default_factory=list)
    human_goals: List[HumanGoal] = field(default_factory=list)
    human_shadows: List[ShadowPattern] = field(default_factory=list)

    # Relationship State (Encapsulated to reduce attributes)
    state: SymbioticState = field(default_factory=SymbioticState)
    relationship_start: Optional[datetime] = None

    # Dependencies (Injected via post_init or manual assignment in factory)
    gemini_client: Optional[GeminiClient] = field(default=None, repr=False)
    workspace: Any = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.relationship_start is None:
            self.relationship_start = datetime.now()

        if self.workspace:
            self._register_subscribers()

    def set_dependencies(self, gemini_client: GeminiClient, workspace: Any) -> None:
        """Injects dependencies and starts listeners."""
        self.gemini_client = gemini_client
        self.workspace = workspace
        self._register_subscribers()

    def _register_subscribers(self) -> None:
        """Subscribes to relevant workspace events."""
        # Avoid circular import
        from services.maximus_core_service.src.consciousness.exocortex.global_workspace import ( # pylint: disable=import-outside-toplevel
            EventType
        )
        if self.workspace:
            self.workspace.subscribe(EventType.CONSTITUTION_VIOLATION, self.handle_conscious_event)
            self.workspace.subscribe(EventType.CONFRONTATION_COMPLETED, self.handle_conscious_event)
            self.workspace.subscribe(EventType.FEEDBACK_RECEIVED, self.handle_conscious_event)

    async def handle_conscious_event(self, event: Any) -> None:
        """Reacts to workspace events to update self-state."""
        if event.type.value == "CONSTITUTION_VIOLATION":
            self.state.trust.trust_breaking_events += 1
            logger.info("Trust Decreased due to Violation.")

        elif event.type.value == "CONFRONTATION_COMPLETED":
            self.state.meaningful_confrontations += 1
            self.state.trust.trust_building_events += 1
            logger.info("Trust Increased due to Confrontation.")

        elif event.type.value == "FEEDBACK_RECEIVED":
            # Update perception based on feedback
            try:
                await self.update_perception(
                    message=event.payload.get("text", ""),
                    context=event.payload
                )
            except Exception as e: # pylint: disable=broad-exception-caught
                logger.error("Failed to update perception: %s", e)

    @property
    def trust(self) -> TrustLevel:
        """Access trust level directly."""
        return self.state.trust

    @property
    def daimon_perception(self) -> Optional[DaimonPerception]:
        """Access perception directly."""
        return self.state.daimon_perception

    @daimon_perception.setter
    def daimon_perception(self, value: Optional[DaimonPerception]) -> None:
        """Set perception."""
        self.state.daimon_perception = value

    async def update_perception(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> DaimonPerception:
        """
        Atualiza a percepção do Daimon usando Gemini.

        Args:
            message: Mensagem do usuário.
            context: Contexto da mensagem.

        Returns:
            DaimonPerception: Percepção atualizada.
        """
        if not self.gemini_client:
            logger.warning("Gemini Client not available for Perception. Using default.")
            return DaimonPerception("UNKNOWN", 0.5, 0.5, 0.5, 0.0, datetime.now())

        self.state.total_interactions += 1

        prompt = f"""
        Analyze the user's state based on this message and context.
        Message: "{message}"
        Context: {context}

        Return JSON compatible with DaimonPerception:
        {{
            "perceived_emotional_state": "str (e.g., Anxious, Calm)",
            "perceived_energy_level": float (0.0-1.0),
            "perceived_alignment": float (0.0-1.0),
            "perceived_stress_level": float (0.0-1.0),
            "confidence_in_perception": float (0.0-1.0)
        }}
        """

        try:
            response = await self.gemini_client.generate_text(
                prompt=prompt,
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "perceived_emotional_state": {"type": "STRING"},
                        "perceived_energy_level": {"type": "NUMBER"},
                        "perceived_alignment": {"type": "NUMBER"},
                        "perceived_stress_level": {"type": "NUMBER"},
                        "confidence_in_perception": {"type": "NUMBER"}
                    }
                }
            )
            data = json.loads(response.get("text", "{}"))

            perception = DaimonPerception(
                perceived_emotional_state=data.get("perceived_emotional_state", "UNKNOWN"),
                perceived_energy_level=data.get("perceived_energy_level", 0.5),
                perceived_alignment=data.get("perceived_alignment", 0.5),
                perceived_stress_level=data.get("perceived_stress_level", 0.5),
                confidence_in_perception=data.get("confidence_in_perception", 0.5),
                last_updated=datetime.now()
            )

            self.state.daimon_perception = perception

            # Broadcast update
            if self.workspace:
                # pylint: disable=import-outside-toplevel
                from services.maximus_core_service.src.consciousness.exocortex \
                    .global_workspace import ConsciousEvent, EventType
                await self.workspace.broadcast(ConsciousEvent(
                    id=f"perc_{int(datetime.now().timestamp())}",
                    type=EventType.SELF_UPDATED,
                    source="SymbioticSelf",
                    payload={"new_perception": data}
                ))

            logger.info("Daimon Perception Updated: %s", perception.perceived_emotional_state)
            return perception

        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error("Error analyzing perception: %s", e)
            # Fallback
            return self.state.daimon_perception or DaimonPerception(
                "ERROR", 0.5, 0.5, 0.5, 0.0, datetime.now()
            )

    def detect_value_conflict(
        self,
        intended_action: str
    ) -> Optional[Dict[str, Any]]:
        """Detecta conflito de valores (simulado)."""
        for value in self.human_values:
            for negative in value.examples_negative:
                if negative.lower() in intended_action.lower():
                    return {
                        "conflicting_value": value.name,
                        "definition": value.definition,
                        "priority": value.priority.name
                    }
        return None

    def generate_symbiotic_report(self) -> str:
        """Gera relatório do estado simbiótico."""
        perception = (
            self.state.daimon_perception.to_narrative()
            if self.state.daimon_perception else "Ainda aprendendo."
        )
        identity = (
            self.human_identity.core_identity_statement
            if self.human_identity else "Indefinido"
        )

        return (
            f"=== RELATÓRIO ===\n"
            f"Identidade: {identity}\n"
            f"Percepção: {perception}\n"
            f"Confiança: {self.state.trust.level_name}\n"
        )
