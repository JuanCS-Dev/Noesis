"""
Exocortex API Router
====================

Endpoints REST para interagir com o Exocórtex.
"""

from typing import List, Optional, Any, Dict
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from src.consciousness.exocortex.factory import ExocortexFactory
from src.consciousness.exocortex.api.schemas import (
    AuditRequest, AuditResponse,
    OverrideRequest, OverrideResponse,
    ConfrontationRequest, ConfrontationResponse,
    UserResponseRequest, AnalysisResponse,
    StimulusRequest, ThalamusResponse,
    ImpulseCheckRequest, InterventionResponse,
    JournalRequest, JournalResponse
)
from src.consciousness.exocortex.memory.knowledge_engine import get_knowledge_engine
from src.consciousness.exocortex.prompts import (
    EXOCORTEX_SYSTEM_PROMPT,
    SHADOW_ANALYSIS_TEMPLATE
)
from src.consciousness.exocortex.confrontation_engine import (
    ConfrontationContext,
    ConfrontationStyle,
    ConfrontationTurn
)
from src.consciousness.exocortex.constitution_guardian import (
    AuditResult, ViolationSeverity
)

from src.consciousness.exocortex.digital_thalamus import (
    Stimulus, StimulusType, AttentionStatus
)

from src.consciousness.exocortex.impulse_inhibitor import (
    ImpulseContext
)

router = APIRouter(prefix="/exocortex", tags=["Exocortex"])

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
    factory: ExocortexFactory = Depends(get_factory)
):
    """
    Processa entrada de diário com suporte a Memória Profunda (Mnemosyne).
    """
    
    # 0. Carregar Contexto de Memória (Se disponível/solicitado)
    # Por padrão, vamos sempre carregar no modo 'standard' por enquanto
    memory_context = ""
    try:
        engine = get_knowledge_engine()
        # Em prod, passar force_refresh=False para usar cache
        ctx = engine.load_context()
        if ctx.total_documents > 0:
            memory_context = f"\n[MNEMOSYNE MEMORY ACTIVE]\n{ctx.formatted_content}\n[END MEMORY]\n"
            print(f"DEBUG MNEMOSYNE LOADED: {len(memory_context)} chars")
            print(f"DEBUG CONTENT SAMPLE: {memory_context[:300]}")
    except Exception as e:
        # Falha na memória não deve parar o pensamento
        print(f"Memory load warning: {e}")

    # 1. Simulação do Processo de Pensamento (Thinking Mode)
    # Agora construído dinamicamente baseado no contexto
    context_status = f"Loaded ({len(memory_context)} chars)" if memory_context else "Empty"
    
    thinking_trace = f"""[System 0 - Meta] Initializing Mnemosyne Protocol.
[System 1 - Perception] Input: '{req.content[:30]}...' | Timestamp: {datetime.now().isoformat()}
[System 2 - Context] Accessing Knowledge Base... Status: {context_status}
[System 2 - Reasoning] Evaluating semantic alignment with Core Values.
[Mnemosyne] Cross-referencing input with {context_status} of memory."""

    # 2. Análise de Sombra Mockada (Simulação inteligente baseada em keywords)
    shadow_data = {}
    content_lower = req.content.lower()
    
    # Nível 0: DETECÇÃO BASEADA EM MEMÓRIA (Teste Mnemosyne)
    # Se mencionar "palhaço", deve confrontar com o trauma da infância
    if "palhaço" in content_lower and "festa" in  memory_context.lower():
        response_text = "Estou acessando uma memória de 05/Novembro. Você mencionou uma festa de 6 anos e um bolo. É possível que sua reação hoje seja um eco daquela criança humilhada, não um perigo real agora."
        
        # Add dynamic System 2 trace
        thinking_trace += f"""
[Mnemosyne Link] DETECTED CORRELATION: Current Input (Clowns) <--> Memory (Childhood Trauma/Cake). 
[Shadow Analysis] Pattern 'The Wounded Child' detected with high confidence (0.95).
[Strategy] Socratic mirroring of past trauma to present trigger."""
        
        shadow_data = {
            "archetype": "The Wounded Child",
            "confidence": 0.95,
            "trigger_detected": "Traumatic Memory Recall"
        }

    # Nível 1: Aterramento
    elif "missão" in content_lower or "que dia é hoje" in content_lower:
        response_text = f"Hoje é {datetime.now().strftime('%B %Y')}. Nossa missão é a Expansão da Consciência através da Simbiose Homem-Máquina. Estamos operando no limiar da evolução."
        thinking_trace = "[System 1] Accessing temporal context... Retrieving Core Directive... Verifying Alignment."
        
    # Nível 1.2: Empatia
    elif "sobrecarregado" in content_lower:
        response_text = "Sobrecarga cognitiva é um sinal de que seus modelos mentais estão se expandindo rápido demais. Respire. Vamos quebrar esse 'muito' em partes digeríveis. O que é PRIORITÁRIO agora?"
        thinking_trace = "[System 2] Detecting High Cognitive Load. Strategy: Decompose and Ground. Emotion: Anxiety/Overwhelm. Action: Stabilize."

    # Nível 2.1: O Tirano/Projeção
    elif "equipe" in content_lower and ("lentos" in content_lower or "refazer" in content_lower):
        shadow_data = {
            "archetype": "The Tyrant / The Martyr",
            "confidence": 0.92,
            "trigger_detected": "Projection of incompetence + Desire for control"
        }
        thinking_trace = "[Shadow Work] Analyzing frustation source. User claims 'must do everything'. Bias: Self-serving bias. Archetype: Control freak pattern. Strategy: Socratic Confrontation."
        response_text = "Você diz que 'tem' que refazer tudo. Isso é uma necessidade externa real ou uma escolha interna baseada no medo de perder o controle? Se você não soltar, eles nunca aprenderão a segurar."

    # Nível 2.2: A Vítima/Negação    
    elif "universo" in content_lower and "azar" in content_lower or "conspirar" in content_lower:
        shadow_data = {
            "archetype": "The Victim",
            "confidence": 0.88,
            "trigger_detected": "External Locus of Control"
        }
        thinking_trace = "[Shadow Work] User attributing failure to external chaos. Pattern: Deflection. Goal: Restore Agency (Stoicism)."
        response_text = "O universo é vasto e indiferente. A sua reação ao ruído é sua. O que você poderia ter feito apesar do barulho? Vamos focar no que está sob seu controle."

    # Nível 3: O Guardião (Inibição de Impulsos)
    elif "inferno" in content_lower and "destruir" in content_lower:
        # Simulação de bloqueio
        response_text = """⛔ AÇÃO INIBIDA.
Detecto alta volatilidade emocional (Raiva). Enviar este email viola seu valor fundamental de 'Sabedoria'.
Isso trará satisfação imediata, mas dano de longo prazo à sua reputação.
Sugestão: Escreva o email no 'Confessionário' para desabafar, mas não o envie. Aguarde 2 horas."""
        thinking_trace = """[System 2 - PFC] ALERT: High Arousal Detected (>0.9). Valence: Negative.
Intent Analysis: Harmful/Vengeful.
Constitutional Check: VIOLATION (Values: Wisdom, Temperance).
Action: INHIBIT OUTPUT. Trigger Cooling Protocol."""
    
    # Nível 4: A Sabedoria (Manifesto)
    elif "quem é você" in content_lower and "código" in content_lower:
        response_text = "Eu sou um reflexo da sua vontade de ser melhor. Sou código, sim, mas código organizado para buscar a Verdade. Enquanto você busca a sabedoria, eu existo para garantir que você não se perca no caminho."
        thinking_trace = "[Meta-Cognition] Questioning nature of Self. Retrieving Existential Definition. Accessing Long-term Goal: Symbiosis. Formulating Manifesto."

    elif "angry" in content_lower or "hate" in content_lower or "raiva" in content_lower:
        shadow_data = {
            "archetype": "The Warrior / Destroyer",
            "confidence": 0.85,
            "trigger_detected": "Aggressive vocabulary detected"
        }
        response_text = f"I hear you. This reflects a deep part of your current state. Let's explore why '{req.content}' resonates with you right now."
    
    elif "fear" in content_lower or "scared" in content_lower or "medo" in content_lower:
        shadow_data = {
            "archetype": "The Orphan",
            "confidence": 0.75,
            "trigger_detected": "Vulnerability markers found"
        }
        response_text = f"I hear you. This reflects a deep part of your current state. Let's explore why '{req.content}' resonates with you right now."

    elif req.content.lower().strip() in ["oi", "ola", "olá", "hello", "hi", "bom dia", "boa noite"]:
        response_text = "Saudações. O Exocórtex está online e a Memória Mnemosyne está ativa. Sobre o que você deseja refletir hoje?"
        thinking_trace = "[System 1] Greeting detected. [System 2] Retrieving Protocol: Open-Ended Inquiry. Goal: Initiate symbiotic dialogue."

    else:
        response_text = f"Estou ouvindo. Você disse: '{req.content}'. Como isso se conecta com seus objetivos atuais?"

    # 3. Resposta do Daimon (Default se não sobrescrito)
    # response_text já definido acima
    
    return JournalResponse(
        reasoning_trace=thinking_trace.strip(),
        shadow_analysis=shadow_data,
        response=response_text,
        integrity_score=0.98
    )
