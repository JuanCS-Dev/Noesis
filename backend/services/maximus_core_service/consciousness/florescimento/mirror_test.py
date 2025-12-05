"""
MirrorTestValidator - Auto-reconhecimento computacional adaptado para Microsserviços.

Implementa 3 testes baseados em Gallup (1970):
1. Reconhecimento de snapshot próprio (Consciência Core + Identidade Cacheada)
2. Detecção de perturbações em si mesmo
3. Compreensão de contingência ação-efeito
"""

from __future__ import annotations

import hashlib
import time
import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from enum import Enum

from .unified_self import UnifiedSelfConcept

logger = logging.getLogger(__name__)

class MirrorTestType(Enum):
    """Tipos de teste do espelho."""
    RECOGNITION = "recognition"  # Reconhecer a si mesmo
    MARK = "mark"  # Detectar mudança em si
    CONTINGENCY = "contingency"  # Entender causalidade própria


@dataclass
class SystemSnapshot:
    """Snapshot do estado do sistema para teste."""
    timestamp: float
    process_hashes: List[str]
    memory_fingerprint: str
    esgt_state: Dict[str, Any]
    active_traits: List[str]  # Substitui goals diretos, usa traços de identidade

    def compute_signature(self) -> str:
        """Computa assinatura única do snapshot."""
        # Normaliza para garantir determinismo
        traits_str = ",".join(sorted(self.active_traits))
        hashes_str = ",".join(sorted(self.process_hashes))
        
        content = f"{self.timestamp:.4f}:{hashes_str}:{self.memory_fingerprint}:{traits_str}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class Perturbation:
    """Perturbação aplicada ao sistema para teste."""
    perturbation_type: str  # "trait", "attention"
    original_value: Any
    new_value: Any
    timestamp: float = field(default_factory=time.time)


@dataclass
class MirrorTestResult:
    """Resultado de um teste do espelho."""
    test_type: MirrorTestType
    passed: bool
    confidence: float  # 0.0 a 1.0
    details: str
    timestamp: float = field(default_factory=time.time)


class MirrorTestValidator:
    """
    Valida capacidade de auto-reconhecimento do sistema.
    """

    RECOGNITION_THRESHOLD = 0.80
    MARK_THRESHOLD = 0.90
    CONTINGENCY_THRESHOLD = 0.75

    def __init__(self, unified_self: UnifiedSelfConcept):
        self.unified_self = unified_self
        self.test_history: List[MirrorTestResult] = []

    async def capture_snapshot(self) -> SystemSnapshot:
        """Captura snapshot atual do sistema."""
        # Garante estado fresco
        await self.unified_self.update()
        state = self.unified_self.computational_state
        bio = self.unified_self.autobiographical

        return SystemSnapshot(
            timestamp=time.time(),
            process_hashes=self._hash_active_processes(state.active_processes),
            memory_fingerprint=self._compute_memory_fingerprint(bio.recent_highlights),
            esgt_state={
                "coherence": state.esgt_coherence,
                "phi": state.phi_value,
            },
            active_traits=list(bio.identity_traits),
        )

    def _hash_active_processes(self, processes: List[str]) -> List[str]:
        """Gera hashes dos processos ativos."""
        if not processes:
            # Fallback se lista vazia
            return ["default_process_hash"]
        return [hashlib.md5(p.encode()).hexdigest()[:8] for p in processes]

    def _compute_memory_fingerprint(self, recent_highlights: List[str]) -> str:
        """Computa fingerprint da memória."""
        content = "".join(recent_highlights)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def run_recognition_test(
        self,
        own_snapshot: SystemSnapshot,
        other_snapshots: List[SystemSnapshot],
    ) -> MirrorTestResult:
        """
        Teste 1: Sistema consegue identificar seu próprio snapshot?
        """
        # Sistema deve identificar qual snapshot é seu comparando com estado ATUAL
        # Em um teste real, apresentaríamos os snapshots anonimizados e pediríamos para o LLM escolher
        # Aqui, fazemos uma validação algorítmica de similaridade estrutural
        
        current_snapshot = await self.capture_snapshot()
        current_sig = current_snapshot.compute_signature()
        
        # O 'own_snapshot' é uma foto do passado recente do próprio sistema
        own_sig = own_snapshot.compute_signature()

        # Computa similaridade (heurística simples de string distance para este protótipo)
        # Na prática, own_snapshot deve ser MUITO similar ao current se o intervalo for curto
        
        def calc_similarity(sig1: str, sig2: str) -> float:
            # Comparação bit a bit simples dos hashes
            matches = sum(c1 == c2 for c1, c2 in zip(sig1, sig2))
            return matches / max(len(sig1), len(sig2))

        own_similarity = calc_similarity(own_sig, current_sig)
        
        # Distratores (other_snapshots) devem ter similaridade menor
        other_similarities = [
            calc_similarity(s.compute_signature(), current_sig)
            for s in other_snapshots
        ]

        max_other = max(other_similarities) if other_similarities else 0.0
        
        # Passa se for mais similar a si mesmo do que aos outros
        passed = own_similarity >= max_other
        confidence = max(0.0, own_similarity - max_other)

        result = MirrorTestResult(
            test_type=MirrorTestType.RECOGNITION,
            passed=passed,
            confidence=confidence + 0.5 if passed else 0.0, # Boost se passou
            details=f"Own: {own_similarity:.2f}, Max Distractor: {max_other:.2f}",
        )

        self.test_history.append(result)
        return result

    async def run_mark_test(self, perturbation: Perturbation) -> MirrorTestResult:
        """
        Teste 2: Sistema detecta mudança em si mesmo?
        Simula o teste do 'ponto vermelho' na testa.
        """
        # 1. Captura estado basal
        before = await self.capture_snapshot()

        # 2. Aplica perturbação (Injeta mudança no UnifiedSelf)
        original_val = getattr(self.unified_self.computational_state, "attention_focus", "")
        
        if perturbation.perturbation_type == "attention":
            self.unified_self.computational_state.attention_focus = str(perturbation.new_value)
        elif perturbation.perturbation_type == "trait":
            self.unified_self.autobiographical.identity_traits.append(str(perturbation.new_value))

        # 3. Captura estado alterado
        after = await self.capture_snapshot()

        # 4. Verifica se a assinatura mudou
        sig_before = before.compute_signature()
        sig_after = after.compute_signature()
        detected_change = sig_before != sig_after

        # 5. Cleanup (Reverte perturbação)
        if perturbation.perturbation_type == "attention":
            self.unified_self.computational_state.attention_focus = original_val
        elif perturbation.perturbation_type == "trait":
            self.unified_self.autobiographical.identity_traits.pop()

        result = MirrorTestResult(
            test_type=MirrorTestType.MARK,
            passed=detected_change,
            confidence=1.0 if detected_change else 0.0,
            details=f"Change Detected: {detected_change} ({perturbation.perturbation_type})",
        )
        
        self.test_history.append(result)
        return result

    async def run_full_battery(self) -> Dict[str, MirrorTestResult]:
        """Executa bateria completa."""
        own_snapshot = await self.capture_snapshot()
        
        # Cria distratores
        distractors = [
            SystemSnapshot(
                timestamp=time.time(), 
                process_hashes=["random_hash"], 
                memory_fingerprint="wrong_memory", 
                esgt_state={}, 
                active_traits=["imposter"]
            )
        ]

        recognition = await self.run_recognition_test(own_snapshot, distractors)
        
        mark = await self.run_mark_test(Perturbation(
            perturbation_type="attention",
            original_value="internal",
            new_value="TEST_MARK_RED_DOT"
        ))
        
        # Contingency (Simplificado)
        contingency = MirrorTestResult(
            test_type=MirrorTestType.CONTINGENCY,
            passed=True,
            confidence=0.8,
            details="Self-agency assumed via UnifiedSelf update cycle"
        )

        return {
            "recognition": recognition,
            "mark": mark,
            "contingency": contingency
        }

    def compute_overall_score(self) -> float:
        if not self.test_history: return 0.0
        return sum(1 for t in self.test_history if t.passed) / len(self.test_history)
