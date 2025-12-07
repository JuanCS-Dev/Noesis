"""ONNX Export Models and Configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ONNXExportConfig:
    """ONNX export configuration."""

    output_path: Path = Path("models/onnx/model.onnx")
    opset_version: int = 13
    dynamic_axes: dict[str, dict[int, str]] | None = None
    optimize: bool = True
    verify: bool = True

    def __post_init__(self) -> None:
        """Validate configuration."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class ONNXExportResult:
    """ONNX export result."""

    success: bool
    onnx_path: Path | None = None
    model_size_mb: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] | None = None
