"""
HCL Monitor Service - Metrics Models
====================================

Pydantic models for system and service metrics.
"""

from datetime import datetime
from typing import Dict

from pydantic import BaseModel, Field


class ServiceStatus(BaseModel):
    """
    Status of individual services.
    """
    maximus_core: str = Field(..., description="Status of Maximus Core")
    chemical_sensing: str = Field(..., description="Status of Chemical Sensing")
    visual_cortex: str = Field(..., description="Status of Visual Cortex")


class SystemMetrics(BaseModel):
    """
    Comprehensive system metrics.
    """
    timestamp: datetime = Field(..., description="Collection timestamp")
    cpu_usage: float = Field(..., description="CPU usage percentage")
    memory_usage: float = Field(..., description="Memory usage percentage")
    disk_io_read_rate: float = Field(..., description="Disk read rate in bytes/sec")
    disk_io_write_rate: float = Field(..., description="Disk write rate in bytes/sec")
    network_io_recv_rate: float = Field(..., description="Network receive rate in bytes/sec")
    network_io_sent_rate: float = Field(..., description="Network send rate in bytes/sec")
    avg_latency_ms: float = Field(..., description="Average system latency in ms")
    error_rate: float = Field(..., description="System error rate")
    service_status: Dict[str, str] = Field(..., description="Status of monitored services")
