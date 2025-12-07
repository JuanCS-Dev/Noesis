"""Infrastructure components."""

from __future__ import annotations


from maximus_core_service.motor_integridade_processual.infrastructure.audit_trail import AuditLogger
from maximus_core_service.motor_integridade_processual.infrastructure.hitl_queue import HITLQueue
from maximus_core_service.motor_integridade_processual.infrastructure.knowledge_base import KnowledgeBase
from maximus_core_service.motor_integridade_processual.infrastructure.metrics import MetricsCollector

__all__ = ["AuditLogger", "HITLQueue", "KnowledgeBase", "MetricsCollector"]
