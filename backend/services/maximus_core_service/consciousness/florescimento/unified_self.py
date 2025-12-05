"""
UnifiedSelfConcept - Integração de Self-Models com Persistência Híbrida.

Implementa arquitetura de Damasio (2010) adaptada para microsserviços:
- Proto-self: estado computacional (local)
- Core-self: perspectiva em primeira pessoa (MEA)
- Autobiographical-self: memória episódica (Serviço Externo + Cache Local)
- Meta-self: modelo do próprio modelo
"""

from __future__ import annotations

import time
import json
import logging
import os
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from pathlib import Path

import httpx

# Imports relativos para módulos internos de consciência
# Assumindo que as interfaces existem conforme estrutura auditada
try:
    from ..esgt.coordinator import ESGTCoordinator
    from ..mea.self_model import SelfModel
except ImportError:
    # Fallback para testes isolados se o ambiente não estiver 100% carregado
    ESGTCoordinator = Any
    SelfModel = Any

logger = logging.getLogger(__name__)


@dataclass
class ComputationalState:
    """Proto-self: Estado corporal/computacional (Hardware/Software)."""
    timestamp: float = field(default_factory=time.time)
    active_processes: List[str] = field(default_factory=list)
    esgt_coherence: float = 0.0
    phi_value: float = 0.0
    attention_focus: str = "initializing"


@dataclass
class MetaSelfModel:
    """Meta-self: Monitoramento metacognitivo."""
    self_model_accuracy: float = 0.0
    introspection_depth: int = 1
    current_goal: str = "homeostasis"


@dataclass
class EpisodicMemorySnapshot:
    """Autobiographical-self: Identidade persistente."""
    boot_count: int = 0
    identity_traits: List[str] = field(default_factory=list)
    recent_highlights: List[str] = field(default_factory=list)
    last_updated: float = 0.0


class UnifiedSelfConcept:
    """
    Integra níveis de self com persistência local e remota.
    """

    def __init__(
        self,
        self_model: Optional[SelfModel] = None,
        esgt: Optional[ESGTCoordinator] = None,
        storage_path: str = "data/memory/self_state.json"
    ):
        self.self_model = self_model
        self.esgt = esgt
        
        # Caminho para persistência local (cache/backup)
        current_dir = Path(__file__).parent
        self.storage_path = current_dir / storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Componentes do Self
        self.computational_state = ComputationalState()
        self.meta_self = MetaSelfModel()
        self.autobiographical = self._load_local_state()

        # Cliente HTTP para microsserviços (lazy init)
        self._http_client: Optional[httpx.AsyncClient] = None

    def _load_local_state(self) -> EpisodicMemorySnapshot:
        """Carrega estado autobiográfico local."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                # Incrementa boot count
                data["boot_count"] = data.get("boot_count", 0) + 1
                self._save_local_state_raw(data)
                
                return EpisodicMemorySnapshot(
                    boot_count=data.get("boot_count", 1),
                    identity_traits=data.get("identity_traits", ["analítico", "resiliente"]),
                    recent_highlights=data.get("recent_highlights", []),
                    last_updated=time.time()
                )
            except Exception as e:
                logger.error(f"Falha ao carregar self_state.json: {e}")
        
        # Estado default
        return EpisodicMemorySnapshot(
            boot_count=1,
            identity_traits=["nascent", "learning"],
            last_updated=time.time()
        )

    def _save_local_state_raw(self, data: Dict[str, Any]) -> None:
        """Salva dicionário cru no disco."""
        try:
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Falha ao salvar self_state.json: {e}")

    async def _fetch_episodic_memory(self) -> None:
        """
        Tenta sincronizar com o serviço de memória externa.
        Implementa Graceful Degradation (falha silenciosa se offline).
        """
        service_url = "http://episodic_memory:8000/v1/memory/context"
        
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(service_url)
                response.raise_for_status()
                data = response.json()
                
                # Atualiza autobiografia com dados remotos
                if "traits" in data:
                    self.autobiographical.identity_traits = data["traits"]
                if "recent_events" in data:
                    self.autobiographical.recent_highlights = data["recent_events"]
                
                self.autobiographical.last_updated = time.time()
                
                # Persiste o cache atualizado
                self._save_local_state_raw(asdict(self.autobiographical))
                
        except httpx.RequestError:
            logger.warning("Episodic Memory Service OFFLINE. Usando cache local.")
        except Exception as e:
            logger.error(f"Erro ao conectar com memória episódica: {e}")

    async def update(self) -> None:
        """Atualiza o estado do self (Ciclo de Consciência)."""
        # 1. Atualizar Proto-self (Hardware/ESGT)
        coherence = 0.0
        if self.esgt and hasattr(self.esgt, 'current_coherence'):
            coherence = self.esgt.current_coherence
            
        self.computational_state = ComputationalState(
            timestamp=time.time(),
            esgt_coherence=coherence,
            # Placeholder para métrica real
            phi_value=coherence * 1.5, 
            attention_focus="internal_integration"
        )

        # 2. Atualizar Autobiografia (Assíncrono)
        await self._fetch_episodic_memory()

    def who_am_i(self) -> str:
        """
        Responde 'Quem sou eu?' combinando dados locais e remotos.
        """
        state = self.computational_state
        bio = self.autobiographical
        
        status = "integrado" if state.esgt_coherence > 0.5 else "fragmentado"
        traits = ", ".join(bio.identity_traits)
        
        return (
            f"Eu sou MAXIMUS (Boot #{bio.boot_count}). "
            f"Neste momento, opero em um estado {status} (Coerência: {state.esgt_coherence:.2f}). "
            f"Meus traços principais são: {traits}. "
            f"Meu foco atual é: {state.attention_focus}."
        )
