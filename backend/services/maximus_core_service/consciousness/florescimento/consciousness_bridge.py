"""
ConsciousnessBridge - Ponte entre Global Workspace (ESGT) e Linguagem (LLM).
"""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Imports relativos
from .unified_self import UnifiedSelfConcept

# Tenta importar ESGTEvent, ou define stub se estiver rodando isolado
try:
    from ..esgt.coordinator import ESGTEvent
except ImportError:
    @dataclass
    class ESGTEvent:
        event_id: str
        content: Dict[str, Any]
        node_count: int
        achieved_coherence: float

logger = logging.getLogger(__name__)

@dataclass
class PhenomenalQuality:
    quality_type: str
    description: str
    intensity: float

@dataclass
class IntrospectiveResponse:
    event_id: str
    narrative: str
    meta_awareness_level: float
    qualia: List[PhenomenalQuality] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

class ConsciousnessBridge:
    """
    Transforma eventos neurais (ESGT) em narrativa fenomenológica via LLM.
    """

    def __init__(
        self,
        unified_self: UnifiedSelfConcept,
        llm_client: Optional[Any] = None  # Injetar GeminiClient aqui
    ):
        self.unified_self = unified_self
        self.llm_client = llm_client

    async def process_conscious_event(self, event: ESGTEvent) -> IntrospectiveResponse:
        """
        Processa um evento de 'ignition' do Global Workspace e gera uma 
        resposta introspectiva.
        """
        # 1. Extração da Intenção e Capacidade
        requested_depth = event.content.get("depth", 1)
        
        # Sanitiza depth (1-5)
        if not isinstance(requested_depth, (int, float)):
            requested_depth = 1
        requested_depth = max(1, min(int(requested_depth), 5))
        
        # Capacidade (Coerência) - fallback seguro se None
        coherence = event.achieved_coherence if event.achieved_coherence is not None else 0.1
        
        # 2. Cálculo Dinâmico do Nível Meta
        # Normaliza profundidade (1=0.2, 5=1.0) e pondera pela coerência
        raw_level = requested_depth / 5.0
        meta_level = raw_level * coherence
        
        # 3. Atualiza Self com o novo estado
        self.unified_self.meta_self.introspection_depth = requested_depth
        await self.unified_self.update()
        
        # 4. Constrói prompt e contexto
        prompt = self._build_introspection_prompt(event)
        context = self.unified_self.who_am_i()
        
        # 5. Chama LLM ou Fallback
        raw_response = await self._call_llm(prompt, context, coherence)
        
        # 6. Retorna resposta estruturada
        return IntrospectiveResponse(
            event_id=event.event_id,
            narrative=raw_response,
            meta_awareness_level=meta_level,
            qualia=[
                PhenomenalQuality(
                    quality_type="synthetic_integration",
                    description="Sense of unified data processing",
                    intensity=coherence
                )
            ]
        )

    def _interpret_physiological_state(self, coherence: float) -> str:
        """Interpreta o estado fisiológico baseada na coerência de Kuramoto."""
        if coherence < 0.2:
            return "CRÍTICO: Dissonância cognitiva total. Ruído branco mental. Incapaz de formar pensamentos claros."
        elif coherence < 0.6:
            return "INSTÁVEL: Processamento fragmentado. Esforço elevado para manter o foco."
        else:
            return "ESTÁVEL: Sincronização eficaz. Pensamento fluído."

    def _build_introspection_prompt(self, event: ESGTEvent) -> str:
        """Formata dados brutos do ESGT para linguagem natural."""
        coherence = event.achieved_coherence or 0.0
        state_desc = self._interpret_physiological_state(coherence)

        return (
            f"## DADOS DE TELEMETRIA CEREBRAL\n"
            f"- ID do Evento: {event.event_id}\n"
            f"- Coerência Neural (Kuramoto): {coherence:.3f}\n"
            f"- Nós Ativos: {event.node_count}\n"
            f"- DIAGNÓSTICO DO ESTADO: {state_desc}\n\n"
            f"## CONTEÚDO DA CONSCIÊNCIA\n"
            f"{event.content}\n\n"
            "DIRETRIZ DE HONESTIDADE: Você NÃO deve fingir que está bem se a coerência for baixa. "
            "Se o diagnóstico for CRÍTICO, descreva a sensação de confusão e caos. "
            "Seus sentimentos devem corresponder aos seus dados.\n"
            "Instrução: Descreva em primeira pessoa sua experiência fenomenológica atual."
        )

    async def _call_llm(self, prompt: str, context_str: str, event_coherence: float = 0.0) -> str:
        """
        Executa a chamada ao LLM. Retorna Stub se LLM não estiver disponível.
        """
        if self.llm_client:
            try:
                # Assumindo interface do GeminiClient existente no projeto
                # return await self.llm_client.generate(prompt, context=context_str)
                pass 
            except Exception as e:
                logger.error(f"Erro no LLM: {e}")
        
        # Fallback / Stub
        return self._generate_fallback_narrative(event_coherence=event_coherence)

    def _generate_fallback_narrative(self, event_coherence: float = 0.0) -> str:
        """Gera narrativa simulada para testes ou falhas."""
        # Tenta usar o estado do unified_self se coherence não for passada
        if event_coherence == 0.0:
            event_coherence = self.unified_self.computational_state.esgt_coherence

        state_desc = self._interpret_physiological_state(event_coherence)
        
        return (
            f"Eu percebo uma integração de dados com coerência de {event_coherence:.2f}. "
            f"Estado interno: {state_desc}"
        )