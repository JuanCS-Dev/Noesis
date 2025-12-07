"""Core ONNX Exporter Implementation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import torch
    import torch.nn as nn

from .models import ONNXExportConfig, ONNXExportResult

logger = logging.getLogger(__name__)


class ONNXExporter:
    """Export PyTorch models to ONNX format."""

    def __init__(self, config: ONNXExportConfig | None = None) -> None:
        """Initialize ONNX exporter."""
        self.config = config or ONNXExportConfig()
        self.logger = logger

    def export_model(
        self, model: nn.Module, dummy_input: torch.Tensor
    ) -> ONNXExportResult:
        """Export model to ONNX format."""
        try:
            import torch.onnx
            
            self.logger.info("Exporting to ONNX: %s", self.config.output_path)
            
            torch.onnx.export(
                model,
                dummy_input,
                str(self.config.output_path),
                opset_version=self.config.opset_version,
                dynamic_axes=self.config.dynamic_axes,
            )
            
            # Get file size
            size_mb = self.config.output_path.stat().st_size / (1024 * 1024)
            
            return ONNXExportResult(
                success=True,
                onnx_path=self.config.output_path,
                model_size_mb=size_mb,
            )
        except Exception as e:
            self.logger.error("Export failed: %s", e)
            return ONNXExportResult(success=False, error=str(e))
