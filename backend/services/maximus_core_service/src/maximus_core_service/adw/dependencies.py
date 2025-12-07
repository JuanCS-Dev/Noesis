"""
ADW Service Dependencies.

Singleton pattern for workflow instances.

Author: MAXIMUS Team
Date: 2025-10-15
"""

from __future__ import annotations

import logging

from maximus_core_service.workflows.attack_surface_adw import AttackSurfaceWorkflow
from maximus_core_service.workflows.credential_intel_adw import CredentialIntelWorkflow
from maximus_core_service.workflows.target_profiling import TargetProfilingWorkflow

logger = logging.getLogger(__name__)

# Workflow instances (singletons)
_attack_surface_workflow: AttackSurfaceWorkflow | None = None
_credential_intel_workflow: CredentialIntelWorkflow | None = None
_target_profiling_workflow: TargetProfilingWorkflow | None = None


def get_attack_surface_workflow() -> AttackSurfaceWorkflow:
    """Dependency: Get attack surface workflow instance."""
    global _attack_surface_workflow
    if _attack_surface_workflow is None:
        _attack_surface_workflow = AttackSurfaceWorkflow()
        logger.info("AttackSurfaceWorkflow initialized")
    return _attack_surface_workflow


def get_credential_intel_workflow() -> CredentialIntelWorkflow:
    """Dependency: Get credential intelligence workflow instance."""
    global _credential_intel_workflow
    if _credential_intel_workflow is None:
        _credential_intel_workflow = CredentialIntelWorkflow()
        logger.info("CredentialIntelWorkflow initialized")
    return _credential_intel_workflow


def get_target_profiling_workflow() -> TargetProfilingWorkflow:
    """Dependency: Get target profiling workflow instance."""
    global _target_profiling_workflow
    if _target_profiling_workflow is None:
        _target_profiling_workflow = TargetProfilingWorkflow()
        logger.info("TargetProfilingWorkflow initialized")
    return _target_profiling_workflow
