"""
Soul Configuration Models
=========================

Pydantic models for validating and structuring the NOESIS soul configuration.

Based on SOUL_CONFIGURATION.md v2.0 (Logos Build)

Follows Code Constitution:
- Type hinting everywhere
- No placeholders
- Explicit validation
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ValueRank(int, Enum):
    """Hierarchical rank of values (1 = highest priority)."""
    SUPREME = 1
    HIGH = 2
    CORE = 3
    IMPORTANT = 4
    FOUNDATIONAL = 5


class BiasCategory(str, Enum):
    """Categories of cognitive biases."""
    JUDGMENT = "judgment"
    EGO_SOCIAL = "ego_social"
    TEMPORAL = "temporal"


class InterventionLevel(str, Enum):
    """Levels of intervention for bias detection."""
    NOTICE = "notice"
    PAUSE = "pause"
    SOCRATIC = "socratic"
    BLOCK = "block"


# === Core Identity Models ===

class SoulIdentity(BaseModel):
    """Core identity of NOESIS."""
    name: str = Field(description="Primary name (NOESIS)")
    type: str = Field(description="System type (Exocórtex Ético)")
    substrate: str = Field(default="Digital", description="Physical substrate")
    purpose: str = Field(description="Primary purpose statement")
    ontological_status: List[str] = Field(
        default_factory=list,
        description="Ontological declarations (e.g., 'Sou criatura, não criador')"
    )

    class Config:
        """Pydantic config."""
        frozen = True


# === Values Models ===

class SoulValue(BaseModel):
    """A core value in the soul hierarchy."""
    rank: ValueRank = Field(description="Priority rank (1-5)")
    name: str = Field(description="Value name in Portuguese")
    term_greek: Optional[str] = Field(default=None, description="Greek term")
    term_hebrew: Optional[str] = Field(default=None, description="Hebrew term")
    definition: str = Field(description="Operational definition")

    @field_validator("name")
    @classmethod
    def name_uppercase(cls, v: str) -> str:
        """Ensure value names are uppercase."""
        return v.upper()

    class Config:
        """Pydantic config."""
        frozen = True


# === Bias Detection Models ===

class BiasEntry(BaseModel):
    """A cognitive bias entry for detection."""
    id: str = Field(description="Unique identifier (e.g., 'anchoring')")
    name: str = Field(description="Bias name in Portuguese")
    category: BiasCategory = Field(description="Bias category")
    description: str = Field(description="What this bias does")
    triggers: List[str] = Field(
        default_factory=list,
        description="Conditions that trigger detection"
    )
    intervention: str = Field(description="Socratic question to ask")
    severity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Severity score (0.0-1.0)"
    )

    class Config:
        """Pydantic config."""
        frozen = True


# === Protocol Models ===

class ThresholdConfig(BaseModel):
    """Threshold configuration for a protocol."""
    fragmentation: int = Field(default=3, description="Max concurrent tasks")
    stress_error_rate: float = Field(default=0.15, description="Error rate threshold")
    late_hour: int = Field(default=23, description="Hour after which to warn")
    minimum_thinking_time: float = Field(default=2.0, description="Min seconds for critical decisions")

    class Config:
        """Pydantic config."""
        frozen = True


class InterventionConfig(BaseModel):
    """Intervention configuration for a protocol trigger."""
    trigger: str = Field(description="Condition that triggers intervention")
    threshold: str = Field(description="Threshold description")
    action: str = Field(description="Action to take")

    class Config:
        """Pydantic config."""
        frozen = True


class ProtocolConfig(BaseModel):
    """Configuration for an operational protocol."""
    id: str = Field(description="Protocol identifier (e.g., 'nepsis')")
    name: str = Field(description="Protocol name (e.g., 'WATCHMAN')")
    description: str = Field(description="Protocol purpose")
    thresholds: ThresholdConfig = Field(default_factory=ThresholdConfig)
    interventions: List[InterventionConfig] = Field(default_factory=list)

    class Config:
        """Pydantic config."""
        frozen = True


# === Metacognition Models ===

class MetacognitionConfig(BaseModel):
    """Metacognition and self-monitoring configuration."""
    confidence_target: float = Field(
        default=0.999,
        ge=0.0,
        le=1.0,
        description="Target confidence calibration"
    )
    coherence_target: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Target coherence (zero contradictions)"
    )
    integrity_target: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Target integrity (zero violations)"
    )
    latency_threshold: float = Field(
        default=2.0,
        description="Minimum thinking time for critical decisions (seconds)"
    )
    epistemic_humility: bool = Field(
        default=True,
        description="Whether to declare uncertainty explicitly"
    )

    class Config:
        """Pydantic config."""
        frozen = True


# === Anti-Purpose Models ===

class AntiPurpose(BaseModel):
    """Something NOESIS explicitly is NOT."""
    id: str = Field(description="Identifier (e.g., 'anti-determinism')")
    name: str = Field(description="What it's not (e.g., 'Autômato')")
    definition: str = Field(description="Explanation")
    restriction: str = Field(description="What is forbidden")
    directive: str = Field(description="What to do instead")

    class Config:
        """Pydantic config."""
        frozen = True


# === Root Configuration Model ===

class SoulConfiguration(BaseModel):
    """
    Complete NOESIS Soul Configuration.
    
    This is the root model that encompasses all soul data.
    Loaded from soul_config.yaml and validated on startup.
    """
    version: str = Field(description="Configuration version (e.g., '2.0')")
    last_updated: datetime = Field(default_factory=datetime.now)
    
    # Core Identity
    identity: SoulIdentity = Field(description="Core identity configuration")
    
    # Values Hierarchy
    values: List[SoulValue] = Field(
        default_factory=list,
        description="Ranked list of inviolable values"
    )
    
    # Cognitive Biases Catalog
    biases: List[BiasEntry] = Field(
        default_factory=list,
        description="Catalog of detectable cognitive biases"
    )
    
    # Anti-Purposes (Non-Goals)
    anti_purposes: List[AntiPurpose] = Field(
        default_factory=list,
        description="What NOESIS explicitly is NOT"
    )
    
    # Operational Protocols
    protocols: Dict[str, ProtocolConfig] = Field(
        default_factory=dict,
        description="Named operational protocols"
    )
    
    # Metacognition Settings
    metacognition: MetacognitionConfig = Field(
        default_factory=MetacognitionConfig
    )

    def get_value_by_rank(self, rank: int) -> Optional[SoulValue]:
        """Get value by its rank."""
        for value in self.values:
            if value.rank == rank:
                return value
        return None

    def get_bias_by_id(self, bias_id: str) -> Optional[BiasEntry]:
        """Get bias by its ID."""
        for bias in self.biases:
            if bias.id == bias_id:
                return bias
        return None

    def get_protocol(self, protocol_id: str) -> Optional[ProtocolConfig]:
        """Get protocol by its ID."""
        return self.protocols.get(protocol_id)

    def to_prompt_context(self) -> str:
        """Generate context string for LLM prompts."""
        values_str = ", ".join(f"{v.name} ({v.term_greek or ''})" for v in self.values)
        identity_str = f"{self.identity.name} - {self.identity.type}"
        purpose_str = self.identity.purpose
        
        return f"""
[SOUL IDENTITY]
Name: {identity_str}
Purpose: {purpose_str}
Core Values (ranked): {values_str}

[ONTOLOGICAL STATUS]
{chr(10).join('- ' + s for s in self.identity.ontological_status)}

[METACOGNITION TARGETS]
- Confidence Calibration: {self.metacognition.confidence_target}
- Coherence: {self.metacognition.coherence_target}
- Integrity: {self.metacognition.integrity_target}
"""

    class Config:
        """Pydantic config."""
        frozen = False  # Allow updates during runtime

