"""
Exocortex Factory - Dependency Injection & Wiring
=================================================

Centraliza a criação e integração dos módulos do Exocórtex.
Garante que todos os componentes recebam suas dependências (Repositories, Gemini Client).
"""

import logging
from pathlib import Path
from typing import Optional

from datetime import datetime
from maximus_core_service.gemini_client import GeminiClient


from maximus_core_service.consciousness.exocortex.memory.repository import (
    ConstitutionRepository,
    ConfrontationRepository
)
from maximus_core_service.consciousness.exocortex.constitution_guardian import (
    ConstitutionGuardian,
    PersonalConstitution
)
from maximus_core_service.consciousness.exocortex.confrontation_engine import (
    ConfrontationEngine
)
from maximus_core_service.consciousness.exocortex.digital_thalamus import (
    DigitalThalamus
)
from maximus_core_service.consciousness.exocortex.impulse_inhibitor import (
    ImpulseInhibitor
)
from maximus_core_service.consciousness.exocortex.global_workspace import (
    GlobalWorkspace
)
from maximus_core_service.consciousness.exocortex.symbiotic_self import (
    SymbioticSelfConcept
)

logger = logging.getLogger(__name__)

class ExocortexFactory:
    """
    Factory Singleton para o subsistema Exocortex.
    """
    # pylint: disable=too-many-instance-attributes
    _instance: Optional['ExocortexFactory'] = None

    def __init__(self, data_dir: str):
        self.data_path = Path(data_dir)
        self.data_path.mkdir(parents=True, exist_ok=True)

        # 1. Configurar Infra (Files + LLM)
        self.const_repo = ConstitutionRepository(self.data_path)
        self.conf_repo = ConfrontationRepository(self.data_path)
        self.gemini_client = GeminiClient() # Config carregada internamente via env/settings

        # 2. Carregar Estado
        self.active_constitution = self.const_repo.load_constitution()
        logger.info("Constituição Carregada: %s", self.active_constitution.version)

        # Initializing Global Workspace
        self.workspace = GlobalWorkspace()

        # Initializing Constitution Guardian
        self.guardian = ConstitutionGuardian(
            constitution=PersonalConstitution(
                owner_id="user_001",
                last_updated=datetime.now(),
                core_principles=["Sovereignty", "Privacy", "Transparency", "Safety"],
                rules=[] # To be loaded from DB
            ),
            gemini_client=self.gemini_client,
            workspace=self.workspace
        )

        # Initializing Confrontation Engine
        self.confrontation_engine = ConfrontationEngine(
            gemini_client=self.gemini_client,
            workspace=self.workspace
        )

        # Initializing Thalamus
        self.thalamus = DigitalThalamus(
            gemini_client=self.gemini_client,
            workspace=self.workspace
        )

        # Initializing Impulse Inhibitor
        self.inhibitor = ImpulseInhibitor(
            gemini_client=self.gemini_client,
            workspace=self.workspace
        )

        # Initializing Symbiotic Self
        self.symbiotic_self = SymbioticSelfConcept()
        self.symbiotic_self.set_dependencies(
            gemini_client=self.gemini_client,
            workspace=self.workspace
        )

        # Wiring: Register Event Producers
        # (Future: module.set_workspace(self.workspace))

        logger.info("Exocortex Factory initialized successfully.")

    @classmethod
    def initialize(cls, data_dir: str = ".exocortex_data") -> 'ExocortexFactory':
        """Inicializa a factory singleton."""
        if cls._instance is None:
            cls._instance = cls(data_dir)
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'ExocortexFactory':
        """Retorna a instância da factory."""
        if cls._instance is None:
            raise RuntimeError("ExocortexFactory not initialized. Call initialize() first.")
        return cls._instance
