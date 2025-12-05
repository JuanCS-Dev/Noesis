"""Core dataset builder implementation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

from .models import DatasetSplit, SplitStrategy

logger = logging.getLogger(__name__)


class DatasetBuilder:
    """Builds training datasets with various split strategies."""

    def __init__(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        sample_ids: list[str],
        timestamps: np.ndarray | None = None,
        output_dir: Path | None = None,
        random_seed: int = 42,
    ) -> None:
        """Initialize dataset builder."""
        self.features = features
        self.labels = labels
        self.sample_ids = sample_ids
        self.timestamps = timestamps
        self.output_dir = Path(output_dir) if output_dir else Path("training/data/splits")
        self.random_seed = random_seed

        self.output_dir.mkdir(parents=True, exist_ok=True)

        assert len(features) == len(labels) == len(sample_ids), "Shape mismatch"
        np.random.seed(random_seed)

        logger.info("DatasetBuilder initialized: %s samples, %s features", len(features), features.shape[1])

    def create_splits(
        self,
        strategy: SplitStrategy = SplitStrategy.STRATIFIED,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        balance_classes: bool = False,
    ) -> dict[str, DatasetSplit]:
        """Create train/val/test splits."""
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "Ratios must sum to 1"

        if strategy == SplitStrategy.RANDOM:
            indices_dict = self._random_split(train_ratio, val_ratio, test_ratio)
        elif strategy == SplitStrategy.STRATIFIED:
            indices_dict = self._stratified_split(train_ratio, val_ratio, test_ratio)
        elif strategy == SplitStrategy.TEMPORAL:
            indices_dict = self._temporal_split(train_ratio, val_ratio, test_ratio)
        else:
            raise ValueError(f"Unsupported strategy: {strategy}")

        splits = {}
        for name, indices in indices_dict.items():
            split = DatasetSplit(
                name=name,
                features=self.features[indices],
                labels=self.labels[indices],
                sample_ids=[self.sample_ids[i] for i in indices],
                indices=indices,
            )
            splits[name] = split
            logger.info("%s split: %s", name.capitalize(), split)

        if balance_classes and "train" in splits:
            splits["train"] = self._balance_classes(splits["train"])

        return splits

    def _random_split(self, train_ratio: float, val_ratio: float, test_ratio: float) -> dict[str, np.ndarray]:
        """Create random split."""
        n_samples = len(self.features)
        indices = np.random.permutation(n_samples)

        n_train = int(n_samples * train_ratio)
        n_val = int(n_samples * val_ratio)

        return {
            "train": indices[:n_train],
            "val": indices[n_train : n_train + n_val],
            "test": indices[n_train + n_val :],
        }

    def _stratified_split(self, train_ratio: float, val_ratio: float, test_ratio: float) -> dict[str, np.ndarray]:
        """Create stratified split (balanced classes)."""
        unique_labels = np.unique(self.labels[self.labels >= 0])

        train_indices = []
        val_indices = []
        test_indices = []

        for label in unique_labels:
            label_indices = np.where(self.labels == label)[0]
            n_label = len(label_indices)
            label_indices = np.random.permutation(label_indices)

            n_train = int(n_label * train_ratio)
            n_val = int(n_label * val_ratio)

            train_indices.extend(label_indices[:n_train].tolist())
            val_indices.extend(label_indices[n_train : n_train + n_val].tolist())
            test_indices.extend(label_indices[n_train + n_val :].tolist())

        train_indices = np.array(train_indices)
        val_indices = np.array(val_indices)
        test_indices = np.array(test_indices)

        np.random.shuffle(train_indices)
        np.random.shuffle(val_indices)
        np.random.shuffle(test_indices)

        return {"train": train_indices, "val": val_indices, "test": test_indices}

    def _temporal_split(self, train_ratio: float, val_ratio: float, test_ratio: float) -> dict[str, np.ndarray]:
        """Create temporal split (respect time ordering)."""
        if self.timestamps is None:
            logger.warning("No timestamps provided, falling back to random split")
            return self._random_split(train_ratio, val_ratio, test_ratio)

        sorted_indices = np.argsort(self.timestamps)
        n_samples = len(sorted_indices)

        n_train = int(n_samples * train_ratio)
        n_val = int(n_samples * val_ratio)

        return {
            "train": sorted_indices[:n_train],
            "val": sorted_indices[n_train : n_train + n_val],
            "test": sorted_indices[n_train + n_val :],
        }

    def _balance_classes(self, split: DatasetSplit) -> DatasetSplit:
        """Balance classes using undersampling."""
        unique_labels, label_counts = np.unique(split.labels[split.labels >= 0], return_counts=True)

        if len(unique_labels) == 0:
            logger.warning("No labeled data to balance")
            return split

        min_count = label_counts.min()
        balanced_indices = []

        for label in unique_labels:
            label_mask = split.labels == label
            label_indices = np.where(label_mask)[0]
            sampled_indices = np.random.choice(label_indices, size=min_count, replace=False)
            balanced_indices.extend(sampled_indices.tolist())

        balanced_indices = np.array(balanced_indices)
        np.random.shuffle(balanced_indices)

        balanced_split = DatasetSplit(
            name=split.name + "_balanced",
            features=split.features[balanced_indices],
            labels=split.labels[balanced_indices],
            sample_ids=[split.sample_ids[i] for i in balanced_indices],
            indices=split.indices[balanced_indices],
        )

        logger.info("Balanced %s: %s -> %s samples", split.name, len(split), len(balanced_split))
        return balanced_split

    def save_splits(self, splits: dict[str, DatasetSplit], prefix: str = "layer1") -> None:
        """Save all splits to disk."""
        for name, split in splits.items():
            filename = f"{prefix}_{name}.npz"
            output_path = self.output_dir / filename
            split.save(output_path)
        logger.info("Saved %s splits with prefix '%s'", len(splits), prefix)

    @classmethod
    def load_splits(cls, split_dir: Path, prefix: str = "layer1") -> dict[str, DatasetSplit]:
        """Load splits from disk."""
        splits = {}
        for split_name in ["train", "val", "test"]:
            filename = f"{prefix}_{split_name}.npz"
            filepath = split_dir / filename

            if filepath.exists():
                split = DatasetSplit.load(filepath, name=split_name)
                splits[split_name] = split
                logger.info("Loaded %s split: %s samples", split_name, len(split))
            else:
                logger.warning("Split file not found: %s", filepath)
        return splits

    def augment_data(
        self, split: DatasetSplit, augmentation_factor: int = 2, noise_std: float = 0.01
    ) -> DatasetSplit:
        """Augment data with noise."""
        augmented_features = [split.features]
        augmented_labels = [split.labels]
        augmented_ids = list(split.sample_ids)

        for i in range(augmentation_factor - 1):
            noise = np.random.normal(0, noise_std, split.features.shape)
            augmented_feat = split.features + noise

            augmented_features.append(augmented_feat)
            augmented_labels.append(split.labels)
            augmented_ids.extend([f"{sid}_aug{i + 1}" for sid in split.sample_ids])

        augmented_split = DatasetSplit(
            name=split.name + "_augmented",
            features=np.concatenate(augmented_features),
            labels=np.concatenate(augmented_labels),
            sample_ids=augmented_ids,
            indices=np.arange(len(augmented_ids)),
        )

        logger.info(
            "Augmented %s: %s -> %s samples (factor=%s)",
            split.name,
            len(split),
            len(augmented_split),
            augmentation_factor,
        )
        return augmented_split

    def get_statistics(self) -> dict[str, Any]:
        """Get dataset statistics."""
        labeled_mask = self.labels >= 0
        n_labeled = labeled_mask.sum()
        n_unlabeled = (~labeled_mask).sum()

        stats = {
            "total_samples": len(self.features),
            "n_features": self.features.shape[1],
            "n_labeled": int(n_labeled),
            "n_unlabeled": int(n_unlabeled),
            "class_distribution": {},
            "feature_stats": {
                "mean": self.features.mean(axis=0).tolist(),
                "std": self.features.std(axis=0).tolist(),
                "min": self.features.min(axis=0).tolist(),
                "max": self.features.max(axis=0).tolist(),
            },
        }

        if n_labeled > 0:
            unique, counts = np.unique(self.labels[labeled_mask], return_counts=True)
            stats["class_distribution"] = dict(zip(unique.tolist(), counts.tolist(), strict=False))

        return stats


class PyTorchDatasetWrapper:
    """Wrapper to convert DatasetSplit to PyTorch Dataset."""

    def __init__(self, split: DatasetSplit, transform=None) -> None:
        """Initialize PyTorch dataset wrapper."""
        self.split = split
        self.transform = transform

    def __len__(self) -> int:
        return len(self.split)

    def __getitem__(self, idx: int) -> tuple[np.ndarray, int]:
        """Get item by index."""
        features = self.split.features[idx]
        label = self.split.labels[idx]

        if self.transform:
            features = self.transform(features)

        return features, label

    def get_sample_id(self, idx: int) -> str:
        """Get sample ID by index."""
        return self.split.sample_ids[idx]
