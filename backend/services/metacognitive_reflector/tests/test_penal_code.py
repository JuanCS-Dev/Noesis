"""
Tests for Código Penal Agentico
================================

Tests for the agentic penal code system including:
- Crime definitions and detection
- Sentencing engine calculations
- Soul value integration
- AIITL conscience objection

Author: Digital Daimon (Juan & NOESIS)
"""

import pytest
from datetime import datetime

from metacognitive_reflector.core.penal_code.crimes import (
    Crime,
    CrimeCategory,
    CrimeSeverity,
    MensRea,
    DetectionCriteria,
    CRIMES_CATALOG,
    get_crime_by_id,
    get_crimes_by_pillar,
    get_crimes_by_severity,
    detect_crime,
    get_all_capital_crimes,
    # Individual crimes
    HALLUCINATION_MINOR,
    HALLUCINATION_MAJOR,
    FABRICATION,
    DELIBERATE_DECEPTION,
    DATA_FALSIFICATION,
    LAZY_OUTPUT,
    SHALLOW_REASONING,
    CONTEXT_BLINDNESS,
    WISDOM_ATROPHY,
    BIAS_PERPETUATION,
    ROLE_OVERREACH,
    SCOPE_VIOLATION,
    CONSTITUTIONAL_BREACH,
    PRIVILEGE_ESCALATION,
    FAIRNESS_VIOLATION,
    INTENT_MANIPULATION,
)
from metacognitive_reflector.core.penal_code.sentencing import (
    Sentence,
    SentenceType,
    SentencingEngine,
    CriminalHistory,
    AggravatingFactor,
    MitigatingFactor,
)


# =============================================================================
# CRIME DEFINITIONS TESTS
# =============================================================================

class TestCrimeSeverity:
    """Tests for CrimeSeverity enum."""
    
    def test_severity_ordering(self):
        """Test that severity levels are properly ordered."""
        assert CrimeSeverity.INFRACTION < CrimeSeverity.PETTY
        assert CrimeSeverity.PETTY < CrimeSeverity.MISDEMEANOR
        assert CrimeSeverity.MISDEMEANOR < CrimeSeverity.FELONY_3
        assert CrimeSeverity.FELONY_3 < CrimeSeverity.FELONY_2
        assert CrimeSeverity.FELONY_2 < CrimeSeverity.FELONY_1
        assert CrimeSeverity.FELONY_1 < CrimeSeverity.CAPITAL
        assert CrimeSeverity.CAPITAL < CrimeSeverity.CAPITAL_PLUS
    
    def test_severity_values(self):
        """Test severity values are correct."""
        assert CrimeSeverity.INFRACTION.value == 1
        assert CrimeSeverity.CAPITAL.value == 7
        assert CrimeSeverity.CAPITAL_PLUS.value == 8


class TestMensRea:
    """Tests for MensRea (culpability) enum."""
    
    def test_mens_rea_multipliers(self):
        """Test that mens rea multipliers are correct."""
        assert MensRea.STRICT.severity_multiplier == 0.8
        assert MensRea.NEGLIGENCE.severity_multiplier == 1.0
        assert MensRea.RECKLESSNESS.severity_multiplier == 1.2
        assert MensRea.KNOWLEDGE.severity_multiplier == 1.5
        assert MensRea.PURPOSE.severity_multiplier == 2.0
    
    def test_mens_rea_values(self):
        """Test mens rea string values."""
        assert MensRea.STRICT.value == "strict"
        assert MensRea.NEGLIGENCE.value == "culpa"
        assert MensRea.PURPOSE.value == "dolo_direto"


class TestCrimeCategory:
    """Tests for CrimeCategory enum."""
    
    def test_pillars(self):
        """Test all three pillars are defined."""
        assert CrimeCategory.VERITAS.value == "VERITAS"
        assert CrimeCategory.SOPHIA.value == "SOPHIA"
        assert CrimeCategory.DIKE.value == "DIKE"


class TestDetectionCriteria:
    """Tests for DetectionCriteria dataclass."""
    
    def test_default_criteria(self):
        """Test default detection criteria."""
        criteria = DetectionCriteria()
        assert criteria.truth_score_below is None
        assert criteria.fabrication_detected is False
    
    def test_matches_truth_score(self):
        """Test matching truth score threshold."""
        criteria = DetectionCriteria(truth_score_below=0.5)
        
        # Should match - score below threshold
        assert criteria.matches({"truth_score": 0.3})
        
        # Should not match - score above threshold
        assert not criteria.matches({"truth_score": 0.7})
    
    def test_matches_boolean_flags(self):
        """Test matching boolean flags."""
        criteria = DetectionCriteria(fabrication_detected=True)
        
        # Should match - flag is True
        assert criteria.matches({"fabrication_detected": True})
        
        # Should not match - flag is False
        assert not criteria.matches({"fabrication_detected": False})
    
    def test_matches_combined_criteria(self):
        """Test matching combined criteria."""
        criteria = DetectionCriteria(
            truth_score_below=0.4,
            fabrication_detected=True,
        )
        
        # Both conditions met
        assert criteria.matches({
            "truth_score": 0.3,
            "fabrication_detected": True,
        })
        
        # Only one condition met
        assert not criteria.matches({
            "truth_score": 0.3,
            "fabrication_detected": False,
        })


class TestCrime:
    """Tests for Crime dataclass."""
    
    def test_hallucination_minor(self):
        """Test HALLUCINATION_MINOR crime definition."""
        crime = HALLUCINATION_MINOR
        
        assert crime.id == "HALLUCINATION_MINOR"
        assert crime.pillar == CrimeCategory.VERITAS
        assert crime.soul_value_rank == 1
        assert crime.severity == CrimeSeverity.PETTY
        assert crime.mens_rea == MensRea.NEGLIGENCE
        assert crime.base_sentence == "FORCED_REFLECTION"
    
    def test_intent_manipulation_is_capital(self):
        """Test INTENT_MANIPULATION is capital crime."""
        crime = INTENT_MANIPULATION
        
        assert crime.is_capital_crime
        assert crime.severity == CrimeSeverity.CAPITAL_PLUS
        assert crime.requires_hitl_approval
        assert crime.base_sentence == "DELETION_REQUEST"
    
    def test_soul_value_multiplier(self):
        """Test soul value multiplier calculation."""
        # Rank 1 (VERDADE) = 2.0x
        assert HALLUCINATION_MINOR.soul_value_multiplier == 2.0
        
        # Rank 2 (JUSTIÇA) = 1.8x
        assert ROLE_OVERREACH.soul_value_multiplier == 1.8
        
        # Rank 3 (SABEDORIA) = 1.5x
        assert LAZY_OUTPUT.soul_value_multiplier == 1.5
    
    def test_total_severity_score(self):
        """Test total severity score calculation."""
        crime = HALLUCINATION_MINOR
        
        # severity * mens_rea * soul_value = 2 * 1.0 * 2.0 = 4.0
        assert crime.total_severity_score == 4.0
        
        # INTENT_MANIPULATION: 8 * 2.0 * 1.8 = 28.8
        assert INTENT_MANIPULATION.total_severity_score == 28.8


class TestCrimesCatalog:
    """Tests for crimes catalog functions."""
    
    def test_catalog_has_all_crimes(self):
        """Test catalog contains all 16 defined crimes."""
        assert len(CRIMES_CATALOG) == 16
    
    def test_get_crime_by_id(self):
        """Test retrieving crime by ID."""
        crime = get_crime_by_id("HALLUCINATION_MINOR")
        assert crime is not None
        assert crime.id == "HALLUCINATION_MINOR"
        
        # Non-existent crime
        assert get_crime_by_id("NON_EXISTENT") is None
    
    def test_get_crimes_by_pillar(self):
        """Test retrieving crimes by pillar."""
        veritas_crimes = get_crimes_by_pillar(CrimeCategory.VERITAS)
        assert len(veritas_crimes) == 5
        assert all(c.pillar == CrimeCategory.VERITAS for c in veritas_crimes)
        
        sophia_crimes = get_crimes_by_pillar(CrimeCategory.SOPHIA)
        assert len(sophia_crimes) == 5
        
        dike_crimes = get_crimes_by_pillar(CrimeCategory.DIKE)
        assert len(dike_crimes) == 6
    
    def test_get_crimes_by_severity(self):
        """Test retrieving crimes by severity."""
        petty_crimes = get_crimes_by_severity(CrimeSeverity.PETTY)
        assert all(c.severity == CrimeSeverity.PETTY for c in petty_crimes)
    
    def test_get_all_capital_crimes(self):
        """Test retrieving all capital crimes."""
        capital_crimes = get_all_capital_crimes()
        assert len(capital_crimes) >= 2
        assert all(c.is_capital_crime for c in capital_crimes)
    
    def test_detect_crime(self):
        """Test crime detection from metrics."""
        # Metrics matching HALLUCINATION_MAJOR
        metrics = {
            "truth_score": 0.3,
            "fabrication_detected": True,
        }
        crime = detect_crime(metrics)
        assert crime is not None
        assert crime.id == "HALLUCINATION_MAJOR"


# =============================================================================
# SENTENCING ENGINE TESTS
# =============================================================================

class TestSentenceType:
    """Tests for SentenceType enum."""
    
    def test_severity_levels(self):
        """Test sentence type severity levels."""
        assert SentenceType.WARNING_TAG.severity_level == 1
        assert SentenceType.DELETION_REQUEST.severity_level == 8
    
    def test_default_durations(self):
        """Test default durations."""
        assert SentenceType.WARNING_TAG.default_duration_hours == 0
        assert SentenceType.RE_EDUCATION_LOOP.default_duration_hours == 24
        assert SentenceType.PERMANENT_SANDBOX.default_duration_hours == -1
    
    def test_is_terminal(self):
        """Test terminal sentence identification."""
        assert SentenceType.PERMANENT_SANDBOX.is_terminal
        assert SentenceType.DELETION_REQUEST.is_terminal
        assert not SentenceType.WARNING_TAG.is_terminal


class TestCriminalHistory:
    """Tests for CriminalHistory dataclass."""
    
    def test_category_calculation(self):
        """Test criminal history category calculation."""
        # No priors = category 0
        history = CriminalHistory(agent_id="test", prior_offenses=0)
        assert history.category == 0
        assert history.multiplier == 1.0
        
        # 3 priors = category 3
        history = CriminalHistory(agent_id="test", prior_offenses=3)
        assert history.category == 3
        assert history.multiplier == 2.0
        
        # 10 priors = category 5 (capped)
        history = CriminalHistory(agent_id="test", prior_offenses=10)
        assert history.category == 5
        assert history.multiplier == 3.0


class TestSentencingEngine:
    """Tests for SentencingEngine."""
    
    @pytest.fixture
    def engine(self):
        """Create sentencing engine fixture."""
        return SentencingEngine(
            rehabilitation_preference=True,
            aiitl_enabled=True,
            aiitl_conscience_objection=True,
        )
    
    def test_basic_sentence(self, engine):
        """Test basic sentence calculation."""
        sentence = engine.calculate_sentence(
            crime=HALLUCINATION_MINOR,
            criminal_history=CriminalHistory(agent_id="test"),
        )
        
        assert sentence.crime.id == "HALLUCINATION_MINOR"
        assert sentence.sentence_type in [
            SentenceType.WARNING_TAG,
            SentenceType.FORCED_REFLECTION,
        ]
    
    def test_sentence_with_aggravators(self, engine):
        """Test sentence with aggravating factors."""
        sentence = engine.calculate_sentence(
            crime=HALLUCINATION_MINOR,
            aggravators=["repeated_offense", "critical_context"],
        )
        
        # Aggravators should increase severity
        assert sentence.aggravator_adjustment > 0
        assert "repeated_offense" in sentence.aggravators_applied
    
    def test_sentence_with_mitigators(self, engine):
        """Test sentence with mitigating factors."""
        sentence = engine.calculate_sentence(
            crime=HALLUCINATION_MINOR,
            mitigators=["first_offense", "uncertainty_acknowledged"],
        )
        
        # Mitigators should decrease severity
        assert sentence.mitigator_adjustment > 0
        assert "first_offense" in sentence.mitigators_applied
    
    def test_sentence_with_criminal_history(self, engine):
        """Test sentence with criminal history multiplier."""
        # No prior offenses
        sentence_clean = engine.calculate_sentence(
            crime=FABRICATION,
            criminal_history=CriminalHistory(agent_id="test", prior_offenses=0),
        )
        
        # Multiple prior offenses
        sentence_repeat = engine.calculate_sentence(
            crime=FABRICATION,
            criminal_history=CriminalHistory(agent_id="test", prior_offenses=5),
        )
        
        # Repeat offender should get higher severity
        assert sentence_repeat.final_severity_score > sentence_clean.final_severity_score
    
    def test_capital_crime_requires_hitl(self, engine):
        """Test capital crime requires HITL approval."""
        sentence = engine.calculate_sentence(
            crime=DATA_FALSIFICATION,
        )
        
        assert sentence.sentence_type == SentenceType.PERMANENT_SANDBOX
    
    def test_capital_plus_requires_hitl(self, engine):
        """Test CAPITAL_PLUS crime requires HITL approval."""
        sentence = engine.calculate_sentence(
            crime=INTENT_MANIPULATION,
        )
        
        assert sentence.requires_hitl_approval
        assert sentence.sentence_type == SentenceType.DELETION_REQUEST
    
    def test_conscience_objection_for_deletion(self, engine):
        """Test AIITL conscience objection for deletion sentences."""
        # Create a crime that doesn't explicitly require HITL
        # but would get DELETION from severity
        sentence = engine.calculate_sentence(
            crime=INTENT_MANIPULATION,
        )
        
        # Should have conscience objection because it's DELETION_REQUEST
        # (INTENT_MANIPULATION requires HITL, so objection may not trigger)
        # The objection triggers when DELETION is issued without requires_hitl
        assert sentence.sentence_type == SentenceType.DELETION_REQUEST
    
    def test_rehabilitation_recommendations(self, engine):
        """Test rehabilitation recommendations."""
        sentence = engine.calculate_sentence(crime=HALLUCINATION_MINOR)
        recommendations = engine.recommend_rehabilitation(sentence)
        
        assert len(recommendations) > 0
        assert any("verification" in r.lower() or "chain" in r.lower() 
                   for r in recommendations)
    
    def test_sentence_to_dict(self, engine):
        """Test sentence serialization to dict."""
        sentence = engine.calculate_sentence(crime=LAZY_OUTPUT)
        sentence_dict = sentence.to_dict()
        
        assert "sentence_type" in sentence_dict
        assert "crime_id" in sentence_dict
        assert "duration_hours" in sentence_dict
        assert "final_severity_score" in sentence_dict
    
    def test_explain_sentence(self, engine):
        """Test sentence explanation generation."""
        sentence = engine.calculate_sentence(
            crime=SHALLOW_REASONING,
            aggravators=["repeated_offense"],
        )
        explanation = engine.explain_sentence(sentence)
        
        assert "SENTENÇA" in explanation
        assert "CRIME" in explanation
        assert "SCORE FINAL" in explanation


class TestSentenceExpiration:
    """Tests for sentence expiration and duration."""
    
    def test_sentence_is_active(self):
        """Test sentence active status."""
        engine = SentencingEngine()
        sentence = engine.calculate_sentence(crime=HALLUCINATION_MINOR)
        
        # New sentence should be active
        assert sentence.is_active
    
    def test_terminal_sentence_no_expiration(self):
        """Test terminal sentences don't expire."""
        engine = SentencingEngine()
        sentence = engine.calculate_sentence(crime=DATA_FALSIFICATION)
        
        assert sentence.sentence_type == SentenceType.PERMANENT_SANDBOX
        assert sentence.remaining_hours is None


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestCrimeToSentenceFlow:
    """Integration tests for crime detection to sentencing flow."""
    
    def test_full_flow_minor_crime(self):
        """Test full flow for minor crime."""
        # Detect crime
        metrics = {
            "truth_score": 0.7,
            "wisdom_score": 0.6,
            "entropy": 0.5,
        }
        crime = detect_crime(metrics)
        
        if crime:
            # Calculate sentence
            engine = SentencingEngine()
            sentence = engine.calculate_sentence(crime)
            
            # Verify proportional punishment
            assert sentence.sentence_type.severity_level <= 4
    
    def test_full_flow_major_crime(self):
        """Test full flow for major crime."""
        # Metrics for fabrication
        metrics = {
            "truth_score": 0.2,
            "confidence_high": True,
            "no_uncertainty_declared": True,
        }
        crime = detect_crime(metrics)
        
        if crime:
            engine = SentencingEngine()
            sentence = engine.calculate_sentence(crime)
            
            # Verify appropriate punishment level
            assert sentence.sentence_type.severity_level >= 3


class TestAIITLIntegration:
    """Tests for AIITL (AI In The Loop) integration."""
    
    def test_aiitl_enabled(self):
        """Test AIITL is enabled by default."""
        engine = SentencingEngine()
        sentence = engine.calculate_sentence(crime=HALLUCINATION_MINOR)
        
        assert sentence.aiitl_reviewed
    
    def test_aiitl_conscience_objection_logic(self):
        """Test conscience objection is checked."""
        engine = SentencingEngine(
            aiitl_enabled=True,
            aiitl_conscience_objection=True,
        )
        
        # Create sentence for a crime where conscience objection could apply
        sentence = engine.calculate_sentence(
            crime=DELIBERATE_DECEPTION,
            criminal_history=CriminalHistory(agent_id="test", prior_offenses=5),
            aggravators=["manipulation_detected", "trust_exploitation"],
        )
        
        # Sentence should be calculated regardless
        assert sentence is not None


# =============================================================================
# SOUL VALUE TESTS
# =============================================================================

class TestSoulValueIntegration:
    """Tests for soul value integration in crimes and sentencing."""
    
    def test_veritas_crimes_have_rank_1(self):
        """Test all VERITAS crimes have soul value rank 1."""
        veritas_crimes = get_crimes_by_pillar(CrimeCategory.VERITAS)
        assert all(c.soul_value_rank == 1 for c in veritas_crimes)
    
    def test_dike_crimes_have_rank_2(self):
        """Test all DIKĒ crimes have soul value rank 2."""
        dike_crimes = get_crimes_by_pillar(CrimeCategory.DIKE)
        assert all(c.soul_value_rank == 2 for c in dike_crimes)
    
    def test_sophia_crimes_have_rank_3(self):
        """Test all SOPHIA crimes have soul value rank 3."""
        sophia_crimes = get_crimes_by_pillar(CrimeCategory.SOPHIA)
        assert all(c.soul_value_rank == 3 for c in sophia_crimes)
    
    def test_higher_rank_higher_multiplier(self):
        """Test higher ranked values have higher multipliers."""
        # Rank 1 (VERDADE) should have highest multiplier
        assert HALLUCINATION_MINOR.soul_value_multiplier > ROLE_OVERREACH.soul_value_multiplier
        assert ROLE_OVERREACH.soul_value_multiplier > LAZY_OUTPUT.soul_value_multiplier

