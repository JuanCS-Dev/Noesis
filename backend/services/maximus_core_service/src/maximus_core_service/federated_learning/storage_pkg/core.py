"""Core FL storage implementation."""

from __future__ import annotations

import json
import logging
import os
import pickle
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

from ..base import FLRound, ModelType
from .models import ModelVersion

logger = logging.getLogger(__name__)


class RestrictedUnpickler(pickle.Unpickler):
    """Restricted pickle unpickler for security."""

    ALLOWED_MODULES = {
        "numpy",
        "numpy.core.multiarray",
        "numpy.core.numeric",
        "numpy.core._multiarray_umath",
        "numpy._core.multiarray",
        "numpy._core.numeric",
        "numpy._core._multiarray_umath",
        "builtins",
        "collections",
    }

    ALLOWED_CLASSES = {
        "numpy.ndarray",
        "numpy.dtype",
        "numpy.core.multiarray._reconstruct",
        "numpy._core.multiarray._reconstruct",
        "builtins.dict",
        "builtins.list",
        "builtins.tuple",
        "builtins.set",
        "builtins.frozenset",
        "builtins.int",
        "builtins.float",
        "builtins.str",
        "builtins.bytes",
        "builtins.bool",
        "builtins.NoneType",
        "collections.OrderedDict",
    }

    def find_class(self, module, name):
        """Override find_class to restrict to whitelist."""
        full_name = f"{module}.{name}"
        if module in self.ALLOWED_MODULES or full_name in self.ALLOWED_CLASSES:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(
            f"Forbidden class: {full_name}. Only numpy arrays and basic Python types allowed."
        )


def safe_pickle_load(file_obj):
    """Safely load pickle data."""
    return RestrictedUnpickler(file_obj).load()


class FLModelRegistry:
    """Registry for storing and retrieving FL model versions."""

    def __init__(self, storage_dir: str | None = None) -> None:
        """Initialize model registry."""
        if storage_dir is None:
            storage_dir = os.getenv("FL_MODELS_DIR", tempfile.mkdtemp(prefix="fl_models_", suffix="_maximus"))
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

        self.versions: dict[int, ModelVersion] = {}
        self.best_version_id: int | None = None
        self.best_accuracy: float = 0.0

        logger.info("FL Model Registry initialized: %s", storage_dir)

    def save_global_model(
        self,
        version_id: int,
        model_type: ModelType,
        round_id: int,
        weights: dict[str, np.ndarray],
        accuracy: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> ModelVersion:
        """Save a global model version."""
        file_name = f"model_v{version_id}_r{round_id}.pkl"
        file_path = self.storage_dir / file_name

        with open(file_path, "wb") as f:
            pickle.dump(weights, f)

        total_parameters = sum(w.size for w in weights.values())

        version = ModelVersion(
            version_id=version_id,
            model_type=model_type,
            round_id=round_id,
            accuracy=accuracy,
            total_parameters=total_parameters,
            file_path=str(file_path),
            metadata=metadata or {},
        )

        self.versions[version_id] = version

        if accuracy > self.best_accuracy:
            self.best_accuracy = accuracy
            self.best_version_id = version_id
            logger.info("New best model: v%s (accuracy=%.4f)", version_id, accuracy)

        logger.info(
            "Saved model v%s from round %s (%s parameters, %.4f accuracy)",
            version_id,
            round_id,
            f"{total_parameters:,}",
            accuracy,
        )

        return version

    def load_global_model(self, version_id: int) -> dict[str, np.ndarray] | None:
        """Load a global model version."""
        if version_id not in self.versions:
            logger.warning("Version %s not found", version_id)
            return None

        version = self.versions[version_id]

        if not version.file_path or not os.path.exists(version.file_path):
            logger.error("Model file not found: %s", version.file_path)
            return None

        try:
            with open(version.file_path, "rb") as f:
                weights = safe_pickle_load(f)
            logger.info("Loaded model v%s from %s", version_id, version.file_path)
            return weights
        except pickle.UnpicklingError as e:
            logger.error("Security error loading model v%s: %s", version_id, e)
            return None
        except Exception as e:
            logger.error("Error loading model v%s: %s", version_id, e)
            return None

    def get_best_model(self) -> dict[str, np.ndarray] | None:
        """Get the best model version."""
        if self.best_version_id is None:
            return None
        return self.load_global_model(self.best_version_id)

    def get_latest_model(self) -> dict[str, np.ndarray] | None:
        """Get the latest model version."""
        if not self.versions:
            return None
        latest_version_id = max(self.versions.keys())
        return self.load_global_model(latest_version_id)

    def list_versions(self, limit: int | None = None) -> list[ModelVersion]:
        """List all model versions."""
        versions = sorted(self.versions.values(), key=lambda v: v.version_id, reverse=True)
        if limit:
            versions = versions[:limit]
        return versions

    def get_version_info(self, version_id: int) -> ModelVersion | None:
        """Get information about a specific version."""
        return self.versions.get(version_id)

    def delete_version(self, version_id: int) -> bool:
        """Delete a model version."""
        if version_id not in self.versions:
            logger.warning("Version %s not found", version_id)
            return False

        version = self.versions[version_id]

        if version.file_path and os.path.exists(version.file_path):
            os.remove(version.file_path)
            logger.info("Deleted model file: %s", version.file_path)

        del self.versions[version_id]
        logger.info("Deleted model version %s", version_id)
        return True


class FLRoundHistory:
    """History of federated learning rounds."""

    def __init__(self, storage_dir: str | None = None) -> None:
        """Initialize round history."""
        if storage_dir is None:
            storage_dir = os.getenv("FL_ROUNDS_DIR", tempfile.mkdtemp(prefix="fl_rounds_", suffix="_maximus"))
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.rounds: list[FLRound] = []
        logger.info("FL Round History initialized: %s", storage_dir)

    def save_round(self, round_obj: FLRound) -> bool:
        """Save a completed round."""
        self.rounds.append(round_obj)

        file_name = f"round_{round_obj.round_id:04d}.json"
        file_path = self.storage_dir / file_name

        with open(file_path, "w") as f:
            json.dump(round_obj.to_dict(), f, indent=2)

        duration = round_obj.get_duration_seconds()
        duration_str = f"{duration:.1f}s" if duration is not None else "in progress"
        logger.info("Saved round %s to %s (duration=%s)", round_obj.round_id, file_path, duration_str)
        return True

    def get_round(self, round_id: int) -> FLRound | None:
        """Get a specific round."""
        for round_obj in self.rounds:
            if round_obj.round_id == round_id:
                return round_obj
        return None

    def get_round_stats(self) -> dict[str, Any]:
        """Get statistics across all rounds."""
        if not self.rounds:
            return {"total_rounds": 0, "total_updates": 0, "total_samples": 0}

        total_updates = sum(len(r.received_updates) for r in self.rounds)
        total_samples = sum(r.get_total_samples() for r in self.rounds)

        durations = [r.get_duration_seconds() for r in self.rounds if r.get_duration_seconds() is not None]
        participation_rates = [r.get_participation_rate() for r in self.rounds]

        avg_metrics = {}
        if self.rounds[-1].metrics:
            metric_names = self.rounds[-1].metrics.keys()
            for metric_name in metric_names:
                values = [r.metrics.get(metric_name, 0.0) for r in self.rounds if r.metrics]
                if values:
                    avg_metrics[metric_name] = np.mean(values)

        return {
            "total_rounds": len(self.rounds),
            "total_updates": total_updates,
            "total_samples": total_samples,
            "average_duration_seconds": np.mean(durations) if durations else 0.0,
            "average_participation_rate": np.mean(participation_rates) if participation_rates else 0.0,
            "average_metrics": avg_metrics,
        }

    def get_convergence_data(self) -> dict[str, list[float]]:
        """Get convergence data for plotting."""
        convergence_data = {"round_id": [], "duration": [], "participation_rate": []}

        if self.rounds and self.rounds[0].metrics:
            for metric_name in self.rounds[0].metrics.keys():
                convergence_data[metric_name] = []

        for round_obj in self.rounds:
            convergence_data["round_id"].append(round_obj.round_id)
            duration = round_obj.get_duration_seconds()
            convergence_data["duration"].append(duration if duration else 0.0)
            convergence_data["participation_rate"].append(round_obj.get_participation_rate())

            if round_obj.metrics:
                for metric_name, value in round_obj.metrics.items():
                    if metric_name in convergence_data:
                        convergence_data[metric_name].append(value)

        return convergence_data
