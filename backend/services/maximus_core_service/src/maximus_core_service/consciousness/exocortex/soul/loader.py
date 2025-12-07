"""
Soul Configuration Loader
=========================

Loads and validates the NOESIS soul configuration from YAML.

Follows Code Constitution:
- Type hinting everywhere
- Explicit error handling
- No silent failures
"""
# pylint: disable=no-member

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

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
        if cls._cached_soul is not None and not force_reload:
            logger.debug("Returning cached soul configuration")
            return cls._cached_soul

        path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

        if not path.exists():
            raise SoulLoadError(f"Soul configuration not found: {path}")

        logger.info("Loading soul configuration from: %s", path)

        try:
            raw_data = cls._load_yaml(path)
            soul = cls._parse_config(raw_data)
            cls._cached_soul = soul

            logger.info(
                "Soul loaded: %s v%s (%d values, %d biases, %d protocols)",
                soul.identity.name, soul.version,
                len(soul.values), len(soul.biases), len(soul.protocols)
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
        return SoulConfiguration(
            version=data.get("version", "1.0"),
            identity=cls._parse_identity(data.get("identity", {})),
            values=cls._parse_values(data.get("values", [])),
            biases=cls._parse_biases(data.get("biases", [])),
            anti_purposes=cls._parse_anti_purposes(data.get("anti_purposes", [])),
            protocols=cls._parse_protocols(data.get("protocols", {})),
            metacognition=cls._parse_metacognition(data.get("metacognition", {}))
        )

    @classmethod
    def _parse_identity(cls, data: Dict[str, Any]) -> SoulIdentity:
        """Parse identity section."""
        return SoulIdentity(
            name=data.get("name", "NOESIS"),
            type=data.get("type", "Exocórtex Ético"),
            substrate=data.get("substrate", "Digital"),
            purpose=data.get("purpose", ""),
            ontological_status=data.get("ontological_status", [])
        )

    @classmethod
    def _parse_values(cls, data: List[Dict[str, Any]]) -> List[SoulValue]:
        """Parse values section."""
        return [
            SoulValue(
                rank=ValueRank(v.get("rank", 5)),
                name=v.get("name", ""),
                term_greek=v.get("term_greek"),
                term_hebrew=v.get("term_hebrew"),
                definition=v.get("definition", "")
            )
            for v in data
        ]

    @classmethod
    def _parse_biases(cls, data: List[Dict[str, Any]]) -> List[BiasEntry]:
        """Parse biases section."""
        return [
            BiasEntry(
                id=b.get("id", ""),
                name=b.get("name", ""),
                category=BiasCategory(b.get("category", "judgment")),
                description=b.get("description", ""),
                triggers=b.get("triggers", []),
                intervention=b.get("intervention", ""),
                severity=b.get("severity", 0.5)
            )
            for b in data
        ]

    @classmethod
    def _parse_anti_purposes(cls, data: List[Dict[str, Any]]) -> List[AntiPurpose]:
        """Parse anti-purposes section."""
        return [
            AntiPurpose(
                id=ap.get("id", ""),
                name=ap.get("name", ""),
                definition=ap.get("definition", ""),
                restriction=ap.get("restriction", ""),
                directive=ap.get("directive", "")
            )
            for ap in data
        ]

    @classmethod
    def _parse_protocols(
        cls, data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, ProtocolConfig]:
        """Parse protocols section."""
        protocols = {}
        for proto_id, proto_data in data.items():
            thresholds_data = proto_data.get("thresholds", {})
            protocols[proto_id] = ProtocolConfig(
                id=proto_data.get("id", proto_id),
                name=proto_data.get("name", ""),
                description=proto_data.get("description", ""),
                thresholds=ThresholdConfig(
                    fragmentation=thresholds_data.get("fragmentation", 3),
                    stress_error_rate=thresholds_data.get("stress_error_rate", 0.15),
                    late_hour=thresholds_data.get("late_hour", 23),
                    minimum_thinking_time=thresholds_data.get(
                        "minimum_thinking_time", 2.0
                    )
                ),
                interventions=[
                    InterventionConfig(
                        trigger=i.get("trigger", ""),
                        threshold=i.get("threshold", ""),
                        action=i.get("action", "")
                    )
                    for i in proto_data.get("interventions", [])
                ]
            )
        return protocols

    @classmethod
    def _parse_metacognition(cls, data: Dict[str, Any]) -> MetacognitionConfig:
        """Parse metacognition section."""
        return MetacognitionConfig(
            confidence_target=data.get("confidence_target", 0.999),
            coherence_target=data.get("coherence_target", 1.0),
            integrity_target=data.get("integrity_target", 1.0),
            latency_threshold=data.get("latency_threshold", 2.0),
            epistemic_humility=data.get("epistemic_humility", True)
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
