"""LIME Configuration.

Perturbation and explanation configuration.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PerturbationConfig:
    """Configuration for feature perturbation.

    Attributes:
        num_samples: Number of perturbed samples to generate
        feature_selection: Method for feature selection
        kernel_width: Width of the exponential kernel
        sample_around_instance: Whether to sample around the instance
    """

    num_samples: int = 5000
    feature_selection: str = "auto"
    kernel_width: float = 0.25
    sample_around_instance: bool = True
