"""Core HCL orchestrator implementation."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

from ..analyze.anomaly_detector import AnomalyDetector
from ..analyze.degradation_detector import PerformanceDegradationDetector
from ..analyze.demand_forecaster import ResourceDemandForecaster
from ..analyze.failure_predictor import FailurePredictor
from ..execute.cache_actuator import CacheActuator
from ..execute.database_actuator import DatabaseActuator
from ..execute.docker_actuator import DockerActuator
from ..execute.kubernetes_actuator import KubernetesActuator
from ..execute.loadbalancer_actuator import LoadBalancerActuator
from ..execute.safety_manager import SafetyManager
from ..knowledge_base.decision_api import DecisionAPI
from ..monitor.system_monitor import SystemMonitor
from ..plan.fuzzy_controller import FuzzyLogicController
from ..plan.mode_definitions import get_mode_policy
from ..plan.rl_agent import SACAgent
from .models import HCLConfig

logger = logging.getLogger(__name__)


class HomeostaticControlLoop:
    """Main HCL orchestrator - autonomous self-regulation loop."""

    def __init__(self, config: HCLConfig | None = None) -> None:
        """Initialize HCL orchestrator."""
        self.config = config or HCLConfig()
        self.dry_run_mode = self.config.dry_run_mode
        self.loop_interval = self.config.loop_interval
        self.running = False

        # Monitor
        self.monitor = SystemMonitor()

        # Analyze
        self.demand_forecaster = ResourceDemandForecaster()
        self.anomaly_detector = AnomalyDetector()
        self.failure_predictor = FailurePredictor()
        self.degradation_detector = PerformanceDegradationDetector()

        # Plan
        self.fuzzy_controller = FuzzyLogicController()
        self.rl_agent = SACAgent()
        self.current_mode = "BALANCED"

        # Execute
        self.k8s_actuator = KubernetesActuator(dry_run_mode=self.dry_run_mode)
        self.docker_actuator = DockerActuator(dry_run_mode=self.dry_run_mode)
        self.db_actuator = DatabaseActuator(dry_run_mode=self.dry_run_mode)
        self.cache_actuator = CacheActuator(dry_run_mode=self.dry_run_mode)
        self.lb_actuator = LoadBalancerActuator(dry_run_mode=self.dry_run_mode)
        self.safety_manager = SafetyManager()

        # Knowledge Base
        self.decision_api = DecisionAPI(db_url=self.config.db_url)

        logger.info(
            "HCL Orchestrator initialized (dry_run=%s, interval=%ss)", self.dry_run_mode, self.loop_interval
        )

    async def initialize(self) -> None:
        """Initialize components and database pool."""
        try:
            import asyncpg

            self.decision_api.pool = await asyncpg.create_pool(self.decision_api.db_url, min_size=2, max_size=10)

            from ..knowledge_base.database_schema import create_schema

            async with self.decision_api.pool.acquire() as conn:
                await create_schema(conn)

            logger.info("HCL components initialized successfully")

        except Exception as e:
            logger.error("HCL initialization error: %s", e)
            raise

    async def run(self) -> None:
        """Main control loop."""
        self.running = True
        logger.info("HCL loop started")

        loop_count = 0

        while self.running:
            try:
                loop_start = time.time()
                loop_count += 1

                logger.info("=== HCL Cycle %s ===", loop_count)

                metrics = await self.monitor.collect_metrics()
                logger.info("Monitor: Collected %s metrics", len(metrics))

                analysis = await self._analyze_metrics(metrics)
                logger.info("Analyze: %s", analysis.get("summary", "Complete"))

                plan = await self._plan_actions(metrics, analysis)
                logger.info("Plan: Mode=%s, Actions=%s", plan["operational_mode"], len(plan["actions"]))

                execution = await self._execute_plan(plan, metrics)
                logger.info("Execute: Success=%s, Applied=%s", execution["success"], execution["applied_count"])

                await self._store_decision(metrics, analysis, plan, execution)

                elapsed = time.time() - loop_start
                wait_time = max(0, self.loop_interval - elapsed)
                logger.info("HCL cycle completed in %.1fs, waiting %.1fs", elapsed, wait_time)

                await asyncio.sleep(wait_time)

            except Exception as e:
                logger.error("HCL loop error: %s", e, exc_info=True)
                await asyncio.sleep(self.loop_interval)

        logger.info("HCL loop stopped")

    async def _analyze_metrics(self, metrics: dict) -> dict:
        """Analyze metrics for anomalies, failures, degradation."""
        analysis = {}
        try:
            metric_array = self._metrics_to_array(metrics)
            anomaly_result = self.anomaly_detector.detect(metric_array)  # type: ignore
            analysis["anomaly"] = anomaly_result

            failure_features = self._extract_failure_features(metrics)
            failure_result = self.failure_predictor.predict(failure_features)
            analysis["failure_prediction"] = failure_result

            degradation_result = self.degradation_detector.detect_degradation(metrics.get("latency_p99", 0))  # type: ignore
            analysis["degradation"] = degradation_result

            forecast = self.demand_forecaster.predict(horizon="1h")
            analysis["forecast"] = forecast

            issues = []
            if anomaly_result.get("is_anomaly"):
                issues.append(f"Anomaly detected (score={anomaly_result['score']:.2f})")
            if failure_result.get("failure_probability", 0) > 0.7:
                issues.append(f"High failure risk ({failure_result['failure_probability']:.0%})")
            if degradation_result.get("is_degraded"):
                issues.append("Performance degradation detected")

            analysis["summary"] = ", ".join(issues) if issues else "System healthy"

        except Exception as e:
            logger.error("Analysis error: %s", e)
            analysis["error"] = str(e)

        return analysis

    async def _plan_actions(self, metrics: dict, analysis: dict) -> dict:
        """Plan operational mode and resource actions."""
        plan: dict[str, Any] = {"operational_mode": self.current_mode, "actions": [], "reasoning": []}

        try:
            cpu_usage = metrics.get("cpu_percent", 0)
            error_rate = metrics.get("error_rate", 0)
            latency = metrics.get("latency_p99", 0)

            mode = self.fuzzy_controller.select_mode(cpu_usage, error_rate, latency)  # type: ignore
            plan["operational_mode"] = mode
            plan["reasoning"].append(f"Fuzzy logic selected {mode} mode")

            policy = get_mode_policy(mode)

            if analysis.get("anomaly", {}).get("is_anomaly"):
                plan["actions"].extend(self._generate_anomaly_actions(policy, metrics))
                plan["reasoning"].append("Anomaly mitigation actions")

            if analysis.get("failure_prediction", {}).get("failure_probability", 0) > 0.7:
                plan["actions"].extend(self._generate_preventive_actions(policy, metrics))
                plan["reasoning"].append("Preventive actions for predicted failure")

            if analysis.get("degradation", {}).get("is_degraded"):
                plan["actions"].extend(self._generate_optimization_actions(policy, metrics))
                plan["reasoning"].append("Performance optimization actions")

            self.current_mode = mode

        except Exception as e:
            logger.error("Planning error: %s", e)
            plan["error"] = str(e)

        return plan

    async def _execute_plan(self, plan: dict, metrics_before: dict) -> dict:
        """Execute planned actions with safety checks."""
        execution: dict[str, Any] = {"success": True, "applied_count": 0, "failed_count": 0, "actions_log": []}

        try:
            for action in plan.get("actions", []):
                if not self.safety_manager.check_rate_limit(action.get("type", "NORMAL")):
                    logger.warning("Action throttled: %s", action)
                    execution["failed_count"] += 1
                    continue

                result = await self._execute_action(action)

                execution["actions_log"].append(
                    {"action": action, "result": result, "timestamp": datetime.now().isoformat()}
                )

                if result.get("success"):
                    execution["applied_count"] += 1
                    self.safety_manager.log_action(action)
                else:
                    execution["failed_count"] += 1
                    execution["success"] = False

        except Exception as e:
            logger.error("Execution error: %s", e)
            execution["error"] = str(e)
            execution["success"] = False

        return execution

    async def _execute_action(self, action: dict) -> dict:
        """Execute individual action using appropriate actuator."""
        action_type = action.get("actuator")

        try:
            if action_type == "kubernetes":
                if action["operation"] == "adjust_hpa":
                    return self.k8s_actuator.adjust_hpa(
                        action["service"], action["min_replicas"], action["max_replicas"]
                    )
            elif action_type == "docker":
                if action["operation"] == "scale":
                    return await self.docker_actuator.scale_service(action["service"], action["replicas"])
            elif action_type == "database":
                if action["operation"] == "adjust_pool":
                    return await self.db_actuator.adjust_connection_pool(
                        action["database"], action["pool_size"], action.get("pool_mode", "transaction")
                    )
            elif action_type == "cache":
                if action["operation"] == "set_strategy":
                    return await self.cache_actuator.set_cache_strategy(action["strategy"])

            return {"success": False, "error": f"Unknown action type: {action_type}"}

        except Exception as e:
            logger.error("Action execution error: %s", e)
            return {"success": False, "error": str(e)}

    async def _store_decision(self, metrics: dict, analysis: dict, plan: dict, execution: dict) -> None:
        """Store decision in knowledge base for learning."""
        try:
            decision = {
                "trigger": analysis.get("summary", "Routine cycle"),
                "operational_mode": plan["operational_mode"],
                "actions_taken": plan["actions"],
                "state_before": metrics,
                "state_after": {},
                "outcome": "SUCCESS" if execution["success"] else "FAILED",
                "reward_signal": self._calculate_reward(metrics, execution),
                "human_feedback": None,
            }

            await self.decision_api.create_decision(decision)

        except Exception as e:
            logger.error("Decision storage error: %s", e)

    def _generate_anomaly_actions(self, policy: dict, metrics: dict) -> list:
        """Generate actions for anomaly mitigation."""
        actions = []
        if float(metrics.get("cpu_percent", 0)) > 80:
            actions.append(
                {
                    "actuator": "kubernetes",
                    "operation": "adjust_hpa",
                    "service": "maximus-core",
                    "min_replicas": 3,
                    "max_replicas": 10,
                    "type": "CRITICAL",
                }
            )
        return actions

    def _generate_preventive_actions(self, policy: dict, metrics: dict) -> list:
        """Generate preventive actions for predicted failures."""
        return [
            {
                "actuator": "docker",
                "operation": "scale",
                "service": "maximus-core",
                "replicas": 4,
                "type": "CRITICAL",
            }
        ]

    def _generate_optimization_actions(self, policy: dict, metrics: dict) -> list:
        """Generate performance optimization actions."""
        actions = []
        if float(metrics.get("latency_p99", 0)) > 1000:
            actions.append(
                {
                    "actuator": "database",
                    "operation": "adjust_pool",
                    "database": "vertice",
                    "pool_size": 50,
                    "pool_mode": "transaction",
                    "type": "NORMAL",
                }
            )
        return actions

    def _metrics_to_array(self, metrics: dict) -> list:
        """Convert metrics dict to array for ML models."""
        return [
            metrics.get("cpu_percent", 0),
            metrics.get("memory_percent", 0),
            metrics.get("latency_p99", 0),
            metrics.get("error_rate", 0),
        ]

    def _extract_failure_features(self, metrics: dict) -> dict:
        """Extract features for failure prediction."""
        return {
            "error_rate_trend": metrics.get("error_rate", 0),
            "memory_leak_indicator": float(metrics.get("memory_percent", 0)) > 85,
            "cpu_spike_pattern": float(metrics.get("cpu_percent", 0)) > 90,
            "disk_io_degradation": float(metrics.get("disk_io_wait", 0)) > 50,
        }

    def _calculate_reward(self, metrics: dict, execution: dict) -> float:
        """Calculate reward signal for RL training."""
        reward = 0.0
        if metrics.get("latency_p99", 1000) < 500:
            reward += 1.0
        if metrics.get("error_rate", 1.0) < 0.01:
            reward += 1.0
        if metrics.get("cpu_percent", 0) > 80:
            reward -= 0.5
        if not execution.get("success", False):
            reward -= 2.0
        return reward

    async def stop(self) -> None:
        """Stop the control loop."""
        self.running = False
        logger.info("HCL loop stop requested")

        if self.decision_api.pool:
            await self.decision_api.pool.close()

        if self.cache_actuator.client:
            await self.cache_actuator.close()
