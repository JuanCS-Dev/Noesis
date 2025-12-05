"""Attention Core - Foveal/Peripheral Vision-Inspired Resource Allocation.

Two-tier processing inspired by human visual attention:
- Peripheral: Lightweight, broad scanning of all inputs (<100ms)
- Foveal: Deep, expensive analysis of high-salience targets (<100ms saccade)

This allows efficient resource allocation by only applying expensive analysis
to events that warrant attention.
"""

from __future__ import annotations

from .attention import AttentionSystem
from .foveal import FovealAnalyzer
from .models import FovealAnalysis, PeripheralDetection
from .peripheral import PeripheralMonitor

__all__ = [
    "PeripheralDetection",
    "FovealAnalysis",
    "PeripheralMonitor",
    "FovealAnalyzer",
    "AttentionSystem",
]
