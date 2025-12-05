"""
Test Suite for SymbioticSelfConcept
===================================

Tests the core exocortex symbiotic model.
"""

import pytest
from datetime import datetime
from typing import Generator, Dict, Any, Optional

from services.maximus_core_service.src.consciousness.exocortex.symbiotic_self import (
    SymbioticSelfConcept,
    DaimonPerception,
    TrustLevel,
    HumanIdentityModel,
    HumanValue,
    ValuePriority
)

class TestSymbioticSelf:
    """Test suite for SymbioticSelfConcept."""

    @pytest.fixture
    def symbiotic_self(self) -> Generator[SymbioticSelfConcept, None, None]:
        """Fixture for SymbioticSelfConcept instance."""
        yield SymbioticSelfConcept()

    def test_initialization(self, symbiotic_self: SymbioticSelfConcept) -> None:
        """Test initial state."""
        assert symbiotic_self.relationship_start is not None
        assert symbiotic_self.trust.level == 1
        assert symbiotic_self.trust.level_name == "Observador"
        assert symbiotic_self.human_identity is None

    def test_trust_dynamics(self) -> None:
        """Test trust levels."""
        trust = TrustLevel(level=1)
        assert trust.level_name == "Observador"
        assert not trust.can_confront()
        
        trust.level = 4
        assert trust.level_name == "Confrontador"
        assert trust.can_confront()

    def test_value_conflict_detection(self, symbiotic_self: SymbioticSelfConcept) -> None:
        """Test detection of value conflicts."""
        # Setup value
        value = HumanValue(
            name="Saúde",
            definition="Cuidar do corpo",
            priority=ValuePriority.IMPORTANT,
            examples_positive=["Gym"],
            examples_negative=["Fumar", "Comer junk food"],
            declared_at=datetime.now(),
            last_validated=datetime.now()
        )
        symbiotic_self.human_values.append(value)
        
        # Test conflict (case insensitive)
        conflict = symbiotic_self.detect_value_conflict("Vou comer JUNK FOOD")
        assert conflict is not None
        assert conflict["conflicting_value"] == "Saúde"
        assert conflict["priority"] == "IMPORTANT"
        
        # Test no conflict
        no_conflict = symbiotic_self.detect_value_conflict("Vou para a academia")
        assert no_conflict is None

    def test_report_generation(self, symbiotic_self: SymbioticSelfConcept) -> None:
        """Test symbiotic report generation."""
        # Setup identity
        symbiotic_self.human_identity = HumanIdentityModel(
            name="Juan",
            core_identity_statement="Eu sou um criador",
            non_negotiables=[],
            aspirational_self="",
            known_strengths=[],
            known_weaknesses=[],
            life_chapter_current=""
        )
        
        # Mock perception manually since update_perception raises error
        symbiotic_self.daimon_perception = DaimonPerception(
            perceived_emotional_state="neutro",
            perceived_energy_level=0.8,
            perceived_alignment=0.9,
            perceived_stress_level=0.2,
            confidence_in_perception=0.7,
            last_updated=datetime.now()
        )
        
        report = symbiotic_self.generate_symbiotic_report()
        assert "Eu sou um criador" in report
        assert "=== RELATÓRIO ===" in report
        assert "Estabilidade percebida" in report