"""
Exocortex Factory - Dependency Injection & Wiring
=================================================

Centraliza a criação e integração dos módulos do Exocórtex.
Garante que todos os componentes recebam suas dependências (Repositories, Gemini Client).

NOESIS Soul Integration:
- Loads soul_config.yaml on startup
- Injects soul configuration into all exocortex modules
- Provides unified identity, values, and biases to the system
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
from maximus_core_service.consciousness.exocortex.soul import (
    SoulLoader,
    SoulConfiguration
)

logger = logging.getLogger(__name__)

class ExocortexFactory:
    """
    Factory Singleton para o subsistema Exocortex.
    
    Integrates NOESIS soul configuration into all exocortex modules,
    providing unified identity, values, biases, and protocols.
    """
    # pylint: disable=too-many-instance-attributes
    _instance: Optional['ExocortexFactory'] = None

    def __init__(self, data_dir: str):
        self.data_path = Path(data_dir)
        self.data_path.mkdir(parents=True, exist_ok=True)

        # ═══════════════════════════════════════════════════════════════════
        # 0. NOESIS SOUL - Load soul configuration first
        # ═══════════════════════════════════════════════════════════════════
        try:
            self.soul: SoulConfiguration = SoulLoader.load()
            logger.info(
                "🧠 NOESIS Soul Loaded: %s v%s",
                self.soul.identity.name,
                self.soul.version
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("⚠️  Failed to load soul config, using defaults: %s", e)
            self.soul = None  # type: ignore

        # ═══════════════════════════════════════════════════════════════════
        # 1. Configure Infrastructure (Files + LLM)
        # ═══════════════════════════════════════════════════════════════════
        self.const_repo = ConstitutionRepository(self.data_path)
        self.conf_repo = ConfrontationRepository(self.data_path)
        self.gemini_client = GeminiClient()

        # 2. Load persisted state
        self.active_constitution = self.const_repo.load_constitution()
        logger.info("Constituição Carregada: %s", self.active_constitution.version)

        # ═══════════════════════════════════════════════════════════════════
        # 3. Initialize Global Workspace
        # ═══════════════════════════════════════════════════════════════════
        self.workspace = GlobalWorkspace()

        # ═══════════════════════════════════════════════════════════════════
        # 4. Initialize Constitution Guardian (with soul values)
        # ═══════════════════════════════════════════════════════════════════
        # Build core principles from soul values if available
        core_principles = self._build_core_principles()
        
        self.guardian = ConstitutionGuardian(
            constitution=PersonalConstitution(
                owner_id="user_001",
                last_updated=datetime.now(),
                core_principles=core_principles,
                rules=[]  # To be loaded from DB
            ),
            gemini_client=self.gemini_client,
            workspace=self.workspace
        )
        
        # Inject soul values into guardian
        if self.soul:
            self.guardian.inject_principles(self.soul.values)

        # ═══════════════════════════════════════════════════════════════════
        # 5. Initialize Confrontation Engine
        # ═══════════════════════════════════════════════════════════════════
        self.confrontation_engine = ConfrontationEngine(
            gemini_client=self.gemini_client,
            workspace=self.workspace
        )

        # ═══════════════════════════════════════════════════════════════════
        # 6. Initialize Digital Thalamus
        # ═══════════════════════════════════════════════════════════════════
        self.thalamus = DigitalThalamus(
            gemini_client=self.gemini_client,
            workspace=self.workspace
        )

        # ═══════════════════════════════════════════════════════════════════
        # 7. Initialize Impulse Inhibitor (with soul biases)
        # ═══════════════════════════════════════════════════════════════════
        self.inhibitor = ImpulseInhibitor(
            gemini_client=self.gemini_client,
            workspace=self.workspace
        )
        
        # Inject bias catalog into inhibitor
        if self.soul:
            self.inhibitor.inject_biases(self.soul.biases)

        # ═══════════════════════════════════════════════════════════════════
        # 8. Initialize Symbiotic Self (with full soul)
        # ═══════════════════════════════════════════════════════════════════
        self.symbiotic_self = SymbioticSelfConcept()
        self.symbiotic_self.set_dependencies(
            gemini_client=self.gemini_client,
            workspace=self.workspace
        )
        
        # Inject complete soul configuration
        if self.soul:
            self.symbiotic_self.inject_soul(self.soul)

        # Log successful initialization
        soul_status = f"with NOESIS soul v{self.soul.version}" if self.soul else "without soul config"
        logger.info("✅ Exocortex Factory initialized successfully (%s).", soul_status)

    def _build_core_principles(self) -> list[str]:
        """Build core principles list from soul values."""
        if self.soul and self.soul.values:
            return [
                f"{v.name}: {v.definition}"
                for v in sorted(self.soul.values, key=lambda x: x.rank)
            ]
        # Fallback to defaults
        return ["Sovereignty", "Privacy", "Transparency", "Safety"]

    def get_soul(self) -> Optional[SoulConfiguration]:
        """Get the loaded soul configuration."""
        return self.soul

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
