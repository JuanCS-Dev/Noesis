"""Shim for training.data_collection."""
from dataclasses import dataclass
from .data_collection_pkg import DataCollector, DataSourceType

@dataclass
class DataCollectionConfig:
    """Shim for backward compatibility."""
    pass

__all__ = ["DataCollector", "DataCollectionConfig", "DataSourceType"]
