"""Data Preprocessor for MAXIMUS Training Pipeline.

Layer-specific preprocessing for Predictive Coding Network:
- Layer 1 (VAE): Feature vectorization (sensory compression)
- Layer 2 (GNN): Graph construction (behavioral patterns)
- Layer 3 (TCN): Time series (operational threats)
- Layer 4 (LSTM): Sequence encoding (tactical campaigns)
- Layer 5 (Transformer): Context encoding (strategic landscape)
"""

from __future__ import annotations

from .base import LayerPreprocessor
from .layer1 import (
    Layer1Preprocessor,
    encode_hash,
    encode_ip,
    encode_string,
    extract_label,
    generate_sample_id,
)
from .layer2 import Layer2Preprocessor
from .layer3 import Layer3Preprocessor
from .models import LayerType, PreprocessedSample
from .preprocessor import DataPreprocessor

__all__ = [
    "LayerType",
    "PreprocessedSample",
    "LayerPreprocessor",
    "Layer1Preprocessor",
    "Layer2Preprocessor",
    "Layer3Preprocessor",
    "DataPreprocessor",
    "encode_ip",
    "encode_string",
    "encode_hash",
    "extract_label",
    "generate_sample_id",
]
