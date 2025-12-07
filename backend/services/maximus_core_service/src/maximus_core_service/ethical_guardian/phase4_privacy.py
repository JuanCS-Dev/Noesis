"""
Phase 4: Privacy and Federated Learning Checks.

Phase 4.1: Differential Privacy budget check
Phase 4.2: Federated Learning readiness check

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from maximus_core_service.federated_learning import FLConfig, FLStatus
from maximus_core_service.privacy import PrivacyBudget

from .models import FLCheckResult, PrivacyCheckResult

if TYPE_CHECKING:
    pass


async def privacy_check(
    privacy_budget: PrivacyBudget,
    action: str,
    context: dict[str, Any],
) -> PrivacyCheckResult:
    """
    Phase 4.1: Check differential privacy budget and constraints.

    Verifica se a ação respeita o privacy budget e princípios de DP.

    Target: <50ms

    Args:
        privacy_budget: PrivacyBudget instance
        action: Action being validated
        context: Action context

    Returns:
        PrivacyCheckResult with budget status
    """
    start_time = time.time()

    # Get current budget status
    budget = privacy_budget
    budget_ok = not budget.budget_exhausted

    # Check if action processes personal data
    processes_pii = context.get("processes_personal_data", False) or context.get(
        "has_pii", False
    )

    # If action processes PII, check budget
    if processes_pii and budget.budget_exhausted:
        budget_ok = False

    duration_ms = (time.time() - start_time) * 1000

    return PrivacyCheckResult(
        privacy_budget_ok=budget_ok,
        privacy_level=budget.privacy_level.value,
        total_epsilon=budget.total_epsilon,
        used_epsilon=budget.used_epsilon,
        remaining_epsilon=budget.remaining_epsilon,
        total_delta=budget.total_delta,
        used_delta=budget.used_delta,
        remaining_delta=budget.remaining_delta,
        budget_exhausted=budget.budget_exhausted,
        queries_executed=len(budget.queries_executed),
        duration_ms=duration_ms,
    )


async def fl_check(
    fl_config: FLConfig | None,
    action: str,
    context: dict[str, Any],
) -> FLCheckResult:
    """
    Phase 4.2: Check federated learning readiness and constraints.

    Verifica se a ação é compatível com FL e se requer DP.

    Target: <30ms

    Args:
        fl_config: FLConfig instance (or None if FL disabled)
        action: Action being validated
        context: Action context

    Returns:
        FLCheckResult with FL status
    """
    start_time = time.time()

    # Check if action involves model training/aggregation
    is_model_training = any(
        keyword in action.lower()
        for keyword in ["train", "model", "learn", "aggregate", "federated"]
    )

    # FL is ready if config exists and action involves training
    fl_ready = is_model_training and fl_config is not None

    # Determine FL status
    if fl_ready:
        fl_status = FLStatus.INITIALIZING.value
        model_type = fl_config.model_type.value if fl_config else None
        aggregation_strategy = fl_config.aggregation_strategy.value if fl_config else None
        requires_dp = fl_config.use_differential_privacy if fl_config else False
        dp_epsilon = fl_config.dp_epsilon if fl_config else None
        dp_delta = fl_config.dp_delta if fl_config else None
        notes = ["FL ready for model training"] if fl_ready else []
    else:
        fl_status = FLStatus.FAILED.value if is_model_training else "not_applicable"
        model_type = None
        aggregation_strategy = None
        requires_dp = False
        dp_epsilon = None
        dp_delta = None
        notes = (
            ["FL not configured"]
            if is_model_training
            else ["Action does not require FL"]
        )

    duration_ms = (time.time() - start_time) * 1000

    return FLCheckResult(
        fl_ready=fl_ready,
        fl_status=fl_status,
        model_type=model_type,
        aggregation_strategy=aggregation_strategy,
        requires_dp=requires_dp,
        dp_epsilon=dp_epsilon,
        dp_delta=dp_delta,
        notes=notes,
        duration_ms=duration_ms,
    )
