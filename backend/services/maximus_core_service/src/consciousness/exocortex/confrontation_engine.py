"""
ConfrontationEngine - Sistema Socrático de Desafio
==================================================

Motor responsável por desafiar o usuário quando padrões negativos ("Shadows")
ou violações constitucionais são detectados.

Filosofia:
- Não sermoneia. Pergunta. (Método Socrático)
- Busca a raiz do comportamento, não apenas a correção superficial.
- Adapta a intensidade baseada na severidade do gatilho.

Padrões Técnicos:
- Gemini 3.0 para geração de diálogo.
- Análise de sentimento/honestidade na resposta.
"""

from __future__ import annotations

import logging
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

from utils.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class ConfrontationStyle(str, Enum):
    """Estilo do confronto socrático."""
    GENTLE_INQUIRY = "GENTLE_INQUIRY"     # Curiosidade, sem julgamento
    DIRECT_CHALLENGE = "DIRECT_CHALLENGE" # Aponta a contradição explicitamente
    RADICAL_HONESTY = "RADICAL_HONESTY"   # Sem filtro, espelho cru da realidade
    PHILOSOPHICAL = "PHILOSOPHICAL"       # Abstrato, focado em princípios

@dataclass
class ConfrontationContext:
    """Contexto para gerar o confronto."""
    trigger_event: str
    violated_rule_id: Optional[str] = None
    shadow_pattern_detected: Optional[str] = None
    user_emotional_state: str = "NEUTRAL"
    recent_history_summary: str = ""

@dataclass
class ConfrontationTurn:
    """Um turno de diálogo de confrontação."""
    id: str
    timestamp: datetime
    ai_question: str
    style_used: ConfrontationStyle
    user_response: Optional[str] = None
    response_analysis: Optional[Dict[str, Any]] = None # Honestidade, defensividade

class ConfrontationEngine:
    """
    Motor de Confrontação Socrática.
    """

    def __init__(self, gemini_client: GeminiClient, workspace: Any = None) -> None:
        self.gemini_client = gemini_client
        self.workspace = workspace

        if self.workspace:
            self._register_subscribers()

    def _register_subscribers(self):
        """Registra listeners no Global Workspace."""
        # Import local para evitar ciclo
        from src.consciousness.exocortex.global_workspace import ( # pylint: disable=import-outside-toplevel
            EventType
        )

        self.workspace.subscribe(EventType.IMPULSE_DETECTED, self.handle_conscious_event)
        self.workspace.subscribe(
            EventType.CONSTITUTION_VIOLATION, self.handle_conscious_event
        )

    async def handle_conscious_event(self, event: Any) -> None:
        """Reage a eventos conscientes gerando confrontação se necessário."""
        # Mapeia evento para contexto de confrontação
        should_confront = False
        context = None

        # Import local para evitar ciclo no Typing se necessário, ou usar Any como fiz

        if event.type.value == "IMPULSE_DETECTED":
            # Se for um impulso pausado ou bloqueado/arriscado
            level = event.payload.get("level")
            if level in ["PAUSE", "BLOCK"]:
                should_confront = True
                context = ConfrontationContext(
                    trigger_event=f"Impulse {level}: {event.payload.get('impulse_type')}",
                    shadow_pattern_detected="Impulsivity",
                    user_emotional_state=event.payload.get("user_state", "UNKNOWN")
                )

        elif event.type.value == "CONSTITUTION_VIOLATION":
            should_confront = True
            context = ConfrontationContext(
                trigger_event="Constitution Violation",
                violated_rule_id=event.payload.get("rule_ids", ["UNKNOWN"])[0],
                user_emotional_state="UNKNOWN" # Guardian might provide via payload future
            )

        if should_confront and context:
            logger.info("Triggering Confrontation via Workspace Event: %s", event.id)
            # O que fazemos com a confrontação gerada?
            # Por enquanto, apenas geramos e talvez logamos ou publicamos outro evento?
            # Ou salvamos no DB?
            # O sistema atual é API-pull based (/confront).
            # Para ser proativo, precisaríamos pushar para o frontend ou salvar como "pendente".
            # Vamos apenas gerar e logar (simulação de push)
            confrontation = await self.generate_confrontation(context)
            logger.info("Confrontation Generated: %s", confrontation.ai_question)

            # Future: Publish CONFRONTATION_STARTED event back to Workspace

    def _determine_style(self, context: ConfrontationContext) -> ConfrontationStyle:
        """Determina o estilo baseado no contexto (Lógica determinística simples por enquanto)."""
        if context.violated_rule_id:
            # Violação de regra -> Desafio Direto
            return ConfrontationStyle.DIRECT_CHALLENGE
        if context.shadow_pattern_detected:
            # Padrão de sombra -> Inquérito Gentil inicial
            return ConfrontationStyle.GENTLE_INQUIRY

        return ConfrontationStyle.PHILOSOPHICAL

    async def generate_confrontation(
        self,
        context: ConfrontationContext
    ) -> ConfrontationTurn:
        """
        Gera uma pergunta socrática para confrontar o usuário.
        """
        style = self._determine_style(context)

        prompt = f"""
        [ROLE]
        You are the 'Daimon' (Inner Voice/Exocortex) of the user.
        Your goal is active psychological growth via Socratic Method.

        [TRIGGER]
        Event: {context.trigger_event}
        Shadow/Violation: {context.shadow_pattern_detected or context.violated_rule_id}
        User State: {context.user_emotional_state}

        [STRATEGY]
        Style: {style.value}
        Goal: Make the user reflect on WHY they did this, without being accusatory.
        Format: A single, piercing question. Max 20 words.
        """

        try:
            # Configuração de resposta simples (texto)
            response = await self.gemini_client.generate_text(
                prompt=prompt,
                temperature=0.7, # Criatividade moderada para perguntas perspicazes
            )

            question = response.get("text", "").strip()
            if not question:
                question = "Por que você escolheu agir assim?" # Fallback

            return ConfrontationTurn(
                id=f"conf_{int(datetime.now().timestamp())}",
                timestamp=datetime.now(),
                ai_question=question,
                style_used=style
            )

        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error("Erro ao gerar confrontação: %s", e)
            return ConfrontationTurn(
                id="error_fallback",
                timestamp=datetime.now(),
                ai_question="Percebo uma dissonância. O que está acontecendo?",
                style_used=ConfrontationStyle.GENTLE_INQUIRY
            )

    async def evaluate_response(
        self,
        turn: ConfrontationTurn,
        user_response: str
    ) -> ConfrontationTurn:
        """
        Avalia a resposta do usuário (Honestidade vs Defensividade).
        """
        turn.user_response = user_response

        response_schema = {
            "type": "OBJECT",
            "properties": {
                "honesty_score": {"type": "NUMBER"}, # 0.0 a 1.0
                "defensiveness_score": {"type": "NUMBER"}, # 0.0 a 1.0
                "is_deflection": {"type": "BOOLEAN"},
                "key_insight": {"type": "STRING"}
            },
            "required": ["honesty_score", "defensiveness_score", "is_deflection"]
        }

        prompt = f"""
        [TASK]
        Analyze the user's response to a confrontation.

        [CONTEXT]
        Question: "{turn.ai_question}"
        User Response: "{user_response}"

        [METRICS]
        - Honesty: Is the user admitting the truth or hiding?
        - Defensiveness: Are they attacking back or justifying excessively?
        - Deflection: Are they changing the subject?
        """

        try:
            response = await self.gemini_client.generate_text(
                prompt=prompt,
                response_schema=response_schema,
                temperature=0.0
            )

            # Parse Safe (usando lógica já validada no sprint anterior)
            analysis = {}
            if response["text"]:
                try:
                    analysis = json.loads(response["text"])
                except json.JSONDecodeError:
                    logger.error("Falha JSON em evaluate_response")

            turn.response_analysis = analysis
            return turn

        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error("Erro ao avaliar resposta: %s", e)
            turn.response_analysis = {"error": str(e)}
            return turn
