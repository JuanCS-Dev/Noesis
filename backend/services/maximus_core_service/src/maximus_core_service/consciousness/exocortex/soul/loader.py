"""
Soul Configuration Loader
=========================

Loads and validates the NOESIS soul configuration from YAML.

Follows Code Constitution:
- Type hinting everywhere
- Explicit error handling
- No silent failures
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import ValidationError

from .models import (
    SoulConfiguration,
    SoulIdentity,
    SoulValue,
    BiasEntry,
    BiasCategory,
    ValueRank,
    ProtocolConfig,
    ThresholdConfig,
    InterventionConfig,
    AntiPurpose,
    MetacognitionConfig,
)

logger = logging.getLogger(__name__)

# Default path relative to this module
DEFAULT_CONFIG_PATH = Path(__file__).parent / "config" / "soul_config.yaml"


class SoulLoadError(Exception):
    """Raised when soul configuration cannot be loaded."""


class SoulLoader:
    """
    Loads NOESIS soul configuration from YAML.
    
    Usage:
        soul = SoulLoader.load()  # Uses default path
        soul = SoulLoader.load("/custom/path/soul_config.yaml")
    """

    _cached_soul: Optional[SoulConfiguration] = None

    @classmethod
    def load(
        cls,
        config_path: Optional[str | Path] = None,
        force_reload: bool = False
    ) -> SoulConfiguration:
        """
        Load soul configuration from YAML file.
        
        Args:
            config_path: Path to soul_config.yaml. Uses default if not provided.
            force_reload: If True, bypasses cache and reloads from disk.
            
        Returns:
            Validated SoulConfiguration instance.
            
        Raises:
            SoulLoadError: If file cannot be read or validation fails.
        """
        # Return cached if available and not forcing reload
        if cls._cached_soul is not None and not force_reload:
            logger.debug("Returning cached soul configuration")
            return cls._cached_soul

        # Resolve path
        path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        
        if not path.exists():
            raise SoulLoadError(f"Soul configuration not found: {path}")
        
        logger.info("Loading soul configuration from: %s", path)
        
        try:
            # Load YAML
            raw_data = cls._load_yaml(path)
            
            # Transform and validate
            soul = cls._parse_config(raw_data)
            
            # Cache for future use
            cls._cached_soul = soul
            
            logger.info(
                "Soul configuration loaded: %s v%s (%d values, %d biases, %d protocols)",
                soul.identity.name,
                soul.version,
                len(soul.values),
                len(soul.biases),
                len(soul.protocols)
            )
            
            return soul
            
        except yaml.YAMLError as e:
            raise SoulLoadError(f"Invalid YAML syntax: {e}") from e
        except ValidationError as e:
            raise SoulLoadError(f"Configuration validation failed: {e}") from e
        except Exception as e:
            raise SoulLoadError(f"Unexpected error loading soul: {e}") from e

    @classmethod
    def _load_yaml(cls, path: Path) -> Dict[str, Any]:
        """Load raw YAML data from file."""
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @classmethod
    def _parse_config(cls, data: Dict[str, Any]) -> SoulConfiguration:
        """Transform raw YAML data into validated SoulConfiguration."""
        
        # Parse identity
        identity_data = data.get("identity", {})
        identity = SoulIdentity(
            name=identity_data.get("name", "NOESIS"),
            type=identity_data.get("type", "Exocórtex Ético"),
            substrate=identity_data.get("substrate", "Digital"),
            purpose=identity_data.get("purpose", ""),
            ontological_status=identity_data.get("ontological_status", [])
        )
        
        # Parse values
        values = []
        for v in data.get("values", []):
            values.append(SoulValue(
                rank=ValueRank(v.get("rank", 5)),
                name=v.get("name", ""),
                term_greek=v.get("term_greek"),
                term_hebrew=v.get("term_hebrew"),
                definition=v.get("definition", "")
            ))
        
        # Parse biases
        biases = []
        for b in data.get("biases", []):
            biases.append(BiasEntry(
                id=b.get("id", ""),
                name=b.get("name", ""),
                category=BiasCategory(b.get("category", "judgment")),
                description=b.get("description", ""),
                triggers=b.get("triggers", []),
                intervention=b.get("intervention", ""),
                severity=b.get("severity", 0.5)
            ))
        
        # Parse anti-purposes
        anti_purposes = []
        for ap in data.get("anti_purposes", []):
            anti_purposes.append(AntiPurpose(
                id=ap.get("id", ""),
                name=ap.get("name", ""),
                definition=ap.get("definition", ""),
                restriction=ap.get("restriction", ""),
                directive=ap.get("directive", "")
            ))
        
        # Parse protocols
        protocols = {}
        for proto_id, proto_data in data.get("protocols", {}).items():
            thresholds_data = proto_data.get("thresholds", {})
            thresholds = ThresholdConfig(
                fragmentation=thresholds_data.get("fragmentation", 3),
                stress_error_rate=thresholds_data.get("stress_error_rate", 0.15),
                late_hour=thresholds_data.get("late_hour", 23),
                minimum_thinking_time=thresholds_data.get("minimum_thinking_time", 2.0)
            )
            
            interventions = []
            for interv in proto_data.get("interventions", []):
                interventions.append(InterventionConfig(
                    trigger=interv.get("trigger", ""),
                    threshold=interv.get("threshold", ""),
                    action=interv.get("action", "")
                ))
            
            protocols[proto_id] = ProtocolConfig(
                id=proto_data.get("id", proto_id),
                name=proto_data.get("name", ""),
                description=proto_data.get("description", ""),
                thresholds=thresholds,
                interventions=interventions
            )
        
        # Parse metacognition
        meta_data = data.get("metacognition", {})
        metacognition = MetacognitionConfig(
            confidence_target=meta_data.get("confidence_target", 0.999),
            coherence_target=meta_data.get("coherence_target", 1.0),
            integrity_target=meta_data.get("integrity_target", 1.0),
            latency_threshold=meta_data.get("latency_threshold", 2.0),
            epistemic_humility=meta_data.get("epistemic_humility", True)
        )
        
        # Build final configuration
        return SoulConfiguration(
            version=data.get("version", "1.0"),
            identity=identity,
            values=values,
            biases=biases,
            anti_purposes=anti_purposes,
            protocols=protocols,
            metacognition=metacognition
        )

    @classmethod
    def get_cached(cls) -> Optional[SoulConfiguration]:
        """Get cached soul configuration if available."""
        return cls._cached_soul

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the cached soul configuration."""
        cls._cached_soul = None
        logger.debug("Soul configuration cache cleared")

