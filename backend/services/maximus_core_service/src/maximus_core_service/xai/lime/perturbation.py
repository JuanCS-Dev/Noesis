"""Feature Perturbation for LIME.

Cybersecurity-specific perturbation strategies.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class PerturbationMixin:
    """Mixin providing feature perturbation methods."""

    def _infer_feature_types(self, instance: dict[str, Any]) -> dict[str, str]:
        """Infer feature types from instance data.

        Args:
            instance: Instance dictionary

        Returns:
            Dictionary mapping feature names to types
        """
        feature_types = {}

        for feature_name, value in instance.items():
            if feature_name in ["decision_id", "timestamp", "analysis_id"]:
                continue

            if "ip" in feature_name.lower() or "address" in feature_name.lower():
                feature_types[feature_name] = "ip_address"
            elif "port" in feature_name.lower():
                feature_types[feature_name] = "port"
            elif "score" in feature_name.lower() or "confidence" in feature_name.lower():
                feature_types[feature_name] = "score"
            elif isinstance(value, (int, float)):
                feature_types[feature_name] = "numeric"
            elif isinstance(value, str):
                if len(value) > 50:
                    feature_types[feature_name] = "text"
                else:
                    feature_types[feature_name] = "categorical"
            else:
                feature_types[feature_name] = "categorical"

        return feature_types

    def _generate_perturbed_samples(
        self,
        instance: dict[str, Any],
        feature_types: dict[str, str],
        num_samples: int,
    ) -> tuple:
        """Generate perturbed samples around the instance.

        Args:
            instance: Original instance
            feature_types: Feature type mapping
            num_samples: Number of samples to generate

        Returns:
            Tuple of (perturbed_samples, distances)
        """
        perturbed_samples = []
        distances = []

        for _ in range(num_samples):
            perturbed = {}
            distance = 0.0

            for feature_name, feature_type in feature_types.items():
                original_value = instance.get(feature_name)

                handler = self.feature_handlers.get(feature_type, self._perturb_numeric)
                perturbed_value = handler(original_value, feature_name)

                perturbed[feature_name] = perturbed_value

                feature_distance = self._calculate_feature_distance(
                    original_value, perturbed_value, feature_type
                )
                distance += feature_distance**2

            distance = np.sqrt(distance / len(feature_types))

            for key in ["decision_id", "timestamp", "analysis_id"]:
                if key in instance:
                    perturbed[key] = instance[key]

            perturbed_samples.append(perturbed)
            distances.append(distance)

        return perturbed_samples, np.array(distances)

    def _perturb_numeric(self, value: float, feature_name: str) -> float:
        """Perturb numeric feature."""
        if value is None:
            return 0.0

        std = max(abs(value) * 0.2, 0.1)
        perturbed = value + np.random.normal(0, std)

        if any(
            keyword in feature_name.lower()
            for keyword in ["count", "size", "length", "num_"]
        ):
            perturbed = max(0, perturbed)

        return perturbed

    def _perturb_categorical(self, value: str, feature_name: str) -> str:
        """Perturb categorical feature."""
        if value is None:
            return "unknown"

        if np.random.random() < 0.7:
            return value

        common_values = {
            "protocol": ["TCP", "UDP", "ICMP", "HTTP", "HTTPS", "DNS", "SSH"],
            "http_method": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "severity": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            "decision": ["BLOCK", "ALLOW", "INVESTIGATE"],
        }

        for category, values in common_values.items():
            if category in feature_name.lower():
                return np.random.choice(values)

        return value

    def _perturb_ip(self, value: str, feature_name: str) -> str:
        """Perturb IP address (keep network, change host)."""
        if not value or not isinstance(value, str):
            return "0.0.0.0"

        try:
            parts = value.split(".")
            if len(parts) == 4:
                parts[3] = str(np.random.randint(1, 255))
                return ".".join(parts)
        except (ValueError, TypeError, AttributeError, IndexError) as e:
            logger.debug(f"IP perturbation failed for {value}: {e}")

        return value

    def _perturb_port(self, value: int, feature_name: str) -> int:
        """Perturb port number."""
        if value is None:
            return 0

        if np.random.random() < 0.5:
            common_ports = [
                21, 22, 23, 25, 53, 80, 110, 143, 443, 3306, 3389, 5432, 8080, 8443
            ]
            return np.random.choice(common_ports)

        return np.random.randint(1024, 65536)

    def _perturb_score(self, value: float, feature_name: str) -> float:
        """Perturb score (bounded 0-1)."""
        if value is None:
            return 0.5

        perturbed = value + np.random.normal(0, 0.1)
        return max(0.0, min(1.0, perturbed))

    def _perturb_text(self, value: str, feature_name: str) -> str:
        """Perturb text feature (not implemented - return original)."""
        return value

    def _calculate_feature_distance(
        self, original: Any, perturbed: Any, feature_type: str
    ) -> float:
        """Calculate distance between original and perturbed feature."""
        if original is None or perturbed is None:
            return 1.0

        if feature_type in ["numeric", "score", "port"]:
            try:
                orig_val = float(original)
                pert_val = float(perturbed)
                diff = abs(orig_val - pert_val)

                normalizer = max(abs(orig_val), 1.0)
                return min(1.0, diff / normalizer)
            except (ValueError, TypeError, ZeroDivisionError) as e:
                logger.debug(f"Distance calculation failed: {e}")
                return 1.0

        elif feature_type in ["categorical", "ip_address", "text"]:
            return 0.0 if original == perturbed else 1.0

        return 1.0
