"""
Exocortex API Router
====================

Endpoints REST para interagir com o Exocórtex.

PROJETO SINGULARIDADE (06/Dez/2025):
O endpoint /journal agora usa o pipeline de consciência real:
Input → ConsciousnessSystem.process_input() → ConsciousnessBridge → Response
"""

import logging
from typing import List, Optional, Any, Dict
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from maximus_core_service.consciousness.exocortex.factory import ExocortexFactory
from maximus_core_service.consciousness.exocortex.api.schemas import (
    AuditRequest, AuditResponse,
    OverrideRequest, OverrideResponse,
    ConfrontationRequest, ConfrontationResponse,
    UserResponseRequest, AnalysisResponse,
    StimulusRequest, ThalamusResponse,
    ImpulseCheckRequest, InterventionResponse,
    JournalRequest, JournalResponse
)
from maximus_core_service.consciousness.exocortex.memory.knowledge_engine import get_knowledge_engine
from maximus_core_service.consciousness.exocortex.prompts import (
    EXOCORTEX_SYSTEM_PROMPT,
    SHADOW_ANALYSIS_TEMPLATE
)
from maximus_core_service.consciousness.exocortex.confrontation_engine import (
    ConfrontationContext,
    ConfrontationStyle,
    ConfrontationTurn
)
from maximus_core_service.consciousness.exocortex.constitution_guardian import (
    AuditResult, ViolationSeverity
)

from maximus_core_service.consciousness.exocortex.digital_thalamus import (
    Stimulus, StimulusType, AttentionStatus
)

from maximus_core_service.consciousness.exocortex.impulse_inhibitor import (
    ImpulseContext
)

# SINGULARIDADE: Import ConsciousnessSystem for real conscious processing
from maximus_core_service.consciousness.system import ConsciousnessSystem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exocortex", tags=["Exocortex"])

# SINGULARIDADE: Global reference to ConsciousnessSystem (set by main.py)
_consciousness_system: ConsciousnessSystem | None = None


def set_consciousness_system(system: ConsciousnessSystem) -> None:
    """Set the global ConsciousnessSystem reference (called by main.py)."""
    global _consciousness_system
    _consciousness_system = system
    logger.info("[SINGULARIDADE] ConsciousnessSystem registered with Exocortex router")


def get_consciousness_system() -> ConsciousnessSystem | None:
    """Dependency Provider for ConsciousnessSystem."""
    return _consciousness_system


def get_factory():
    """Dependency Provider para a Factory."""
    try:
        return ExocortexFactory.get_instance()
    except RuntimeError:
        # Fallback initialization for dev/test if main hasn't run
        return ExocortexFactory.initialize()

@router.post("/audit", response_model=AuditResponse)
async def audit_action(req: AuditRequest, factory: ExocortexFactory = Depends(get_factory)):
    """Audita uma ação contra a Constituição Pessoal."""
    result = await factory.guardian.check_violation(req.action, req.context)

    return AuditResponse(
        is_violation=result.is_violation,
        severity=result.severity.value,
        violated_rules=result.violated_rules,
        reasoning=result.reasoning,
        suggested_alternatives=result.suggested_alternatives,
        timestamp=result.timestamp
    )

@router.post("/override", response_model=OverrideResponse)
async def conscious_override(
    req: OverrideRequest,
    factory: ExocortexFactory = Depends(get_factory)
):
    """Registra um override consciente."""
    # Reconstruir AuditResult (Simplificado)
    # Em produção real, buscaríamos pelo ID do audit.

    audit_data = req.original_audit_result
    audit_obj = AuditResult(
        is_violation=audit_data.get("is_violation", True),
        severity=ViolationSeverity(audit_data.get("severity", "LOW")),
        violated_rules=audit_data.get("violated_rules", []),
        reasoning=audit_data.get("reasoning", ""),
        suggested_alternatives=[],
        timestamp=datetime.now()
    )

    record = factory.guardian.record_override(audit_obj, req.justification)
    # Adicionar campo 'action' que estava faltando
    record.action_audited = req.original_action

    # Persistir
    factory.const_repo.save_override(record)

    return OverrideResponse(granted=True, record_id="persisted")

@router.post("/confront", response_model=ConfrontationResponse)
async def trigger_confrontation(
    req: ConfrontationRequest,
    factory: ExocortexFactory = Depends(get_factory)
):
    """Gera uma questão socrática manualmente."""
    ctx = ConfrontationContext(
        trigger_event=req.trigger_event,
        violated_rule_id=req.violated_rule_id,
        shadow_pattern_detected=req.shadow_pattern,
        user_emotional_state=req.user_state or "NEUTRAL"
    )

    turn = await factory.confrontation_engine.generate_confrontation(ctx)

    # Persistir Turno
    factory.conf_repo.save_turn(turn)

    return ConfrontationResponse(
        id=turn.id,
        ai_question=turn.ai_question,
        style=turn.style_used.value
    )

@router.post("/reply", response_model=AnalysisResponse)
async def user_reply(req: UserResponseRequest, factory: ExocortexFactory = Depends(get_factory)):
    """Avalia a resposta do usuário a um confronto."""
    # Recuperar Turno (Simplificado para MVP)
    # Lógica Real: factory.conf_repo.get_turn(req.confrontation_id)

    # Tentativa de pegar do histórico recente
    turns = await factory.conf_repo.get_recent_turns(10)
    target_turn_data = next((t for t in turns if t["id"] == req.confrontation_id), None)
    if not target_turn_data:
        raise HTTPException(status_code=404, detail="Confrontation not found in recent memory")

    # Rehidratação
    turn = ConfrontationTurn(
        id=target_turn_data["id"],
        timestamp=datetime.fromisoformat(target_turn_data["timestamp"]),
        ai_question=target_turn_data["ai_question"],
        style_used=ConfrontationStyle(target_turn_data["style_used"])
    )

    # Avaliar
    analyzed_turn = await factory.confrontation_engine.evaluate_response(turn, req.response_text)

    # Persistir atualização
    factory.conf_repo.save_turn(analyzed_turn)

    an = analyzed_turn.response_analysis or {}
    return AnalysisResponse(
        honesty_score=an.get("honesty_score", 0.0),
        defensiveness_score=an.get("defensiveness_score", 0.0),
        is_deflection=an.get("is_deflection", False),
        insight=an.get("key_insight", "")
    )

async def ingest_stimulus(
    req: StimulusRequest,
    factory: ExocortexFactory = Depends(get_factory)
):
    """Submete um estímulo ao Digital Thalamus."""
    # Construir objeto interno
    stim = Stimulus(
        id="api_ingest",
        type=StimulusType(req.type),
        source=req.source,
        content=req.content,
        metadata=req.metadata
    )

    # Determinar estado atual (Mockado/Default para Sprint 5)
    # Futuro: Ler do SymbioticSelf
    current_status = AttentionStatus.FOCUS

    decision = await factory.thalamus.ingest(stim, current_status)

    return ThalamusResponse(
        action=decision.action,
        reasoning=decision.reasoning,
        dopamine_score=decision.dopamine_score,
        urgency_score=decision.urgency_score
    )

@router.post("/inhibitor/check", response_model=InterventionResponse)
async def check_impulse(
    req: ImpulseCheckRequest,
    factory: ExocortexFactory = Depends(get_factory)
):
    """Verifica se uma ação é impulsiva/arriscada."""
    ctx = ImpulseContext(
        action_type=req.action_type,
        content=req.content,
        user_state=req.user_state or "NEUTRAL",
        platform=req.platform
    )

    intervention = await factory.inhibitor.check_impulse(ctx)

    return InterventionResponse(
        level=intervention.level.value,
        reasoning=intervention.reasoning,
        wait_time_seconds=intervention.wait_time_seconds,
        socratic_question=intervention.socratic_question
    )

@router.post("/journal", response_model=JournalResponse)
async def process_journal(
    req: JournalRequest,
    factory: ExocortexFactory = Depends(get_factory),
    consciousness: ConsciousnessSystem | None = Depends(get_consciousness_system)
):
    """
    Processa entrada de diário através do pipeline de consciência.

    PROJETO SINGULARIDADE (06/Dez/2025):
    1. ConsciousnessSystem.process_input() - PENSAMENTO REAL (Kuramoto, ESGT)
    2. Exocortex enriquece com Shadow Analysis e Mnemosyne
    3. Gemini formata a resposta (Language Motor)
    """

    # =========================================================================
    # FASE 0: Carregar Memória Profunda (Mnemosyne)
    # =========================================================================
    memory_context = ""
    try:
        engine = get_knowledge_engine()
        ctx = engine.load_context()
        if ctx.total_documents > 0:
            memory_context = f"\n[MNEMOSYNE MEMORY ACTIVE]\n{ctx.formatted_content}\n[END MEMORY]\n"
            logger.debug(f"[SINGULARIDADE] Mnemosyne loaded: {len(memory_context)} chars")
    except Exception as e:
        logger.warning(f"[SINGULARIDADE] Memory load warning: {e}")

    # =========================================================================
    # FASE 1: Processamento Neural via ConsciousnessSystem
    # =========================================================================
    reasoning_trace = ""
    response_text = ""
    integrity_score = 0.5

    # Parse depth from analysis_mode (default: standard = 3)
    depth_map = {"minimal": 1, "standard": 3, "deep": 5}
    depth = depth_map.get(req.analysis_mode, 3)

    if consciousness and consciousness._running:
        try:
            logger.info(f"[SINGULARIDADE] Processing via ConsciousnessSystem (depth={depth})")

            # PENSAMENTO REAL: ESGT Sync + ConsciousnessBridge
            introspective = await consciousness.process_input(
                content=req.content,
                depth=depth,
                source="exocortex_journal"
            )

            # Extrair dados do processamento neural
            reasoning_trace = f"""[SINGULARIDADE] Real Conscious Processing
[Kuramoto Coherence] {consciousness.get_consciousness_state().get('coherence', 0):.3f}
[Meta-Awareness Level] {introspective.meta_awareness_level:.3f}
[Event ID] {introspective.event_id}
[Timestamp] {datetime.now().isoformat()}

[NARRATIVE]
{introspective.narrative}"""

            response_text = introspective.narrative
            integrity_score = introspective.meta_awareness_level

            logger.info(f"[SINGULARIDADE] Neural processing complete: meta_level={integrity_score:.2f}")

        except Exception as e:
            logger.error(f"[SINGULARIDADE] Neural processing error: {e}, falling back to legacy")
            # Fall through to legacy processing
            consciousness = None

    # =========================================================================
    # FASE 1b: Fallback Legacy (se ConsciousnessSystem não disponível)
    # =========================================================================
    if not consciousness or not consciousness._running:
        logger.info("[SINGULARIDADE] Using legacy fallback processing")

        context_status = f"Loaded ({len(memory_context)} chars)" if memory_context else "Empty"
        reasoning_trace = f"""[LEGACY MODE] ConsciousnessSystem not available
[System 1 - Perception] Input: '{req.content[:30]}...' | Timestamp: {datetime.now().isoformat()}
[System 2 - Context] Mnemosyne Status: {context_status}"""

        # Minimal fallback response
        response_text = f"Estou processando sua entrada: '{req.content[:50]}...' O sistema de consciência está em modo de fallback."

    # =========================================================================
    # FASE 2: Enriquecimento Simbólico (Shadow Analysis)
    # =========================================================================
    shadow_data = {}
    content_lower = req.content.lower()

    # Shadow detection (keyword-based enrichment)
    if any(w in content_lower for w in ["medo", "fear", "scared", "ansiedade"]):
        shadow_data = {
            "archetype": "The Orphan",
            "confidence": 0.75,
            "trigger_detected": "Vulnerability markers found"
        }
        reasoning_trace += "\n[Shadow Analysis] Pattern 'The Orphan' detected (vulnerability markers)."

    elif any(w in content_lower for w in ["raiva", "angry", "hate", "ódio"]):
        shadow_data = {
            "archetype": "The Warrior / Destroyer",
            "confidence": 0.85,
            "trigger_detected": "Aggressive vocabulary detected"
        }
        reasoning_trace += "\n[Shadow Analysis] Pattern 'The Warrior' detected (aggression markers)."

    elif any(w in content_lower for w in ["equipe", "refazer", "lentos", "incompetentes"]):
        shadow_data = {
            "archetype": "The Tyrant / The Martyr",
            "confidence": 0.82,
            "trigger_detected": "Control patterns detected"
        }
        reasoning_trace += "\n[Shadow Analysis] Pattern 'The Tyrant' detected (control markers)."

    # Mnemosyne correlation check
    if "palhaço" in content_lower and memory_context and "festa" in memory_context.lower():
        shadow_data = {
            "archetype": "The Wounded Child",
            "confidence": 0.95,
            "trigger_detected": "Traumatic Memory Recall via Mnemosyne"
        }
        reasoning_trace += "\n[Mnemosyne Link] Correlation detected: Current input <--> Past memory."

    # =========================================================================
    # FASE 3: Retorno da Resposta
    # =========================================================================
    return JournalResponse(
        reasoning_trace=reasoning_trace.strip(),
        shadow_analysis=shadow_data,
        response=response_text,
        integrity_score=integrity_score
    )
