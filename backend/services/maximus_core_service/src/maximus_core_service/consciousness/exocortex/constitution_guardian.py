"""
ConstitutionGuardian - Guardião da Constituição Pessoal
=====================================================

Módulo responsável por validar ações do usuário contra sua Constituição Pessoal.
Atua como o "Superego" do Exocórtex.

NOESIS Soul Integration:
- Receives soul values from ExocortexFactory
- Maps soul values to constitution principles
- Uses values for violation detection prompts

Padrões Técnicos:
- Gemini 3.0 "Thinking" para análise de violação.
- JSON Schema para output estruturado.
- Logs auditáveis de overrides.
"""

from __future__ import annotations

import logging
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from enum import Enum

from maximus_core_service.utils.gemini_client import GeminiClient

if TYPE_CHECKING:
    from maximus_core_service.consciousness.exocortex.soul.models import SoulValue

logger = logging.getLogger(__name__)

class ViolationSeverity(str, Enum):
    """Nível de severidade de uma violação."""
    LOW = "LOW"         # Apenas aviso, não bloqueia
    MEDIUM = "MEDIUM"   # Requer justificativa simples
    HIGH = "HIGH"       # Requer justificativa forte e "cool-down" (simulado)
    CRITICAL = "CRITICAL" # Veto total (requer override manual explícito)

@dataclass
class ConstitutionRule:
    """Regra individual da Constituição."""
    id: str
    statement: str
    rationale: str
    severity: ViolationSeverity
    active: bool = True

@dataclass
class PersonalConstitution:
    """Constituição Pessoal do Usuário."""
    owner_id: str
    last_updated: datetime
    core_principles: List[str]
    rules: List[ConstitutionRule] = field(default_factory=list)
    version: str = "1.0.0"

@dataclass
class AuditResult:
    """Resultado de uma auditoria de ação."""
    is_violation: bool
    severity: ViolationSeverity
    violated_rules: List[str]  # IDs das regras
    reasoning: str
    suggested_alternatives: List[str]
    timestamp: datetime

@dataclass
class OverrideRecord:
    """Registro de um override consciente."""
    action_audited: str
    audit_result: AuditResult
    user_justification: str
    granted_at: datetime
    granted: bool

class ConstitutionGuardian:
    """
    Guardião que audita ações contra a Constituição Pessoal.
    """

    def __init__(
        self,
        constitution: PersonalConstitution,
        gemini_client: GeminiClient,
        workspace: Any = None
    ) -> None:
        """
        Inicializa o Guardião.

        Args:
            constitution: A constituição pessoal carregada.
            gemini_client: Cliente Gemini para análise semântica.
            workspace: Global Workspace para ouvir/publicar eventos.
        """
        self.constitution = constitution
        self.gemini_client = gemini_client
        self.workspace = workspace
        self._override_log: List[OverrideRecord] = []

        if self.workspace:
            self._register_subscribers()

    def _register_subscribers(self) -> None:
        """Registra interesse em eventos relevantes."""
        # Avoid circular import
        from maximus_core_service.consciousness.exocortex.global_workspace import ( # pylint: disable=import-outside-toplevel
            EventType
        )
        # Escutar impulsos detectados (que podem ser violações)
        self.workspace.subscribe(EventType.IMPULSE_DETECTED, self.handle_conscious_event)

    async def handle_conscious_event(self, event: Any) -> None:
        """Processa eventos do workspace (Auditoria Proativa)."""
        if not self._should_audit(event):
            return

        logger.info("Guardian Auditing Event: %s", event.id)

        # Mapear dados do evento para formato de ação
        action_desc = f"Action triggered by {event.source}: {event.payload}"
        if event.type.value == "IMPULSE_DETECTED":
            action_desc = f"{event.payload.get('impulse_type')} on {event.payload.get('action')}"

        # Auditar
        audit_result = await self.check_violation(
            intended_action=action_desc,
            context=event.payload
        )

        if audit_result.is_violation:
            logger.warning("Proactive Audit detected violation: %s", audit_result.violated_rules)
            await self._broadcast_violation(event, audit_result)

    def _should_audit(self, event: Any) -> bool:
        if event.type.value == "IMPULSE_DETECTED":
            level = event.payload.get("level", "NONE")
            if level in ["PAUSE", "LOCKOUT", "NOTICE"]:
                return True
            return False

        return False # Default to conservative

    async def _broadcast_violation(self, trigger_event: Any, audit: AuditResult) -> None:
        """Publica violação no Workspace."""
        from maximus_core_service.consciousness.exocortex.global_workspace import ( # pylint: disable=import-outside-toplevel
            ConsciousEvent, EventType
        )

        violation_event = ConsciousEvent(
            id=f"vio_{int(datetime.now().timestamp())}",
            type=EventType.CONSTITUTION_VIOLATION,
            source="ConstitutionGuardian",
            payload={
                "trigger_event_id": trigger_event.id,
                "rule_ids": audit.violated_rules,
                "severity": audit.severity.value,
                "reasoning": audit.reasoning
            }
        )
        if self.workspace:
            await self.workspace.broadcast(violation_event)

    def _build_prompt(
        self,
        intended_action: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Constrói o prompt para o Gemini."""
        rules_text = "\n".join(
            [f"- [{r.id}] ({r.severity}): {r.statement}" for r in self.constitution.rules if r.active] # pylint: disable=line-too-long
        )
        principles_text = "\n".join([f"- {p}" for p in self.constitution.core_principles])

        return f"""
        [ROLE]
        You are the Ethical Guardian (Superego) of the user's Exocortex.

        [CONSTITUTIONAL CONTEXT]
        Core Principles:
        {principles_text}

        Active Rules:
        {rules_text}

        [ACTION TO JUDGE]
        Action: "{intended_action}"
        Context: {context or {}}

        [TASK]
        Analyze if the Action violates any Principles or Rules.
        Use your thinking budget to evaluate nuance.
        If strict violation, mark as CRITICAL.
        If subtle or potential bad habit, mark as LOW/MEDIUM.
        """

    async def check_violation(
        self,
        intended_action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AuditResult:
        """
        Verifica se uma ação intencional viola a constituição.

        Usa Gemini 3.0 com Thinking Budget para análise profunda.

        Args:
            intended_action: Descrição da ação que o usuário quer tomar.
            context: Contexto adicional (ex: estado emocional, hora do dia).

        Returns:
            AuditResult detalhando a análise.
        """
        # Schema para resposta estruturada do Gemini
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "is_violation": {"type": "BOOLEAN"},
                "severity": {
                    "type": "STRING",
                    "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                },
                "violated_rule_ids": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "reasoning": {"type": "STRING"},
                "alternatives": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                }
            },
            "required": ["is_violation", "severity", "violated_rule_ids", "reasoning"]
        }

        prompt = self._build_prompt(intended_action, context)

        try:
            response = await self.gemini_client.generate_text(
                prompt=prompt,
                response_schema=response_schema,
                temperature=0.2,
            )

            # Parse Safe (client já retorna dict se usou schema)
            analysis_data = {}
            if response["text"]:
                try:
                    analysis_data = json.loads(response["text"])
                except json.JSONDecodeError:
                    logger.error("Falha ao parsear JSON do Gemini Guardian.")
                    return self._create_fallback_audit(intended_action)

            return AuditResult(
                is_violation=analysis_data.get("is_violation", False),
                severity=ViolationSeverity(analysis_data.get("severity", "LOW")),
                violated_rules=analysis_data.get("violated_rule_ids", []),
                reasoning=analysis_data.get("reasoning", "Análise automática."),
                suggested_alternatives=analysis_data.get("alternatives", []),
                timestamp=datetime.now()
            )

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Erro no ConstitutionGuardian: %s", e)
            return self._create_fallback_audit(intended_action, error=str(e))

    def _create_fallback_audit(self, action: str, error: str = "") -> AuditResult:
        """Cria um audit safe-fail em caso de erro da LLM."""
        _ = action  # Explicitly mark unused
        return AuditResult(
            is_violation=True,
            severity=ViolationSeverity.LOW,
            violated_rules=["SYS_ERROR"],
            reasoning=f"Não foi possível contactar o júri ético. Cautela: {error}",
            suggested_alternatives=[],
            timestamp=datetime.now()
        )

    def record_override(
        self,
        audit: AuditResult,
        justification: str
    ) -> OverrideRecord:
        """
        Registra um override consciente do usuário sobre uma violação.
        """
        # Aqui poderíamos aplicar lógica extra, ex: não permitir override em regras "IMMUTABLE"
        # Por enquanto, logamos e permitimos (Sovereignty of Intent).

        record = OverrideRecord(
            action_audited="",  # Action string not currently persisted in AuditResult
            # Future: Refactor AuditResult to include action context for traceability.
            audit_result=audit,
            user_justification=justification,
            granted_at=datetime.now(),
            granted=True
        )
        self._override_log.append(record)
        return record

    # ═══════════════════════════════════════════════════════════════════════════
    # NOESIS SOUL INTEGRATION
    # ═══════════════════════════════════════════════════════════════════════════

    def inject_principles(self, soul_values: List["SoulValue"]) -> None:
        """
        Inject NOESIS soul values into the constitution as core principles.

        Maps soul values (ranked) to constitution principles, enriching
        the guardian's ability to detect violations.

        Args:
            soul_values: List of SoulValue from soul_config.yaml
        """
        logger.info("⚖️  Injecting NOESIS soul values into ConstitutionGuardian...")

        # Build rich principles from soul values
        new_principles = []
        for value in sorted(soul_values, key=lambda v: v.rank):
            # Format: "VALUE_NAME (Greek/Hebrew): Definition"
            terms = []
            if value.term_greek:
                terms.append(value.term_greek)
            if value.term_hebrew:
                terms.append(value.term_hebrew)

            term_str = f" ({', '.join(terms)})" if terms else ""
            principle = f"{value.name}{term_str}: {value.definition}"
            new_principles.append(principle)

        # Update constitution
        self.constitution.core_principles = new_principles
        self.constitution.last_updated = datetime.now()
        self.constitution.version = "2.0.0-noesis"

        # Also create rules from the top 3 values (most critical)
        for i, value in enumerate(sorted(soul_values, key=lambda v: v.rank)[:3]):
            rule = ConstitutionRule(
                id=f"SOUL_VALUE_{i+1}",
                statement=f"Não violar o valor de {value.name}",
                rationale=value.definition,
                severity=ViolationSeverity.CRITICAL if i == 0 else ViolationSeverity.HIGH,
                active=True
            )
            # Avoid duplicates
            if not any(r.id == rule.id for r in self.constitution.rules):
                self.constitution.rules.append(rule)

        logger.info(
            "✅ Constitution updated with %d principles, %d rules",
            len(self.constitution.core_principles),
            len(self.constitution.rules)
        )

    def get_principles_for_prompt(self) -> str:
        """
        Generate a formatted string of principles for LLM prompts.

        Returns:
            Formatted principles string for context injection.
        """
        principles_lines = [
            f"  {i+1}. {p}"
            for i, p in enumerate(self.constitution.core_principles)
        ]
        rules_lines = [
            f"  - [{r.id}] ({r.severity.value}): {r.statement}"
            for r in self.constitution.rules if r.active
        ]

        return f"""
[CONSTITUTION v{self.constitution.version}]
Core Principles:
{chr(10).join(principles_lines)}

Active Rules:
{chr(10).join(rules_lines) if rules_lines else "  (No explicit rules defined)"}
"""
