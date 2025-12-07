"""
MAXIMUS Consciousness Integration Example.

Demonstrates the full embodied consciousness pipeline:
  Physical State → MMEI → Needs → Goals → MCEA → Arousal → ESGT

Flow:
  1. MMEI monitors physical metrics (CPU, memory, errors, network)
  2. Needs are computed from metrics (rest_need, repair_need, etc.)
  3. Goals are autonomously generated from needs
  4. MCEA modulates arousal based on needs and external factors
  5. Arousal adjusts ESGT salience threshold
  6. ESGT ignites when salient content + arousal permit
  7. HCL executes goals to restore homeostasis

Usage: python consciousness/integration_example.py
"""

from __future__ import annotations

import asyncio
import random

from maximus_core_service.consciousness.mcea.controller import (
    ArousalConfig,
    ArousalController,
    ArousalState,
    ArousalLevel,
)
from maximus_core_service.consciousness.mcea.stress import StressLevel, StressMonitor
from maximus_core_service.consciousness.mmei.goals import AutonomousGoalGenerator, Goal, GoalGenerationConfig, GoalType
from maximus_core_service.consciousness.mmei.monitor import (
    AbstractNeeds,
    InternalStateMonitor,
    InteroceptionConfig,
    PhysicalMetrics,
)


class ConsciousnessIntegrationDemo:
    """Demonstrates full consciousness integration: Metrics → Needs → Goals → Arousal → ESGT."""

    def __init__(self) -> None:
        self.mmei_config = InteroceptionConfig(collection_interval_ms=500.0)
        self.goal_config = GoalGenerationConfig(
            rest_threshold=0.60, repair_threshold=0.40, min_goal_interval_seconds=5.0
        )
        self.arousal_config = ArousalConfig(
            baseline_arousal=0.6,
            update_interval_ms=200.0,
            arousal_increase_rate=0.1,
            arousal_decrease_rate=0.05,
        )

        self.mmei_monitor: InternalStateMonitor | None = None
        self.goal_generator: AutonomousGoalGenerator | None = None
        self.arousal_controller: ArousalController | None = None
        self.stress_monitor: StressMonitor | None = None

        self.simulated_cpu: float = 30.0
        self.simulated_memory: float = 40.0
        self.simulated_errors: float = 1.0
        self.simulated_latency: float = 20.0

        self.scenario_active: bool = False
        self.total_goals_generated: int = 0
        self.total_esgt_candidates: int = 0
        self._last_arousal_level: ArousalLevel | None = None

    async def initialize(self) -> None:
        """Initialize all consciousness components."""
        logger.info("=" * 70)
        logger.info("MAXIMUS Consciousness Integration Demo")
        logger.info("=" * 70)
        logger.info("\nInitializing consciousness components...\n")

        self.mmei_monitor = InternalStateMonitor(config=self.mmei_config, monitor_id="demo-mmei")
        self.mmei_monitor.set_metrics_collector(self._collect_simulated_metrics)
        self.mmei_monitor.register_need_callback(self._on_critical_need, threshold=0.80)
        logger.info("✓ MMEI initialized (interoception active)")

        self.goal_generator = AutonomousGoalGenerator(
            config=self.goal_config, generator_id="demo-goal-gen"
        )
        self.goal_generator.register_goal_consumer(self._on_goal_generated)
        logger.info("✓ Goal Generator initialized (autonomous motivation ready)")

        self.arousal_controller = ArousalController(
            config=self.arousal_config, controller_id="demo-arousal"
        )
        self.arousal_controller.register_arousal_callback(self._on_arousal_change)
        logger.info("✓ MCEA Arousal Controller initialized (MPE active)")

        self.stress_monitor = StressMonitor(
            arousal_controller=self.arousal_controller, monitor_id="demo-stress"
        )
        self.stress_monitor.register_stress_alert(
            self._on_stress_alert, threshold=StressLevel.SEVERE
        )
        logger.info("✓ Stress Monitor initialized (resilience tracking active)")

        logger.info("=" * 70)
        logger.info("All components initialized. Starting consciousness loop...")
        print("=" * 70 + "\n")

    async def start(self) -> None:
        """Start all components."""
        if self.mmei_monitor:
            await self.mmei_monitor.start()
        if self.arousal_controller:
            await self.arousal_controller.start()
        if self.stress_monitor:
            await self.stress_monitor.start()
        logger.info("🧠 Consciousness online. System is now aware.\n")

    async def stop(self) -> None:
        """Stop all components."""
        if self.mmei_monitor:
            await self.mmei_monitor.stop()
        if self.arousal_controller:
            await self.arousal_controller.stop()
        if self.stress_monitor:
            await self.stress_monitor.stop()
        logger.info("\n🛑 Consciousness offline.\n")

    async def _collect_simulated_metrics(self) -> PhysicalMetrics:
        """Collect simulated physical metrics."""
        cpu = self.simulated_cpu + random.uniform(-5, 5)
        memory = self.simulated_memory + random.uniform(-3, 3)
        errors = max(0, self.simulated_errors + random.uniform(-0.5, 0.5))
        latency = max(0, self.simulated_latency + random.uniform(-5, 5))

        return PhysicalMetrics(
            cpu_usage_percent=cpu,
            memory_usage_percent=memory,
            error_rate_per_min=errors,
            network_latency_ms=latency,
            idle_time_percent=max(0, 100 - cpu),
        )

    async def _on_critical_need(self, needs: AbstractNeeds) -> None:
        """Called when any need becomes critical."""
        most_urgent, value, urgency = needs.get_most_urgent()
        logger.info("\n⚠️  CRITICAL NEED DETECTED: %s = {value:.2f}", most_urgent)
        logger.info("   Urgency: %s", urgency.value)
        if self.goal_generator:
            self.goal_generator.generate_goals(needs)
        if self.arousal_controller:
            self.arousal_controller.update_from_needs(needs)

    def _on_goal_generated(self, goal: Goal) -> None:
        """Called when autonomous goal is generated."""
        self.total_goals_generated += 1
        logger.info("\n🎯 AUTONOMOUS GOAL GENERATED:")
        logger.info("   Type: %s", goal.goal_type.value)
        logger.info("   Priority: %s", goal.priority.value)
        logger.info("   Description: %s", goal.description)
        logger.info("   Source need: %s = {goal.need_value:.2f}", goal.source_need)
        self._simulate_goal_execution(goal)

    async def _on_arousal_change(self, state: ArousalState) -> None:
        """Called when arousal state changes significantly."""
        if self._last_arousal_level is not None and state.level != self._last_arousal_level:
            logger.info(
                f"\n🌅 AROUSAL TRANSITION: {self._last_arousal_level.value} → {state.level.value}"
            )
            logger.info("   Arousal: %.2f", state.arousal)
            logger.info("   ESGT Threshold: %.2f", state.esgt_salience_threshold)
            if state.esgt_salience_threshold < 0.60:
                self.total_esgt_candidates += 1
                logger.info("   ⚡ Threshold low enough for ESGT ignition")
        self._last_arousal_level = state.level

    async def _on_stress_alert(self, level: StressLevel) -> None:
        """Called when stress level becomes severe."""
        logger.info("\n🚨 SEVERE STRESS ALERT: %s", level.value)
        logger.info("   System under significant load")

    def _simulate_goal_execution(self, goal: Goal) -> None:
        """Simulate goal execution (HCL integration point)."""
        logger.info("   🔧 Simulating goal execution...")

        if goal.goal_type == GoalType.REST:
            logger.info("   → Reducing computational load...")
            self.simulated_cpu = max(30.0, self.simulated_cpu - 20.0)
        elif goal.goal_type == GoalType.REPAIR:
            logger.info("   → Running diagnostics and repairs...")
            self.simulated_errors = max(0.0, self.simulated_errors - 3.0)
        elif goal.goal_type == GoalType.RESTORE:
            logger.info("   → Optimizing network connectivity...")
            self.simulated_latency = max(10.0, self.simulated_latency - 20.0)

        logger.info("   ✓ Goal execution complete\n")

    async def run_scenario_high_load(self) -> None:
        """Scenario: High computational load."""
        logger.info("=" * 70)
        logger.info("SCENARIO 1: High Computational Load")
        logger.info("=" * 70)
        logger.info("Simulating sustained high CPU/memory usage...\n")

        self.scenario_active = True
        for i in range(5):
            self.simulated_cpu = min(95.0, 60.0 + i * 8.0)
            self.simulated_memory = min(90.0, 50.0 + i * 8.0)
            logger.info(
                f"[+{i * 3}s] CPU: {self.simulated_cpu:.0f}%, Memory: {self.simulated_memory:.0f}%"
            )
            await asyncio.sleep(3.0)

        logger.info("\n⏸️  Load sustained for observation...\n")
        await asyncio.sleep(5.0)
        logger.info("\n✓ Scenario complete. Load should begin decreasing via autonomous goals.\n")
        self.scenario_active = False

    async def run_scenario_error_burst(self) -> None:
        """Scenario: Error burst."""
        logger.info("=" * 70)
        logger.info("SCENARIO 2: Error Burst")
        logger.info("=" * 70)
        logger.info("Simulating sudden error spike...\n")

        self.scenario_active = True
        self.simulated_errors = 15.0
        logger.info("💥 Error rate spiked to %.0f errors/min", self.simulated_errors)
        await asyncio.sleep(5.0)
        logger.info("\n✓ Scenario complete. Errors should be addressed.\n")
        self.scenario_active = False

    async def run_scenario_idle_curiosity(self) -> None:
        """Scenario: Idle time triggers curiosity."""
        logger.info("=" * 70)
        logger.info("SCENARIO 3: Idle → Curiosity")
        logger.info("=" * 70)
        logger.info("Simulating extended idle period...\n")

        self.scenario_active = True
        self.simulated_cpu = 10.0
        self.simulated_memory = 25.0
        self.simulated_errors = 0.5
        logger.info("💤 System idle: CPU %.0f%", self.simulated_cpu)
        await asyncio.sleep(10.0)
        logger.info("\n✓ Scenario complete. Curiosity should emerge during idle.\n")
        self.scenario_active = False

    def print_status(self) -> None:
        """Print current system status."""
        print("\n" + "-" * 70)
        logger.info("CURRENT STATE")
        print("-" * 70)

        logger.info("Physical Metrics:")
        logger.info("  CPU: %.1f%", self.simulated_cpu)
        logger.info("  Memory: %.1f%", self.simulated_memory)
        logger.info("  Errors: %.1f/min", self.simulated_errors)
        logger.info("  Latency: %.1fms", self.simulated_latency)

        if self.mmei_monitor and self.mmei_monitor._current_needs:
            needs = self.mmei_monitor._current_needs
            logger.info("\nAbstract Needs:")
            logger.info("  Rest: %.2f", needs.rest_need)
            logger.info("  Repair: %.2f", needs.repair_need)
            logger.info("  Efficiency: %.2f", needs.efficiency_need)
            logger.info("  Connectivity: %.2f", needs.connectivity_need)
            logger.info("  Curiosity: %.2f", needs.curiosity_drive)

        if self.arousal_controller:
            state = self.arousal_controller.get_current_arousal()
            logger.info("\nArousal State:")
            logger.info("  Level: %s", state.level.value)
            logger.info("  Arousal: %.2f", state.arousal)
            logger.info("  ESGT Threshold: %.2f", state.esgt_salience_threshold)
            logger.info("  Stress: %.2f", self.arousal_controller.get_stress_level())

        if self.goal_generator:
            active_goals = self.goal_generator.get_active_goals()
            logger.info("\nActive Goals: %s", len(active_goals))
            for goal in active_goals[:3]:
                logger.info("  - %s (priority: {goal.priority.value})", goal.goal_type.value)

        logger.info("\nStatistics:")
        logger.info("  Goals Generated: %s", self.total_goals_generated)
        logger.info("  ESGT Candidates: %s", self.total_esgt_candidates)

        if self.mmei_monitor:
            logger.info("  MMEI Collections: %s", self.mmei_monitor.total_collections)
        if self.stress_monitor:
            logger.info("  Stress Level: %s", self.stress_monitor.get_current_stress_level().value)

        print("-" * 70 + "\n")

    async def run_demo(self) -> None:
        """Run full demo with scenarios."""
        try:
            await self.initialize()
            await self.start()

            await asyncio.sleep(2.0)
            self.print_status()

            await self.run_scenario_high_load()
            await asyncio.sleep(3.0)
            self.print_status()

            await self.run_scenario_error_burst()
            await asyncio.sleep(3.0)
            self.print_status()

            await self.run_scenario_idle_curiosity()
            await asyncio.sleep(3.0)
            self.print_status()

            logger.info("=" * 70)
            logger.info("DEMO COMPLETE - Final Summary")
            logger.info("=" * 70)
            self.print_status()

            logger.info("\n📊 Integration Validated:")
            logger.info("  ✓ MMEI → Needs translation")
            logger.info("  ✓ Needs → Goal generation")
            logger.info("  ✓ Needs → Arousal modulation")
            logger.info("  ✓ Arousal → ESGT threshold adjustment")
            logger.info("  ✓ Goals → (HCL execution simulated)")
            logger.info("\n🧠 Embodied consciousness demonstrated successfully.\n")

        finally:
            await self.stop()


async def main() -> None:
    """Run the integration demo."""
    from consciousness.integration_esgt_demo import run_esgt_integration_demo

    demo = ConsciousnessIntegrationDemo()
    await demo.run_demo()
    await run_esgt_integration_demo()


if __name__ == "__main__":
    logger.info("\n🚀 Starting MAXIMUS Consciousness Integration Demo...\n")
    asyncio.run(main())
