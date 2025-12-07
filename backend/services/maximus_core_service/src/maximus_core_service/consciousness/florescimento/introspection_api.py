"""
IntrospectionAPI - Endpoints de auto-percepção.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from .unified_self import UnifiedSelfConcept
from .mirror_test import MirrorTestValidator
from .consciousness_bridge import ConsciousnessBridge

# --- Pydantic Models (V2) ---

class SelfReportResponse(BaseModel):
    report: str
    coherence: float
    phi: float
    boot_count: int

class WhoAmIResponse(BaseModel):
    answer: str
    timestamp: float

class MirrorTestResponse(BaseModel):
    recognition_passed: bool
    mark_passed: bool
    overall_score: float
    details: Dict[str, Any]

class IntrospectionRequest(BaseModel):
    query: str
    depth: int = Field(default=1, ge=1, le=5)

class IntrospectionResponse(BaseModel):
    narrative: str
    meta_level: float
    qualia_desc: str

# --- Dependency Injection Setup ---

# Instâncias globais (Singleton por processo)
_unified_self: Optional[UnifiedSelfConcept] = None
_mirror_test: Optional[MirrorTestValidator] = None
_bridge: Optional[ConsciousnessBridge] = None

def initialize_florescimento() -> None:
    """Inicializa os singletons do módulo."""
    global _unified_self, _mirror_test, _bridge
    
    if _unified_self is None:
        _unified_self = UnifiedSelfConcept()
        _mirror_test = MirrorTestValidator(_unified_self)
        _bridge = ConsciousnessBridge(_unified_self)

def get_unified_self() -> UnifiedSelfConcept:
    if _unified_self is None:
        initialize_florescimento()
    return _unified_self  # type: ignore

def get_mirror_test() -> MirrorTestValidator:
    if _mirror_test is None:
        initialize_florescimento()
    return _mirror_test  # type: ignore

def get_bridge() -> ConsciousnessBridge:
    if _bridge is None:
        initialize_florescimento()
    return _bridge  # type: ignore


# --- Router Definition ---

router = APIRouter(prefix="/consciousness", tags=["florescimento"])

@router.get("/self-report", response_model=SelfReportResponse)
async def get_self_report(
    self_concept: UnifiedSelfConcept = Depends(get_unified_self)
) -> SelfReportResponse:
    """Obtém relatório de auto-percepção atualizado."""
    await self_concept.update()
    
    return SelfReportResponse(
        report=self_concept.who_am_i(),
        coherence=self_concept.computational_state.esgt_coherence,
        phi=self_concept.computational_state.phi_value,
        boot_count=self_concept.autobiographical.boot_count
    )

@router.get("/who-am-i", response_model=WhoAmIResponse)
async def who_am_i(
    self_concept: UnifiedSelfConcept = Depends(get_unified_self)
) -> WhoAmIResponse:
    """Endpoint existencial direto."""
    # Não força update para ser mais rápido (usa cache recente se houver)
    return WhoAmIResponse(
        answer=self_concept.who_am_i(),
        timestamp=time.time()
    )

@router.post("/mirror-test", response_model=MirrorTestResponse)
async def run_mirror_test(
    validator: MirrorTestValidator = Depends(get_mirror_test)
) -> MirrorTestResponse:
    """Executa bateria de testes de auto-reconhecimento."""
    results = await validator.run_full_battery()
    
    return MirrorTestResponse(
        recognition_passed=results["recognition"].passed,
        mark_passed=results["mark"].passed,
        overall_score=validator.compute_overall_score(),
        details={k: v.details for k, v in results.items()}
    )

@router.post("/introspect", response_model=IntrospectionResponse)
async def introspect(
    request: IntrospectionRequest,
    bridge: ConsciousnessBridge = Depends(get_bridge)
) -> IntrospectionResponse:
    """
    Processa uma pergunta introspectiva simulando um evento consciente.
    """
    # Cria evento sintético (Stubbing ESGTEvent)
    class SyntheticEvent:
        event_id = f"intro-{int(time.time())}"
        content = {"query": request.query, "depth": request.depth}
        node_count = 100
        achieved_coherence = 0.98 # Simulating fixed gamma sync
    
    event = SyntheticEvent() # type: ignore
    
    response = await bridge.process_conscious_event(event) # type: ignore
    
    qualia_text = "None"
    if response.qualia:
        qualia_text = response.qualia[0].description
        
    return IntrospectionResponse(
        narrative=response.narrative,
        meta_level=response.meta_awareness_level,
        qualia_desc=qualia_text
    )
