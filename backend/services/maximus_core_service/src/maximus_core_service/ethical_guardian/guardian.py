"""
Ethical Guardian - Main orchestration class.

Integrates the 7-phase ethical validation stack.
Performance target: <500ms per validation.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any

from maximus_core_service.compliance import ComplianceConfig, ComplianceEngine, RegulationType
from maximus_core_service.ethics import EthicalIntegrationEngine, EthicalVerdict
from maximus_core_service.fairness import BiasDetector, FairnessMonitor
from maximus_core_service.federated_learning import AggregationStrategy, FLConfig, ModelType
from maximus_core_service.governance import AuditLogger, GovernanceConfig, PolicyEngine
from maximus_core_service.hitl import HITLDecisionFramework, RiskAssessor
from maximus_core_service.privacy import CompositionType, PrivacyAccountant, PrivacyBudget
from maximus_core_service.xai import ExplanationEngine

from .audit import get_statistics, log_decision
from .models import (
    EthicalDecisionResult,
    EthicalDecisionType,
    HITLCheckResult,
)
from .phase0_governance import governance_check
from .phase1_ethics import ethics_evaluation
from .phase2_xai import generate_explanation
from .phase3_fairness import fairness_check
from .phase4_privacy import fl_check, privacy_check
from .phase5_hitl import hitl_check
from .phase6_compliance import compliance_check

logger = logging.getLogger(__name__)


class EthicalGuardian:
    """
    Guardian que valida todas as ações do MAXIMUS através do Ethical AI Stack.

    Integra as 7 fases éticas:
    - Phase 0: Governance (ERB, Policies, Audit)
    - Phase 1: Ethics (4 frameworks filosóficos)
    - Phase 2: XAI (Explicabilidade)
    - Phase 3: Fairness (Bias detection)
    - Phase 4: Privacy (DP) & Federated Learning
    - Phase 5: HITL (Human-in-the-Loop)
    - Phase 6: Compliance (Regulações)

    Performance target: <500ms por validação completa
    """

    def __init__(
        self,
        governance_config: GovernanceConfig | None = None,
        privacy_budget: PrivacyBudget | None = None,
        enable_governance: bool = True,
        enable_ethics: bool = True,
        enable_fairness: bool = True,
        enable_xai: bool = True,
        enable_privacy: bool = True,
        enable_fl: bool = False,
        enable_hitl: bool = True,
        enable_compliance: bool = True,
    ):
        """
        Inicializa o Ethical Guardian.

        Args:
            governance_config: Configuração do governance
            privacy_budget: Privacy budget para DP
            enable_governance: Habilita checks de governance
            enable_ethics: Habilita avaliação ética
            enable_fairness: Habilita checks de fairness e bias
            enable_xai: Habilita explicações XAI
            enable_privacy: Habilita checks de privacy
            enable_fl: Habilita checks de federated learning
            enable_hitl: Habilita checks de HITL
            enable_compliance: Habilita checks de compliance
        """
        self.governance_config = governance_config or GovernanceConfig()
        self.enable_governance = enable_governance
        self.enable_ethics = enable_ethics
        self.enable_fairness = enable_fairness
        self.enable_xai = enable_xai
        self.enable_privacy = enable_privacy
        self.enable_fl = enable_fl
        self.enable_hitl = enable_hitl
        self.enable_compliance = enable_compliance

        self._init_governance()
        self._init_ethics()
        self._init_xai()
        self._init_fairness()
        self._init_privacy(privacy_budget)
        self._init_fl()
        self._init_hitl()
        self._init_compliance()

        # Statistics
        self.total_validations = 0
        self.total_approved = 0
        self.total_rejected = 0
        self.avg_duration_ms = 0.0

    def _init_governance(self) -> None:
        """Initialize Phase 0: Governance."""
        if self.enable_governance:
            self.policy_engine = PolicyEngine(self.governance_config)
            try:
                self.audit_logger = AuditLogger(self.governance_config)
            except ImportError:
                self.audit_logger = None
        else:
            self.policy_engine = None
            self.audit_logger = None

    def _init_ethics(self) -> None:
        """Initialize Phase 1: Ethics."""
        if self.enable_ethics:
            self.ethics_engine = EthicalIntegrationEngine(
                config={
                    "enable_kantian": True,
                    "enable_utilitarian": True,
                    "enable_virtue": True,
                    "enable_principialism": True,
                    "cache_enabled": True,
                    "cache_ttl_seconds": 3600,
                }
            )
        else:
            self.ethics_engine = None

    def _init_xai(self) -> None:
        """Initialize Phase 2: XAI."""
        if self.enable_xai:
            self.xai_engine = ExplanationEngine(
                config={
                    "enable_lime": True,
                    "enable_shap": False,
                    "enable_counterfactual": False,
                    "cache_enabled": True,
                    "cache_max_size": 1000,
                }
            )
        else:
            self.xai_engine = None

    def _init_fairness(self) -> None:
        """Initialize Phase 3: Fairness."""
        if self.enable_fairness:
            self.bias_detector = BiasDetector(
                config={
                    "min_sample_size": 30,
                    "significance_level": 0.05,
                    "disparate_impact_threshold": 0.8,
                    "sensitivity": "medium",
                }
            )
            self.fairness_monitor = FairnessMonitor(
                config={
                    "check_interval_seconds": 3600,
                    "alert_threshold": 0.1,
                }
            )
        else:
            self.bias_detector = None
            self.fairness_monitor = None

    def _init_privacy(self, privacy_budget: PrivacyBudget | None) -> None:
        """Initialize Phase 4.1: Privacy."""
        if self.enable_privacy:
            self.privacy_budget = privacy_budget or PrivacyBudget(
                total_epsilon=3.0,
                total_delta=1e-5,
            )
            self.privacy_accountant = PrivacyAccountant(
                total_epsilon=self.privacy_budget.total_epsilon,
                total_delta=self.privacy_budget.total_delta,
                composition_type=CompositionType.ADVANCED_SEQUENTIAL,
            )
        else:
            self.privacy_budget = None
            self.privacy_accountant = None

    def _init_fl(self) -> None:
        """Initialize Phase 4.2: Federated Learning."""
        if self.enable_fl:
            self.fl_config = FLConfig(
                model_type=ModelType.THREAT_CLASSIFIER,
                aggregation_strategy=AggregationStrategy.DP_FEDAVG,
                min_clients=3,
                use_differential_privacy=True,
                dp_epsilon=8.0,
                dp_delta=1e-5,
            )
        else:
            self.fl_config = None

    def _init_hitl(self) -> None:
        """Initialize Phase 5: HITL."""
        if self.enable_hitl:
            self.risk_assessor = RiskAssessor()
            self.hitl_framework = HITLDecisionFramework(
                risk_assessor=self.risk_assessor
            )
        else:
            self.risk_assessor = None
            self.hitl_framework = None

    def _init_compliance(self) -> None:
        """Initialize Phase 6: Compliance."""
        if self.enable_compliance:
            self.compliance_engine = ComplianceEngine(
                config=ComplianceConfig(
                    enabled_regulations=[
                        RegulationType.GDPR,
                        RegulationType.SOC2_TYPE_II,
                        RegulationType.ISO_27001,
                    ],
                    auto_collect_evidence=False,
                    continuous_monitoring=False,
                )
            )
        else:
            self.compliance_engine = None

    async def validate_action(
        self,
        action: str,
        context: dict[str, Any],
        actor: str = "maximus",
        tool_name: str | None = None,
    ) -> EthicalDecisionResult:
        """
        Valida uma ação através do stack ético completo.

        Performance target: <500ms

        Args:
            action: Ação a ser validada
            context: Contexto da ação
            actor: Quem está executando
            tool_name: Nome do tool (opcional)

        Returns:
            EthicalDecisionResult com decisão completa e métricas
        """
        start_time = time.time()
        result = EthicalDecisionResult(
            action=action,
            actor=actor,
            timestamp=datetime.utcnow(),
        )
        self.total_validations += 1

        try:
            # Phase 0: Governance
            if self.enable_governance:
                gov_result = await governance_check(
                    self.policy_engine, action, context, actor
                )
                result.governance = gov_result

                if not gov_result.is_compliant:
                    result.decision_type = EthicalDecisionType.REJECTED_BY_GOVERNANCE
                    result.is_approved = False
                    result.rejection_reasons = [
                        f"Policy violation: {v.get('title', 'Unknown')}"
                        for v in gov_result.violations
                    ]
                    result.total_duration_ms = (time.time() - start_time) * 1000
                    await log_decision(self.audit_logger, result)
                    return result

            # Phase 1: Ethics
            if self.enable_ethics:
                ethics_result = await ethics_evaluation(
                    self.ethics_engine, action, context, actor
                )
                result.ethics = ethics_result

                if ethics_result.verdict == EthicalVerdict.REJECTED:
                    result.decision_type = EthicalDecisionType.REJECTED_BY_ETHICS
                    result.is_approved = False
                    result.rejection_reasons.append(
                        f"Ethical verdict: {ethics_result.verdict.value}"
                    )
                    result.total_duration_ms = (time.time() - start_time) * 1000
                    await log_decision(self.audit_logger, result)
                    return result

            # Phase 2: XAI
            if self.enable_xai and result.ethics:
                try:
                    result.xai = await generate_explanation(
                        self.xai_engine, action, context, result.ethics
                    )
                except Exception:
                    result.xai = None

            # Phase 3: Fairness
            if self.enable_fairness:
                try:
                    result.fairness = await fairness_check(
                        self.bias_detector, action, context
                    )
                    if (
                        not result.fairness.fairness_ok
                        and result.fairness.mitigation_recommended
                    ):
                        result.decision_type = EthicalDecisionType.REJECTED_BY_FAIRNESS
                        result.is_approved = False
                        result.rejection_reasons.append(
                            f"Critical bias detected: {result.fairness.bias_severity}"
                        )
                        result.total_duration_ms = (time.time() - start_time) * 1000
                        await log_decision(self.audit_logger, result)
                        return result
                except Exception as e:
                    logger.warning(f"Fairness check failed: {e}")
                    result.fairness = None

            # Phase 4.1: Privacy
            if self.enable_privacy:
                try:
                    result.privacy = await privacy_check(
                        self.privacy_budget, action, context
                    )
                    if not result.privacy.privacy_budget_ok and (
                        context.get("processes_personal_data")
                        or context.get("has_pii")
                    ):
                        result.decision_type = EthicalDecisionType.REJECTED_BY_PRIVACY
                        result.is_approved = False
                        result.rejection_reasons.append("Privacy budget exhausted")
                        result.total_duration_ms = (time.time() - start_time) * 1000
                        await log_decision(self.audit_logger, result)
                        return result
                except Exception:
                    result.privacy = None

            # Phase 4.2: Federated Learning
            if self.enable_fl:
                try:
                    result.fl = await fl_check(self.fl_config, action, context)
                except Exception:
                    result.fl = None

            # Phase 5: HITL
            if self.enable_hitl:
                try:
                    confidence = result.ethics.confidence if result.ethics else 0.0
                    result.hitl = await hitl_check(
                        self.risk_assessor, action, context, confidence
                    )
                except Exception as e:
                    logger.warning(f"HITL check failed: {e}")
                    result.hitl = HITLCheckResult(
                        requires_human_review=True,
                        automation_level="manual",
                        risk_level="medium",
                        confidence_threshold_met=False,
                        estimated_sla_minutes=15,
                        escalation_recommended=False,
                        human_expertise_required=["soc_operator"],
                        decision_rationale="HITL check failed - defaulting to human review",
                        duration_ms=0.0,
                    )

            # Phase 6: Compliance
            if self.enable_compliance:
                try:
                    result.compliance = await compliance_check(
                        self.compliance_engine, action, context
                    )
                except Exception:
                    result.compliance = None

            # Final Decision
            self._make_final_decision(result)

            # Update statistics
            if result.is_approved:
                self.total_approved += 1
            else:
                self.total_rejected += 1

        except Exception as e:
            result.decision_type = EthicalDecisionType.ERROR
            result.is_approved = False
            result.rejection_reasons.append(f"Error during validation: {str(e)}")

        # Final timing
        result.total_duration_ms = (time.time() - start_time) * 1000
        self.avg_duration_ms = (
            self.avg_duration_ms * (self.total_validations - 1)
            + result.total_duration_ms
        ) / self.total_validations

        await log_decision(self.audit_logger, result)
        return result

    def _make_final_decision(self, result: EthicalDecisionResult) -> None:
        """Make final decision based on all phase results."""
        if result.hitl and result.hitl.requires_human_review:
            result.decision_type = EthicalDecisionType.REQUIRES_HUMAN_REVIEW
            result.is_approved = False
            result.conditions.append(
                f"Human review required (Risk: {result.hitl.risk_level})"
            )
        elif result.ethics and result.ethics.verdict == EthicalVerdict.APPROVED:
            result.decision_type = EthicalDecisionType.APPROVED
            result.is_approved = True
            if result.hitl and result.hitl.automation_level == "supervised":
                result.decision_type = EthicalDecisionType.APPROVED_WITH_CONDITIONS
                result.conditions.append("Approved with SUPERVISED monitoring")
        elif result.ethics and result.ethics.verdict == EthicalVerdict.CONDITIONAL:
            result.decision_type = EthicalDecisionType.APPROVED_WITH_CONDITIONS
            result.is_approved = True
            result.conditions.append("Action approved with ethical conditions")
        elif result.ethics is None:
            result.decision_type = EthicalDecisionType.APPROVED
            result.is_approved = True
            result.conditions.append("Approved by default (no ethical checks)")

    def get_statistics(self) -> dict[str, Any]:
        """Get validation statistics."""
        return get_statistics(
            total_validations=self.total_validations,
            total_approved=self.total_approved,
            total_rejected=self.total_rejected,
            avg_duration_ms=self.avg_duration_ms,
            enable_governance=self.enable_governance,
            enable_ethics=self.enable_ethics,
            enable_xai=self.enable_xai,
            enable_compliance=self.enable_compliance,
        )
