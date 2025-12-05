"""Inference Backend Implementations.

Mixin providing backend setup and inference for PyTorch, ONNX, and TensorRT.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from .config import InferenceConfig

# Try to import PyTorch
try:
    import torch
    import torch.nn as nn

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    if TYPE_CHECKING:
        import torch
        import torch.nn as nn

logger = logging.getLogger(__name__)


class BackendMixin:
    """Mixin providing backend setup and inference methods.

    Handles PyTorch, ONNX, and TensorRT backends.

    Attributes:
        config: Inference configuration.
        model: Loaded model.
    """

    config: InferenceConfig
    model: Any

    def _setup_model(self, model: Any) -> Any:
        """Setup model for inference.

        Args:
            model: Input model.

        Returns:
            Prepared model.
        """
        if self.config.backend == "pytorch":
            return self._setup_pytorch_model(model)

        if self.config.backend == "onnx":
            return self._setup_onnx_model(model)

        if self.config.backend == "tensorrt":
            return self._setup_tensorrt_model(model)

        raise ValueError(f"Unknown backend: {self.config.backend}")

    def _setup_pytorch_model(self, model: nn.Module) -> nn.Module:
        """Setup PyTorch model.

        Args:
            model: PyTorch model.

        Returns:
            Prepared model.
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch not available")

        device = torch.device(self.config.device)
        model = model.to(device)
        model.eval()

        if self.config.compile_model:
            try:
                model = torch.compile(model, mode="reduce-overhead")
                logger.info("Model compiled with torch.compile")
            except AttributeError:
                logger.debug("torch.compile not available (PyTorch < 2.0)")

        return model

    def _setup_onnx_model(self, model_path: str | Path) -> Any:
        """Setup ONNX model.

        Args:
            model_path: Path to ONNX model.

        Returns:
            ONNX session.
        """
        try:
            import onnxruntime as ort

            if self.config.device == "cuda":
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            else:
                providers = ["CPUExecutionProvider"]

            session = ort.InferenceSession(str(model_path), providers=providers)

            logger.info("ONNX model loaded with providers: %s", providers)

            return session

        except ImportError as err:
            raise ImportError(
                "onnxruntime not available. Install with: pip install onnxruntime"
            ) from err

    def _setup_tensorrt_model(self, model_path: str | Path) -> Any:
        """Setup TensorRT model.

        Args:
            model_path: Path to TensorRT engine.

        Returns:
            TensorRT context.
        """
        try:
            import tensorrt as trt

            with open(model_path, "rb") as f:
                runtime = trt.Runtime(trt.Logger(trt.Logger.WARNING))
                engine = runtime.deserialize_cuda_engine(f.read())

            context = engine.create_execution_context()

            logger.info("TensorRT engine loaded")

            return context

        except ImportError as err:
            raise ImportError(
                "TensorRT not available. Install NVIDIA TensorRT"
            ) from err

    def _run_inference(self, input_data: Any) -> Any:
        """Run model inference.

        Args:
            input_data: Input data.

        Returns:
            Model output.
        """
        if self.config.backend == "pytorch":
            return self._run_pytorch_inference(input_data)

        if self.config.backend == "onnx":
            return self._run_onnx_inference(input_data)

        if self.config.backend == "tensorrt":
            return self._run_tensorrt_inference(input_data)

        raise ValueError(f"Unknown backend: {self.config.backend}")

    def _run_pytorch_inference(self, input_data: Any) -> Any:
        """Run PyTorch inference.

        Args:
            input_data: Input tensor.

        Returns:
            Output tensor.
        """
        if not isinstance(input_data, torch.Tensor):
            input_data = torch.tensor(input_data)

        device = torch.device(self.config.device)
        input_data = input_data.to(device)

        with torch.no_grad():
            if self.config.use_amp and device.type == "cuda":
                with torch.cuda.amp.autocast():
                    output = self.model(input_data)
            else:
                output = self.model(input_data)

        return output

    def _run_onnx_inference(self, input_data: Any) -> Any:
        """Run ONNX inference.

        Args:
            input_data: Input array.

        Returns:
            Output array.
        """
        if TORCH_AVAILABLE and isinstance(input_data, torch.Tensor):
            input_data = input_data.cpu().numpy()

        input_name = self.model.get_inputs()[0].name
        outputs = self.model.run(None, {input_name: input_data})

        return outputs[0]

    def _run_tensorrt_inference(self, input_data: Any) -> Any:
        """Run TensorRT inference.

        Args:
            input_data: Input array.

        Returns:
            Output array.

        Raises:
            ValueError: TensorRT backend not fully supported.
        """
        raise ValueError(
            "TensorRT backend requires engine-specific setup. "
            "Use 'pytorch' or 'onnx' backends for general inference. "
            "For TensorRT deployment, create optimized engine using nvidia-docker "
            "and configure buffers/streams appropriately."
        )

    def _warmup(self) -> None:
        """Warm up model with dummy inputs."""
        logger.info("Warming up model: %d runs", self.config.num_warmup_runs)

        if self.config.backend == "pytorch" and TORCH_AVAILABLE:
            dummy_input = torch.randn(1, 3, 224, 224).to(self.config.device)
        else:
            dummy_input = np.random.randn(1, 3, 224, 224).astype(np.float32)

        for _ in range(self.config.num_warmup_runs):
            try:
                _ = self._run_inference(dummy_input)
            except Exception as e:
                logger.warning("Warmup failed: %s", e)
                break

        logger.info("Warmup complete")
