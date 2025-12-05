"""Maximus Core Service - Maximus Integrated.

This module serves as the primary integration point for the entire Maximus AI
system, bringing together all core components into a cohesive and functional
unit. It orchestrates the flow of information and control between the autonomic
core, reasoning engine, memory system, tool orchestrator, and other specialized
modules.

This integrated module is responsible for the overall operation and coordination
of Maximus, ensuring that all parts work in harmony to achieve intelligent
behavior and respond effectively to complex tasks and dynamic environments.
"""

from __future__ import annotations

from .core import MaximusIntegrated
from .neuromodulation_mixin import NeuromodulationMixin
from .predictive_coding_mixin import PredictiveCodingMixin
from .skill_learning_mixin import SkillLearningMixin

__all__ = [
    "MaximusIntegrated",
    "NeuromodulationMixin",
    "PredictiveCodingMixin",
    "SkillLearningMixin",
]
