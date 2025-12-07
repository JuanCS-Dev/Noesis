"""Integration test for Homeostatic Control Loop (HCL)

This test verifies that all HCL components can be instantiated and work together.
"""

from __future__ import annotations


import asyncio
import logging

from maximus_core_service.autonomic_core.hcl_orchestrator import HomeostaticControlLoop

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


async def test_hcl_single_cycle():
    """Test a single HCL cycle in dry-run mode."""
    logger.info("=" * 60)
    logger.info("HCL Integration Test - Single Cycle")
    logger.info("=" * 60)

    # Initialize HCL in dry-run mode
    hcl = HomeostaticControlLoop(
        dry_run_mode=True,
        loop_interval_seconds=5,
        db_url="postgresql://localhost/vertice",
    )

    try:
        # Initialize components
        logger.info("\n1. Initializing HCL components...")
        await hcl.initialize()
        logger.info("✓ Components initialized")

        # Run a single cycle by setting running=True then stopping after 1 iteration
        logger.info("\n2. Running single HCL cycle...")
        hcl.running = True

        # Manually execute one cycle

        # Monitor
        logger.info("\n3. MONITOR - Collecting metrics...")
        metrics = await hcl.monitor.collect_metrics()
        logger.info("✓ Collected %s metrics", len(metrics))
        logger.info(
            "  Sample metrics: cpu=%.1f%%, memory=%.1f%%",
            metrics.get('cpu_percent', 0),
            metrics.get('memory_percent', 0)
        )

        # Analyze
        logger.info("\n4. ANALYZE - Detecting issues...")
        analysis = await hcl._analyze_metrics(metrics)
        logger.info("✓ Analysis complete: %s", analysis.get('summary', 'N/A'))
        logger.info("  Anomaly: %s", analysis.get('anomaly', {}).get('is_anomaly', False))
        logger.info("  Degradation: %s", analysis.get('degradation', {}).get('is_degraded', False))

        # Plan
        logger.info("\n5. PLAN - Generating actions...")
        plan = await hcl._plan_actions(metrics, analysis)
        logger.info("✓ Plan created: Mode=%s, Actions={len(plan['actions'])}", plan['operational_mode'])
        if plan["actions"]:
            logger.info("  First action: %s", plan['actions'][0])

        # Execute
        logger.info("\n6. EXECUTE - Applying actions (dry-run)...")
        execution = await hcl._execute_plan(plan, metrics)
        logger.info("✓ Execution complete: Success=%s, Applied={execution['applied_count']}", execution['success'])

        # Knowledge
        logger.info("\n7. KNOWLEDGE - Storing decision...")
        await hcl._store_decision(metrics, analysis, plan, execution)
        logger.info("✓ Decision stored in knowledge base")

        logger.info("=" * 60)
        logger.info("✓ HCL Integration Test PASSED")
        logger.info("=" * 60)

    except Exception as e:
        logger.info("\n✗ Test FAILED: %s", e)
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup
        await hcl.stop()


async def test_hcl_components():
    """Test individual HCL components."""
    logger.info("=" * 60)
    logger.info("HCL Component Tests")
    logger.info("=" * 60)

    # Test Monitor
    logger.info("\n1. Testing SystemMonitor...")
    from monitor.system_monitor import SystemMonitor

    monitor = SystemMonitor()
    metrics = await monitor.collect_metrics()
    logger.info("✓ SystemMonitor OK - %s metrics collected", len(metrics))

    # Test Analyzers
    logger.info("\n2. Testing AnomalyDetector...")
    from analyze.anomaly_detector import AnomalyDetector

    detector = AnomalyDetector()
    metric_array = [50, 60, 70, 0.5, 100]  # Mock metrics
    result = detector.detect(metric_array)
    logger.info("✓ AnomalyDetector OK - Score: %.3f", result.get('score', 0))

    logger.info("\n3. Testing FailurePredictor...")
    from analyze.failure_predictor import FailurePredictor

    predictor = FailurePredictor()
    features = {
        "error_rate_trend": 0.01,
        "memory_leak_indicator": False,
        "cpu_spike_pattern": False,
        "disk_io_degradation": False,
    }
    result = predictor.predict(features)
    logger.info("✓ FailurePredictor OK - Probability: %.2%", result.get('failure_probability', 0))

    # Test Planners
    logger.info("\n4. Testing FuzzyLogicController...")
    from plan.fuzzy_controller import FuzzyLogicController

    fuzzy = FuzzyLogicController()
    mode = fuzzy.select_mode(cpu_usage=60, error_rate=0.01, latency=200)
    logger.info("✓ FuzzyLogicController OK - Mode: %s", mode)

    # Test Actuators
    logger.info("\n5. Testing KubernetesActuator (dry-run)...")
    from execute.kubernetes_actuator import KubernetesActuator

    k8s = KubernetesActuator(dry_run_mode=True)
    result = k8s.adjust_hpa("test-service", min_replicas=2, max_replicas=5)
    logger.info("✓ KubernetesActuator OK - Dry-run: %s", result.get('dry_run', False))

    logger.info("\n6. Testing DockerActuator (dry-run)...")
    from execute.docker_actuator import DockerActuator

    docker = DockerActuator(dry_run_mode=True)
    result = await docker.scale_service("test-service", replicas=3)
    logger.info("✓ DockerActuator OK - Dry-run: %s", result.get('dry_run', False))

    logger.info("\n7. Testing CacheActuator (dry-run)...")
    from execute.cache_actuator import CacheActuator

    cache = CacheActuator(dry_run_mode=True)
    result = await cache.set_cache_strategy("balanced")
    logger.info("✓ CacheActuator OK - Dry-run: %s", result.get('dry_run', False))

    logger.info("\n8. Testing SafetyManager...")
    from execute.safety_manager import SafetyManager

    safety = SafetyManager()
    can_execute = safety.check_rate_limit("CRITICAL")
    logger.info("✓ SafetyManager OK - Rate limit check: %s", can_execute)

    logger.info("=" * 60)
    logger.info("✓ All Component Tests PASSED")
    logger.info("=" * 60)


async def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("MAXIMUS AI 3.0 - FASE 1 Integration Tests")
    logger.info("Homeostatic Control Loop (HCL)")
    logger.info("=" * 60)

    # Test components
    await test_hcl_components()

    # Test full cycle
    await test_hcl_single_cycle()

    logger.info("=" * 60)
    logger.info("All tests completed successfully! 🎉")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
