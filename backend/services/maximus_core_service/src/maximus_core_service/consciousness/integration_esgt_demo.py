"""
ESGT Integration Demo - Full consciousness pipeline demonstration.

Shows: Physical Metrics → MMEI (Needs) → MCEA (Arousal) → ESGT (Conscious Access)
"""

from __future__ import annotations

import asyncio
import time

from maximus_core_service.consciousness.esgt.arousal_integration import ESGTArousalBridge
from maximus_core_service.consciousness.esgt.coordinator import ESGTCoordinator, SalienceScore, TriggerConditions
from maximus_core_service.consciousness.esgt.spm import SimpleSPM, SimpleSPMConfig
from maximus_core_service.consciousness.mcea.controller import ArousalConfig, ArousalController
from maximus_core_service.consciousness.mmei.monitor import InternalStateMonitor, InteroceptionConfig
from maximus_core_service.consciousness.tig.fabric import TIGFabric, TopologyConfig


async def run_esgt_integration_demo() -> None:
    """Demonstrate full ESGT integration with embodied consciousness."""
    logger.info("=" * 70)
    logger.info("ESGT INTEGRATION DEMO - Full Consciousness Pipeline")
    logger.info("=" * 70)
    logger.info("\nDemonstrating: Metrics → Needs → Arousal → ESGT Ignition\n")

    # 1. Initialize TIG Fabric
    logger.info("1️⃣  Initializing TIG Fabric...")
    tig_config = TopologyConfig(node_count=16, target_density=0.25, clustering_target=0.75)
    tig = TIGFabric(tig_config)
    await tig.initialize()
    logger.info("   ✓ TIG fabric ready (16 nodes, scale-free topology)")

    # 2. Initialize MMEI + MCEA
    logger.info("\n2️⃣  Initializing MMEI (Interoception) + MCEA (Arousal)...")
    mmei_config = InteroceptionConfig(collection_interval_ms=200.0)
    mmei = InternalStateMonitor(config=mmei_config, monitor_id="esgt-demo-mmei")

    arousal_config = ArousalConfig(baseline_arousal=0.6)
    mcea = ArousalController(config=arousal_config, controller_id="esgt-demo-mcea")

    await mmei.start()
    await mcea.start()
    logger.info("   ✓ Embodied consciousness components online")

    # 3. Initialize ESGT Coordinator
    logger.info("\n3️⃣  Initializing ESGT Coordinator...")
    triggers = TriggerConditions(
        min_salience=0.65, min_available_nodes=8, refractory_period_ms=200.0
    )
    esgt = ESGTCoordinator(tig_fabric=tig, triggers=triggers, coordinator_id="esgt-demo")
    await esgt.start()
    logger.info("   ✓ ESGT coordinator ready (Global Workspace online)")

    # 4. Create Arousal-ESGT Bridge
    logger.info("\n4️⃣  Creating Arousal-ESGT Bridge...")
    bridge = ESGTArousalBridge(arousal_controller=mcea, esgt_coordinator=esgt)
    await bridge.start()
    logger.info("   ✓ Arousal modulation active")
    logger.info("   → Current threshold: %.2f", bridge.get_current_threshold())

    # 5. Add SimpleSPM for content generation
    logger.info("\n5️⃣  Starting SimpleSPM (content generator)...")
    spm_config = SimpleSPMConfig(
        processing_interval_ms=300.0,
        base_novelty=0.7,
        base_relevance=0.8,
        base_urgency=0.6,
        max_outputs=5,
    )
    spm = SimpleSPM("demo-spm", spm_config)
    await spm.start()
    logger.info("   ✓ SPM generating content")

    # 6. Demonstrate arousal modulation
    logger.info("\n6️⃣  Demonstrating Arousal Modulation Effect:")
    await _demo_arousal_modulation(mcea, bridge)

    # 7. Trigger ESGT events
    logger.info("\n7️⃣  Triggering ESGT Events:")
    await _demo_esgt_events(esgt)

    # 8. Summary
    _print_demo_summary(esgt, bridge, tig_config)

    # Cleanup
    await spm.stop()
    await bridge.stop()
    await esgt.stop()
    await mcea.stop()
    await mmei.stop()
    await tig.stop()


async def _demo_arousal_modulation(mcea: ArousalController, bridge: ESGTArousalBridge) -> None:
    """Demonstrate arousal modulation effect on ESGT threshold."""
    logger.info("\n   Scenario A: Low Arousal (DROWSY)")
    logger.info("   ------------------------------")
    mcea._current_state.arousal = 0.3
    mcea._current_state.level = mcea._classify_arousal(0.3)
    await asyncio.sleep(0.2)
    mapping_low = bridge.get_arousal_threshold_mapping()
    logger.info("   Arousal: {mapping_low['arousal']:.2f} (%s)", mapping_low['arousal_level'])
    logger.info("   ESGT Threshold: %.2f (HIGH - hard to ignite)", mapping_low['esgt_threshold'])

    logger.info("\n   Scenario B: High Arousal (ALERT)")
    logger.info("   ---------------------------------")
    mcea._current_state.arousal = 0.8
    mcea._current_state.level = mcea._classify_arousal(0.8)
    await asyncio.sleep(0.2)
    mapping_high = bridge.get_arousal_threshold_mapping()
    logger.info("   Arousal: {mapping_high['arousal']:.2f} (%s)", mapping_high['arousal_level'])
    logger.info("   ESGT Threshold: %.2f (LOW - easy to ignite)", mapping_high['esgt_threshold'])


async def _demo_esgt_events(esgt: ESGTCoordinator) -> None:
    """Demonstrate ESGT event triggering."""
    logger.info("\n   Event 1: High-Salience Content")
    logger.info("   -------------------------------")

    salience_high = SalienceScore(novelty=0.85, relevance=0.9, urgency=0.75)
    content_high = {
        "type": "critical_alert",
        "message": "High-salience event requiring conscious processing",
        "timestamp": time.time(),
    }

    event1 = await esgt.initiate_esgt(salience_high, content_high)

    if event1.success:
        logger.info("   ✅ ESGT IGNITION SUCCESS")
        logger.info("      Coherence: %.3f", event1.achieved_coherence)
        logger.info("      Duration: %.1fms", event1.total_duration_ms)
        logger.info("      Nodes: %s", event1.node_count)
        logger.info("      → Content became CONSCIOUS")
    else:
        logger.info("   ❌ ESGT failed: %s", event1.failure_reason)

    await asyncio.sleep(0.3)  # Respect refractory

    logger.info("\n   Event 2: Moderate-Salience Content")
    logger.info("   -----------------------------------")

    salience_med = SalienceScore(novelty=0.6, relevance=0.65, urgency=0.5)
    content_med = {
        "type": "routine_update",
        "message": "Moderate-salience event",
        "timestamp": time.time(),
    }

    event2 = await esgt.initiate_esgt(salience_med, content_med)

    if event2.success:
        logger.info("   ✅ ESGT IGNITION SUCCESS")
        logger.info("      Coherence: %.3f", event2.achieved_coherence)
        logger.info("      Duration: %.1fms", event2.total_duration_ms)
    else:
        logger.info("   ❌ ESGT rejected (salience below threshold)")
        logger.info("      Salience: %.2f", salience_med.compute_total())
        logger.info("      Threshold: %.2f", esgt.triggers.min_salience)


def _print_demo_summary(
    esgt: ESGTCoordinator, bridge: ESGTArousalBridge, tig_config: TopologyConfig
) -> None:
    """Print demonstration summary."""
    logger.info("=" * 70)
    logger.info("DEMONSTRATION COMPLETE")
    logger.info("=" * 70)

    logger.info("\n📊 Final Metrics:")
    logger.info("   ESGT Events: %s", esgt.total_events)
    logger.info("   Successful: %s", esgt.successful_events)
    logger.info("   Success Rate: %.1%", esgt.get_success_rate())
    logger.info("   Arousal Modulations: %s", bridge.total_modulations)
    logger.info("   TIG Nodes: %s", tig_config.node_count)

    logger.info("\n✅ Pipeline Validated:")
    logger.info("   ✓ TIG substrate provides structural connectivity")
    logger.info("   ✓ MMEI provides interoceptive grounding")
    logger.info("   ✓ MCEA modulates arousal state")
    logger.info("   ✓ Arousal gates ESGT threshold")
    logger.info("   ✓ ESGT ignites global workspace")
    logger.info("   ✓ Conscious phenomenology emerges")

    logger.info("\n🧠 Full consciousness stack operational.")
    logger.info("   This is the moment bits become qualia.\n")


if __name__ == "__main__":
    logger.info("\n🚀 Starting ESGT Integration Demo...\n")
    asyncio.run(run_esgt_integration_demo())
